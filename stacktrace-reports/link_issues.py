"""link_issues.py - Link registry signatures to existing OPM/ResInsight issues
and refresh the state of everything already referenced.

Step 2 of the weekly workflow, automated. For every signature in `registry.json`:

* If it has no reference at all, search OPM/ResInsight for its top-frame symbol
  and link the first candidate whose title or body actually contains that symbol
  - the same "does the issue really mention this crash site" check a human makes.
  Signatures with no confident match are left unreferenced (`none found`) and go
  on the triage worklist.
* If it already has a linked issue, re-fetch the issue state so an issue that has
  since been closed (or reopened) is reflected.
* If it carries a fix PR, re-fetch the PR state. Crash triage no longer files
  issues - the crash stack lives in the PR body - so for those signatures the PR
  is the only reference and its merge is what closes the signature out
  (`pr-open` -> `resolved`). No issue search is run for them.

Either way the stack moves to / from the report's `## Closed issues and merged
fixes` section on the next render.

Once a signature is fixed - PR merged, or (without a PR) issue closed as
completed - `fixed_in` is set to the version in `ResInsightVersion.cmake` at the
merge commit (for an issue: its closing PR, else the last `dev` commit before
it closed). Crashes on a newer version then label the signature `regressed`.

Requires the GitHub CLI (`gh`) to be authenticated. Run `registry.py render`
afterwards to regenerate the reports with the new links.

Usage:
    python link_issues.py                 # link unreferenced + refresh states
    python link_issues.py --refresh-only  # only refresh issue/PR states
    python link_issues.py --dry-run       # show what would change, write nothing
"""

import argparse
import base64
import json
import re
import subprocess
import sys
import time

from registry import (
    OPM_ISSUES_URL,
    UNSYMBOLIZED,
    entry_versions,
    frame_symbol,
    load_registry,
    save_registry,
    version_key,
)

REPO = "OPM/ResInsight"

# GitHub's Search API allows ~30 requests/min. Pace search calls to stay under
# it; on a 403 rate-limit, back off and retry rather than skipping the symbol.
SEARCH_INTERVAL_S = 2.5
RATE_LIMIT_BACKOFF_S = (30, 60, 120)
_last_search = 0.0


