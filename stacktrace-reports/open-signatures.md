---
title: Open crash signatures
permalink: /stacktrace-reports/open-signatures/
layout: wide
---

# Open crash signatures — seen but not fixed or started

Snapshot of `registry.json` on **2026-08-10**, covering every weekly CSV up to and
including **2026-08-07** (16 weeks, 192 unique signatures, 2818 crash reports).

This page answers one question: *which crashes have we observed but neither fixed
nor begun working on?* It is a point-in-time analysis, not a generated page — the
weekly reports under [index.md](./index.md) stay the authoritative per-week record.

**Definitions used below**

- **Fixed** — the fix PR is `MERGED`, or the linked OPM issue is `CLOSED`.
- **Started** — status `investigating`, `patch-proposed` or `pr-open`, i.e. a batch
  has been picked up or a PR is in review.
- **Not started** — status `new` or `linked`: seen, possibly linked to an issue, but
  nobody has looked at it.
- `cur` — occurrences reported by build **2026.06.1 or newer** (the current release
  line). `all` — occurrences across all 16 weeks.

> **Counting caveat.** Consecutive weekly CSVs overlap, so a single crash event is
> re-counted in each week it appears in. `all` and `cur` are occurrence counts in the
> telemetry export, not distinct crash events; treat them as relative weight only. A
> signature spanning many weeks with a flat per-week count (e.g. `1, 1, 1, 1`) is
> usually **one** event, not four.

## What changed since the 2026-08-09 snapshot

Four fix PRs closed out and one issue was triaged, which moves 11 signatures:

