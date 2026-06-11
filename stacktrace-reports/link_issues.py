"""link_issues.py - Link registry signatures to existing OPM/ResInsight issues
and refresh the open/closed state of already-linked ones.

Step 2 of the weekly workflow, automated. For every signature in `registry.json`:

* If it has no linked issue, search OPM/ResInsight for its top-frame symbol and
  link the first candidate whose title or body actually contains that symbol -
  the same "does the issue really mention this crash site" check a human makes.
  Signatures with no confident match are left unlinked (`none found`).
* If it already has a linked issue, re-fetch the issue state so an issue that has
  since been closed (or reopened) is reflected, and the stack moves to / from the
  report's `## Closed issues` section on the next render.

Requires the GitHub CLI (`gh`) to be authenticated. Run `registry.py render`
afterwards to regenerate the reports with the new links.

Usage:
    python link_issues.py                 # link unlinked + refresh linked
    python link_issues.py --refresh-only  # only refresh already-linked states
    python link_issues.py --dry-run       # show what would change, write nothing
"""

import argparse
import json
import subprocess
import sys
import time

from registry import (
    OPM_ISSUES_URL,
    UNSYMBOLIZED,
    frame_symbol,
    load_registry,
    save_registry,
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


def set_status_from_issue(entry: dict) -> None:
    """Derive a status from the linked issue + any PR already recorded."""
    iss = entry.get("opm_issue")
    if not iss:
        return
    if entry.get("pr"):
        entry["status"] = "resolved" if iss["state"] == "CLOSED" else "pr-open"
    else:
        entry["status"] = "resolved" if iss["state"] == "CLOSED" else "linked"


def link_entry(entry: dict, number: int, state: str) -> None:
    entry["opm_issue"] = {
        "number": number,
        "state": state,
        "url": f"{OPM_ISSUES_URL}/{number}",
    }
    set_status_from_issue(entry)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--limit", type=int, default=5, help="search results to inspect per symbol")
    ap.add_argument("--refresh-only", action="store_true", help="only refresh linked states")
    ap.add_argument("--dry-run", action="store_true", help="write nothing")
    args = ap.parse_args()

    reg = load_registry()
    sigs = reg["signatures"]

    linked = refreshed = changed = 0
    search_cache: dict[str, dict | None] = {}

    # Sort by impact so the most frequent crashes are searched first.
    ordered = sorted(
        sigs.values(),
        key=lambda e: -sum(w["count"] for w in e["weeks"].values()),
    )

    for entry in ordered:
        iss = entry.get("opm_issue")
        if iss:
            new_state = refresh_state(iss["number"])
            if new_state and new_state != iss["state"]:
                print(f"  ~ #{iss['number']} {iss['state']} -> {new_state}  ({entry['top_frame']})")
                iss["state"] = new_state
                set_status_from_issue(entry)
                refreshed += 1
                changed += 1
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
        print(f"[dry-run] would link={linked} refresh={refreshed}")
        return

    if changed:
        save_registry(reg)
    print(f"linked={linked} refreshed={refreshed} (run registry.py render to update reports)")


if __name__ == "__main__":
    main()