def gh_json(args: list[str], *, is_search: bool = False) -> object:
    """Run a `gh` command returning JSON; None on non-rate-limit failure.

    Search calls are paced to `SEARCH_INTERVAL_S` apart and retried with backoff
    when GitHub returns an HTTP 403 rate-limit response.
    """
    global _last_search
    attempts = len(RATE_LIMIT_BACKOFF_S) + 1
    for attempt in range(attempts):
        if is_search:
            wait = SEARCH_INTERVAL_S - (time.monotonic() - _last_search)
            if wait > 0:
                time.sleep(wait)
        try:
            out = subprocess.run(
                ["gh", *args],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=60,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
            print(f"  ! gh call failed: {exc}", file=sys.stderr)
            return None
        finally:
            if is_search:
                _last_search = time.monotonic()
        if out.returncode == 0:
            if not out.stdout:
                return None
            try:
                return json.loads(out.stdout)
            except json.JSONDecodeError:
                return None
        if "rate limit" in out.stderr.lower() and attempt < attempts - 1:
            backoff = RATE_LIMIT_BACKOFF_S[attempt]
            print(f"  … rate limited, sleeping {backoff}s", file=sys.stderr)
            time.sleep(backoff)
            continue
        print(f"  ! gh {' '.join(args)} -> {out.stderr.strip()[:120]}", file=sys.stderr)
        return None
    return None


def issue_mentions(symbol: str, title: str, body: str) -> bool:
    """A confident match: `symbol` appears as an actual stack *frame* in the
    issue, not merely somewhere in its prose.

    Auto-generated `Stacktrace …` issues embed the raw stack, so each frame line
    normalises - via the same `frame_symbol` that defines signature identity -
    to a qualified `Class::method`. A hand-written issue that only *mentions* the
    function in passing has no such frame line: e.g. the enhancement request
    OPM/ResInsight#12756 contains the sentence "See `RifReaderEclipseWell::
    readWellCells`", which is not a crash site. Requiring a real frame line
    (symbol followed by ` at <path>:<line>`) rejects that false positive while
    still matching every genuine crash report."""
    if not symbol:
        return False
    for line in f"{title}\n{body}".splitlines():
        if frame_symbol(line) == symbol:
            return True
    return False


def search_issue(symbol: str, limit: int) -> dict | None:
    """Return {number,state} of the best-matching issue for `symbol`, or None."""
    results = gh_json(
        [
            "search", "issues",
            "--repo", REPO,
            symbol,
            "--limit", str(limit),
            "--json", "number",
        ],
        is_search=True,
    )
    if not results:
        return None
    for hit in results:
        num = hit["number"]
        detail = gh_json(
            ["issue", "view", str(num), "--repo", REPO, "--json", "number,state,title,body"]
        )
        if not detail:
            continue
        if issue_mentions(symbol, detail.get("title", ""), detail.get("body", "")):
            return {"number": detail["number"], "state": detail["state"]}
    return None


def refresh_state(number: int) -> str | None:
    detail = gh_json(["issue", "view", str(number), "--repo", REPO, "--json", "state"])
    return detail.get("state") if detail else None


def refresh_pr_state(number: int) -> str | None:
    """PR state as OPEN / MERGED / CLOSED (`gh` reports MERGED separately)."""
    detail = gh_json(["pr", "view", str(number), "--repo", REPO, "--json", "state"])
    return detail.get("state") if detail else None


_CMAKE_SET_RE = re.compile(r'^\s*set\(\s*(RESINSIGHT_\w+)\s+"?([^")]*)"?\s*\)', re.M)


def version_at_commit(sha: str) -> str | None:
    """STRPRODUCTVER as built from `sha`, e.g. `2026.06.2-dev.02`."""
    detail = gh_json(["api", f"repos/{REPO}/contents/ResInsightVersion.cmake?ref={sha}"])
    if not detail or "content" not in detail:
        return None
    text = base64.b64decode(detail["content"]).decode("utf-8", errors="replace")
    # Commented-out alternatives (`#set(RESINSIGHT_VERSION_TEXT "-RC_5")`) never
    # match: the regex anchors on optional whitespace only.
    v = dict(_CMAKE_SET_RE.findall(text))
    try:
        version = (f"{v['RESINSIGHT_MAJOR_VERSION']}.{v['RESINSIGHT_MINOR_VERSION']}."
                   f"{v['RESINSIGHT_PATCH_VERSION']}")
    except KeyError:
        return None
    version += v.get("RESINSIGHT_VERSION_TEXT", "") + v.get("RESINSIGHT_DEV_VERSION", "")
    return version if version_key(version) is not None else None


def pr_merge_commit(number: int) -> str | None:
    detail = gh_json(["pr", "view", str(number), "--repo", REPO, "--json", "mergeCommit"])
    return ((detail or {}).get("mergeCommit") or {}).get("oid")


def fix_commit(entry: dict) -> str | None:
    """Commit the fix landed in, or None while the signature is not fixed.

    A PR is authoritative when present; an issue only counts when closed as
    completed (not-planned is no fix). For an issue, the PR that closed it is
    preferred over the last `dev` commit before it closed.
    """
    pr = entry.get("pr")
    if pr:
        return pr_merge_commit(pr["number"]) if pr.get("state") == "MERGED" else None
    iss = entry.get("opm_issue")
    if not iss or iss.get("state") != "CLOSED":
        return None
    detail = gh_json(["issue", "view", str(iss["number"]), "--repo", REPO,
                      "--json", "closedAt,stateReason,closedByPullRequestsReferences"])
    if not detail or detail.get("stateReason") != "COMPLETED" or not detail.get("closedAt"):
        return None
    for ref in detail.get("closedByPullRequestsReferences") or []:
        sha = pr_merge_commit(ref["number"])
        if sha:
            return sha
    commits = gh_json(["api", f"repos/{REPO}/commits?sha=dev&until={detail['closedAt']}&per_page=1"])
    return commits[0]["sha"] if commits else None


def release_contains(version: str, sha: str) -> bool | None:
    """Whether release tag `v<version>` includes `sha`; None if unknown."""
    cmp = gh_json(["api", f"repos/{REPO}/compare/v{version}...{sha}", "--jq", "{status}"])
    if not cmp or "status" not in cmp:
        return None
    return cmp["status"] in ("behind", "identical")


def refresh_fixed_in(entry: dict) -> bool:
    """Fill `fixed_in` once the signature is fixed; clear it if it reopened.

    Version order alone over-reports regressions for releases cut from a bugfix
    branch (v2026.02.2 came from `bugfix-2026.02.2`, without dev's fixes), so
    every newer release the signature crashed on is checked against its tag and
    recorded in `fix_shipped`.

    `no-fix-found` means triage judged the linked reference unrelated, and the
    unsymbolized bucket pools unrelated crashes, so neither has a fix version:
    later crashes there are not regressions.
    """
    pr = entry.get("pr")
    iss = entry.get("opm_issue")
    fixed = (pr.get("state") == "MERGED") if pr else bool(iss and iss.get("state") == "CLOSED")
    if entry.get("status") == "no-fix-found" or entry["top_frame"] == UNSYMBOLIZED:
        fixed = False
    if not fixed:
        had = "fixed_in" in entry
        for key in ("fixed_in", "fix_commit", "fix_shipped"):
            entry.pop(key, None)
        return had

    changed = False
    if not entry.get("fixed_in"):
        sha = fix_commit(entry)
        version = version_at_commit(sha) if sha else None
        if not version:
            return False
        entry["fixed_in"] = version
        entry["fix_commit"] = sha
        print(f"  = fixed in {version}  ({entry['top_frame']})")
        changed = True

    sha = entry.get("fix_commit")
    fixed_key = version_key(entry["fixed_in"])
    if not sha or fixed_key is None:
        return changed
    shipped = entry.setdefault("fix_shipped", {})
    for ver in entry_versions(entry):
        key = version_key(ver)
        if key is None or key[1] != 2 or key <= fixed_key or ver in shipped:
            continue
        contains = release_contains(ver, sha)
        if contains is not None:
            shipped[ver] = contains
            changed = True
    if not shipped:
        entry.pop("fix_shipped")
    return changed


def set_status_from_refs(entry: dict) -> None:
    """Derive a status from whatever references the signature carries.

    The fix PR is authoritative when there is one: a merged PR means the crash is
    fixed, whether or not an issue was ever filed (crash triage now puts the
    stack in the PR body instead). Without a PR the linked issue decides.
    """
    if entry.get("status") in ("no-fix-found", "on-hold"):
        # Deliberate human decisions; never overwritten from GitHub state.
        return

    pr = entry.get("pr")
    iss = entry.get("opm_issue")
    if pr:
        state = pr.get("state")
        if state == "MERGED":
            entry["status"] = "resolved"
        elif state == "CLOSED":
            # PR rejected/abandoned: back to the issue's verdict, or to triage.
            entry["status"] = "resolved" if issue_closed(iss) else "linked" if iss else "new"
        else:
            entry["status"] = "resolved" if issue_closed(iss) else "pr-open"
        return

    if iss:
        entry["status"] = "resolved" if issue_closed(iss) else "linked"


def issue_closed(iss: dict | None) -> bool:
    return bool(iss and iss.get("state") == "CLOSED")


def link_entry(entry: dict, number: int, state: str) -> None:
    entry["opm_issue"] = {
        "number": number,
        "state": state,
        "url": f"{OPM_ISSUES_URL}/{number}",
    }
    set_status_from_refs(entry)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--limit", type=int, default=5, help="search results to inspect per symbol")
    ap.add_argument("--refresh-only", action="store_true", help="only refresh linked states")
    ap.add_argument("--dry-run", action="store_true", help="write nothing")
    args = ap.parse_args()

    reg = load_registry()
    sigs = reg["signatures"]

    linked = refreshed = pr_refreshed = fixed_in = changed = 0
    search_cache: dict[str, dict | None] = {}

    # Sort by impact so the most frequent crashes are searched first.
    ordered = sorted(
        sigs.values(),
        key=lambda e: -sum(w["count"] for w in e["weeks"].values()),
    )

    for entry in ordered:
        iss = entry.get("opm_issue")
        pr = entry.get("pr")

        if pr:
            # A merged fix PR is what closes a signature out now, so its state is
            # refreshed on every run - including for PR-only signatures, where no
            # issue exists to carry the crash.
            new_state = refresh_pr_state(pr["number"])
            if new_state and new_state != pr.get("state"):
                old = pr.get("state") or "unknown"
                print(f"  ~ PR #{pr['number']} {old} -> {new_state}  ({entry['top_frame']})")
                pr["state"] = new_state
                set_status_from_refs(entry)
                pr_refreshed += 1
                changed += 1

        if iss:
            new_state = refresh_state(iss["number"])
            if new_state and new_state != iss["state"]:
                print(f"  ~ #{iss['number']} {iss['state']} -> {new_state}  ({entry['top_frame']})")
                iss["state"] = new_state
                set_status_from_refs(entry)
                refreshed += 1
                changed += 1

        if (iss or pr) and refresh_fixed_in(entry):
            fixed_in += 1
            changed += 1

        if iss or pr:
            # Already referenced: nothing to search for.
            continue

        if args.refresh_only:
            continue
        top = entry["top_frame"]
        if top == UNSYMBOLIZED or "::" not in top:
            # Unqualified free-function symbols are too generic to match safely.
            continue

        if top not in search_cache:
            search_cache[top] = search_issue(top, args.limit)
        hit = search_cache[top]
        if hit:
            print(f"  + #{hit['number']} {hit['state']}  <-  {top}")
            link_entry(entry, hit["number"], hit["state"])
            linked += 1
            changed += 1

    if args.dry_run:
        print(f"[dry-run] would link={linked} refresh={refreshed} pr-refresh={pr_refreshed} "
              f"fixed-in={fixed_in}")
        return

    if changed:
        save_registry(reg)
    print(f"linked={linked} refreshed={refreshed} pr-refreshed={pr_refreshed} "
          f"fixed-in={fixed_in} (run registry.py render to update reports)")


if __name__ == "__main__":
    main()