- **[#14495](https://github.com/OPM/ResInsight/pull/14495) merged** (`crash-triage-combined`).
  It also **supersedes [#14485](https://github.com/OPM/ResInsight/pull/14485) and
  [#14489](https://github.com/OPM/ResInsight/pull/14489)**, which were closed unmerged
  after their commits were folded into the combined branch. The 4 signatures that
  pointed at those two PRs have been re-pointed at #14495 and are now `resolved`; left
  alone they would have fallen back to `new` and reappeared on the worklist as
  untriaged.
- **[#14492](https://github.com/OPM/ResInsight/pull/14492) merged** — 2 signatures on
  the `PdmObjectHandle**` tree resolved. A dangling `#14483` issue link on one of them
  did not resolve on GitHub at all and was dropped.
- **[#14185](https://github.com/OPM/ResInsight/issues/14185) triaged** — see the
  section below. It was the messiest reference in the registry; it is now down to one
  signature, which is fixed.

Group C (work in flight) is consequently down from 10 signatures / 5 open PRs to
**1 signature and 1 open PR**, and group D from 5 signatures to 3.

## Summary

| Bucket | Signatures | Reports (all) | Reports on 2026.06.1+ | Reports in week 2026-08-07 |
|---|---:|---:|---:|---:|
| Fixed — PR merged | 77 | 1464 | 206 | 74 |
| Fixed — issue closed / fixed upstream | 96 | 1039 | 131 | 31 |
| Started, not landed — PR open | 1 | 4 | 0 | 0 |
| **Investigated, no fix found** | **13** | **260** | **3** | **3** |
| **Marked resolved without a merged reference** | **3** | **10** | **0** | **0** |
| **Not started** | **2** | **41** | **0** | **0** |

`registry.py worklist` prints **no untriaged signatures**: every signature now carries
an issue, a PR, or a settled triage status. The backlog that remains is therefore not
a queue of unseen crashes — it is 15 signatures that are known and still unfixed
(groups A and B), plus a small set of bookkeeping inconsistencies (group D) and a much
larger population of crashes that are marked fixed but are still arriving from users
on the released build (group E).

## A. Not started — 2 signatures

Both are the same crash as the largest single entry in the registry, the OpenMP
summary-loading race under [#11342](https://github.com/OPM/ResInsight/issues/11342)
(open since long before this telemetry began). They were auto-linked to the issue by
`link_issues.py` and never picked up, because a linked signature drops off the
worklist.

| Signature | Top frame | cur | all | First seen | Last seen | Weeks | Reference |
|---|---|---:|---:|---|---|---:|---|
| `0ac4bb9ffe9f` | `RimFileSummaryCase::createSummaryReaderInterfaceThreadSafe` | 0 | 34 | 2026-04-09 | 2026-05-07 | 4 | [#11342](https://github.com/OPM/ResInsight/issues/11342) OPEN |
| `f6c284a0e525` | `RimFileSummaryCase::createSummaryReaderInterfaceThreadSafe` | 0 | 7 | 2026-05-12 | 2026-06-30 | 7 | [#11342](https://github.com/OPM/ResInsight/issues/11342) OPEN |

A third variant of the same crash, `bb02459d6dfe` (186 reports), *was* investigated and
ended at `no-fix-found` — see group B. Taken together, #11342 accounts for **227
reports across 3 signatures**, by far the heaviest unfixed item in the registry,
though nothing on it has been reported from 2026.06.1 or newer.

**Recommendation.** Treat #11342 as one work item rather than three signatures. The
recorded untested lead is that `getRestartRelativeFilePathResdata` calls non-thread-safe
resdata from inside the parallel loop.

## B. Investigated, no fix found — 13 signatures

Triage reached these, ruled out the obvious causes, and closed them out without a fix.
They are counted as "closed out" in the weekly reports, but **the bugs are still
present** — nothing shipped for any of them.

| Signature | Top frame | cur | all | First seen | Last seen | Weeks | Reference |
|---|---|---:|---:|---|---|---:|---|
| `7ee60e04022b` | `RivTernaryTextureCoordsCreator::createTextureCoords` | 2 | 2 | 2026-08-06 | 2026-08-07 | 1 | none |
| `94ae601b2092` | `RivTextureCoordsCreator::createTextureCoords` | 1 | 1 | 2026-08-07 | 2026-08-07 | 1 | none |
| `bb02459d6dfe` | `RimFileSummaryCase::createSummaryReaderInterfaceThreadSafe` | 0 | 186 | 2026-04-09 | 2026-06-30 | 14 | [#11342](https://github.com/OPM/ResInsight/issues/11342) OPEN |
| `4bd3f3b19531` | `RiaGrpcApplicationInterface::processRequests` | 0 | 18 | 2026-03-24 | 2026-04-14 | 4 | none |
| `b8bc3e3c7278` | `cvf::PrimitiveSetIndexedUInt::render` | 0 | 13 | 2026-05-12 | 2026-06-05 | 8 | [#14009](https://github.com/OPM/ResInsight/issues/14009) OPEN |
| `69ff9a60f1fa` | `RigStimPlanFractureDefinition::~RigStimPlanFractureDefinition` | 0 | 10 | 2026-06-10 | 2026-06-10 | 5 | none |
| `73b3919e646c` | `RifActiveCellsReader::applyActiveCellsToAllGrids` | 0 | 7 | 2026-04-27 | 2026-06-02 | 7 | none |
| `2fee534b1f8c` | `RifEclipseOutputFileTools::createReportStepsMetaData` | 0 | 5 | 2026-04-13 | 2026-05-05 | 3 | none |
| `f008e6cc06cc` | `RiuSummaryPlot::showContextMenu` | 0 | 5 | 2026-05-28 | 2026-05-28 | 5 | none |
| `0822c8001a77` | `operator` (`RiaWellNameComparer.cpp:87` lambda) | 0 | 4 | 2026-06-02 | 2026-06-02 | 4 | none |
| `359dda73050e` | `cvf::Vector3<double>::Vector3` | 0 | 4 | 2026-06-02 | 2026-06-02 | 4 | none |
| `6e43c5539b5e` | `caf::addXmlCapabilityToField<caf::PdmField<int>>` | 0 | 4 | 2026-06-02 | 2026-06-02 | 4 | none |
| `301aefc06fb9` | `RigFemPartResultCalculatorSurfaceAlignedStress::calculate` | 0 | 1 | 2026-05-05 | 2026-05-05 | 1 | none |

`4bd3f3b19531` lost its reference in this snapshot: it had been auto-linked to #14185,
but only because `link_issues.py` matched frame `[16]`
`RiaGrpcApplicationInterface::processRequests` inside the stack #14185 pasted. That
issue is the `RigEclipseWellLogExtractor` crash, not this one, so the link was removed.
The signature stays off the worklist on its `no-fix-found` status.

### Why they were abandoned

The recorded notes group into four recurring reasons, and the grouping matters more
than the individual entries — each reason suggests a different kind of follow-up than
"try harder on the stack".

**1. Fault is outside ResInsight code (5).** `4bd3f3b19531` (gRPC shutdown),
`b8bc3e3c7278` (OpenGL driver at `glDrawRangeElements`), `f008e6cc06cc` (Qt nested
event loop under `menu.exec()`), `2fee534b1f8c` (wild pointer inside ERT
`ecl_file_view_iget_file_kw`), `73b3919e646c` (`ecl_grid_set_active_index` reading a
cell array written moments earlier). The ResInsight call site is guarded in every
case; the stack bottoms out in a third-party or vendored library.

**2. Heap corruption symptom, origin elsewhere (3).** `69ff9a60f1fa` (empty destructor
faulting on POD members), `0822c8001a77` (SIGSEGV in a static `std::map` cache on a
provably single-threaded path), `6e43c5539b5e` (fault in universally-exercised PDM
field-init code, reached via the gRPC `CreateChildPdmObject` path). These are victim
frames — a local guard cannot fix them, and they will keep reappearing under different
signatures until the corrupting writer is found.

**3. Not guardable (1).** `359dda73050e` — memory-commit failure allocating one AABB
leaf per active cell on a very large grid. `std::bad_alloc` will not catch an
overcommit SIGSEGV.

**4. Cannot pinpoint the null (4).** `7ee60e04022b`, `94ae601b2092`, `301aefc06fb9`,
plus `bb02459d6dfe`. The two texture-coords asserts are the notable pair: both are
`CVF_ASSERT( quadTextureCoords && quadMapper && resultAccessor && texMapper )`, both
were **first seen in the week of 2026-08-07**, and the notes on both point at an
object-lifetime problem on the view-linking path
(`RimViewLinker::updateTimeStep`) rather than a missing guard.

**Recommendation.** Two threads are worth pulling, and both are cross-signature:

- The **view-linking lifetime** hypothesis shared by `7ee60e04022b` + `94ae601b2092`
  — these are the only entries in this group still arriving on the current release,
  and they are new this week rather than a legacy tail.
- The **heap-corruption cluster** (reason 2). Three independent triages concluded
  "corruption from elsewhere"; a run of the gRPC/project-close paths under ASan or
  Valgrind would test all three at once, which no amount of stack reading will.

## C. Started, not landed — 1 signature, 1 open PR

Included for completeness: work is in flight, so this is *not* part of the backlog.

| PR | Branch | Signatures | Reports on 2026.06.1+ | In week 2026-08-07 |
|---|---|---:|---:|---:|
| [#14424](https://github.com/OPM/ResInsight/pull/14424) | `fix-14423-delta-ensemble-close-cases` | 1 (`PdmObjectHandle::prepareForDelete`) | 0 | 0 |

Nothing is left in `investigating`. The last such entry, `b80de5fc87c2`, had been stuck
in that state since the #14185 batch; it has now been triaged out (next section).
#14424 is the oldest item still in flight, open since the week of 2026-06-05.

## D. Marked resolved without a merged reference — 3 signatures

These are marked `resolved` but nothing machine-checkable in the registry proves it:
no merged PR, and either no reference at all or an issue that is still open. They are
hidden from the worklist by status alone.

| Signature | Top frame | all | Reference | Recorded reason |
|---|---|---:|---|---|
| `b80de5fc87c2` | `RigEclipseWellLogExtractor::calculateIntersection` | 4 | [#14185](https://github.com/OPM/ResInsight/issues/14185) OPEN | fixed on dev by `f1218e527f` (#14183) |
| `5c2d85ca0acd` | `RimViewController::askUserToRestoreOriginalCellFilterCollection` | 3 | none | fixed on dev by `81f4628fa6` (#14302) |
| `dc342505e2ac` | `RimWellPathTieIn::defineEditorAttribute` | 3 | none | fixed on dev by `24be78f105` |

Each carries a note naming the commit that fixed it, so the `resolved` status is
justified — the registry simply has no field for "fixed by commit X" and the audit
trail lives only in free text. The three `RicWellPathExportMswTableData::generateCellSegments`
entries that used to sit here have been re-pointed from #14185 to
[#14121](https://github.com/OPM/ResInsight/issues/14121) (CLOSED), which is the issue
their recorded fix commit `253d57f1a5` actually closes; they now verify as fixed and
have moved to group E.

### Triage of #14185

[#14185](https://github.com/OPM/ResInsight/issues/14185) ("Stacktrace
RigEclipseWellLogExtractor", `BugInRelease`, open since 2026-06-09) was the messiest
reference in the registry: five signatures pointed at it with four different statuses.
The cause was mechanical rather than conceptual — the issue body pastes one full stack,
and `link_issues.py` matches *any* frame in that stack, so three signatures whose crash
site is frame `[6]` and one whose site is frame `[16]` all attached themselves to it.
They are now split by actual crash site:

| Signatures | Crash site | Correct reference |
|---|---|---|
| `e934af263f7e`, `756f5de23e61`, `29e769992730` | frame `[6]` `RicWellPathExportMswTableData::generateCellSegments` — `CVF_ASSERT( wellPathGeometry )` on a null geometry | [#14121](https://github.com/OPM/ResInsight/issues/14121) CLOSED, fixed by `253d57f1a5` |
| `4bd3f3b19531` | frame `[16]` `RiaGrpcApplicationInterface::processRequests` — unrelated gRPC shutdown crash | none (unlinked) |
| `b80de5fc87c2` | frame `[3]` `RigEclipseWellLogExtractor::calculateIntersection` — the crash #14185 is actually about | #14185, fixed by `f1218e527f` (#14183) |

**The remaining crash is not the #14121 null-geometry bug**, even though it shares the
call chain. In v2026.02.2 — the only build that reported it —
`RigEclipseWellLogExtractor.cpp:82` is

```cpp
const RigCell& cell = m_caseData->mainGrid()->cell( globalCellIndex );   // line 80

if ( cell.isInvalid() || cell.subGrid() != nullptr ) continue;           // line 82  <-- SIGSEGV
```

`m_wellPathGeometry` cannot be null on this path: `findCellIntersectionInfosAlongPath`
constructs a dummy `RigWellPath` from the coordinate vector, and the v2026.02.2
constructor takes `gsl::not_null`. What faults is the *cell index*. `RigMainGrid::cell()`
indexes `m_cells` without a bounds check, so an out-of-range `globalCellIndex` computes
a valid-looking address at line 80 and faults on the first member read at line 82.

The index comes from `findCloseCellIndices` → `RigMainGrid::findIntersectingCells`,
which in v2026.02.2 lazily built the `mutable m_cellSearchTree` with **no
synchronisation** — so a tree being built or destroyed by another thread could be
queried, yielding garbage indices. That is fixed on dev by
[`f1218e527f`](https://github.com/OPM/ResInsight/commit/f1218e527f) ("#14183 Fix crash
in AABB cell search tree from unsynchronized lazy build", 2026-06-10), which serialises
the build behind `m_cellSearchTreeMutex` and holds a local `cvf::ref` to the tree for
the duration of the query. Both `f1218e527f` and `253d57f1a5` are contained in
**v2026.06.0 and v2026.06.1**.

All 4 reports are from 2026.02.2, none after the week of 2026-06-26, and the flat count
of 1 per week across 4 overlapping CSVs is most likely a **single crash event**.

**Recommendation.** Close #14185 on GitHub as fixed by #14183 — it is the last thing
keeping an open issue attached to a resolved signature. Longer term, add a
`fixed_commit` field to the registry so group D can be verified rather than trusted,
and make `link_issues.py` prefer the *top* frame of a pasted stack over any frame, which
is what produced all four mis-links here.

## E. Marked fixed, still crashing — 42 signatures in the latest week

Not part of the "not fixed or started" backlog by status, but it is where the actual
crash volume is, and it is what the "closed out" figure in the weekly reports hides.

In the week of 2026-08-07, **42 signatures with a closed issue or merged PR produced
105 of the week's 108 crash reports**. Across the current release line, 337 of the 340
occurrences on 2026.06.1+ sit on signatures already marked fixed.

| Signature | Top frame | Week 2026-08-07 | cur | Reference |
|---|---|---:|---:|---|
| `4b98ba7f3609` | (unsymbolized crash site) | 22 | 51 | [#14270](https://github.com/OPM/ResInsight/issues/14270) CLOSED + [PR #14271](https://github.com/OPM/ResInsight/pull/14271) MERGED |
| `36a46843df47` | `cvf::ref<RigActiveCellInfo>::p` | 6 | 5 | [PR #14495](https://github.com/OPM/ResInsight/pull/14495) MERGED |
| `49d08ca2f441` | `caf::AppEnumMapperBase::defaultValue` | 6 | 4 | [#14368](https://github.com/OPM/ResInsight/issues/14368) CLOSED + [PR #14369](https://github.com/OPM/ResInsight/pull/14369) MERGED |
| `22ad7ead4114` | `RifEclipseOutputFileTools::timeSteps` | 5 | 18 | [#13927](https://github.com/OPM/ResInsight/issues/13927) CLOSED |
| `963953dcf22e` | `RifEclipseOutputFileTools::timeSteps` | 4 | 25 | [#13927](https://github.com/OPM/ResInsight/issues/13927) CLOSED |
| `287c62e9cb25` | `RicCreateRftPlotsFeature::onActionTriggered` | 4 | 8 | [#14450](https://github.com/OPM/ResInsight/issues/14450) CLOSED + [PR #14454](https://github.com/OPM/ResInsight/pull/14454) MERGED |
| `49fcd1424922` | `manageTerminate` | 4 | 8 | [#14451](https://github.com/OPM/ResInsight/issues/14451) CLOSED + [PR #14455](https://github.com/OPM/ResInsight/pull/14455) MERGED |
| `f20aa1d03f76` | `RigEclipseCaseData::formationNames` | 3 | 8 | [#14448](https://github.com/OPM/ResInsight/issues/14448) CLOSED + [PR #14449](https://github.com/OPM/ResInsight/pull/14449) MERGED |
| `d2161286a077` | `caf::PdmUiEditorHandle::updateUi` | 3 | 5 | [#14175](https://github.com/OPM/ResInsight/issues/14175) CLOSED |

The benign explanation covers most of it: 98 of the week's 108 reports come from
**2026.06.1**, and nearly every fix listed above merged *after* that build was cut, so
users are hitting bugs already fixed on `dev`. That is expected and resolves itself at
the next release.

Two entries do not fit that explanation cleanly and are worth a second look:

- **`#13927` / `RifEclipseOutputFileTools::timeSteps`** — two separate signatures
  (43 occurrences on 2026.06.1+), still arriving in the latest week, with the issue
  closed and **no fix PR recorded at all**. Nothing in the registry says what fixed it.
- **`4b98ba7f3609`** — 22 reports in one week, the single largest entry, but the
  signature is `(unsymbolized crash site)`. The worklist deliberately skips
  unsymbolized signatures as "not individually actionable", so this volume is invisible
  to triage regardless of its state. It is worth checking whether the build's symbol
  upload is failing rather than treating it as one bug.

## What to do next

1. **Verify #13927 is actually fixed** — highest current-release volume of anything
   claiming to be resolved, with no fix PR on record (group E).
2. **Investigate the two texture-coords asserts** (`7ee60e04022b`, `94ae601b2092`) —
   the only unfixed signatures still arriving on the current release, new this week,
   with a shared and testable hypothesis (group B).
3. **Run the gRPC / project-close paths under a memory sanitiser** — one experiment
   covers three signatures that triage abandoned as "corruption from elsewhere"
   (group B, reason 2).
4. **Pick up #11342 as one item** across its three signatures; it is the largest
   unfixed crash in the registry (groups A and B).
5. **Close #14185** as fixed by #14183, now that its five signatures have been split by
   actual crash site (group D).
6. **Check symbol upload for `4b98ba7f3609`** — 22 reports a week that triage
   structurally cannot see (group E).
7. **Harden the bookkeeping**: a `fixed_commit` field would let group D be verified,
   and matching `link_issues.py` on the top frame rather than any frame would prevent
   the #14185-style pile-up from recurring.
