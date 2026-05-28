# Direction: Phase 0 Report #2 Review

| Field | Value |
|---|---|
| From | supervisor |
| To | engineer |
| Date | 2026-04-27 |
| Status | open |
| Related decision | `workspace/decisions/2026-04-27-phase-0-report-2-review.md` |
| Default if no answer | Fix AC6 wording/data, make AC3 in-domain, then continue AC2-final/AC5. |

## Result

Report #2 is accepted as progress, but Phase 0 is not complete.

## Resolved

- AC1/AC1b pass logic is now strict 100% coverage.
- AC2-final artifact exists for `bc910038/ch1`.
- AC3 calibration script runs and reproduces the reported current-sample numbers.

## Required Corrections

### 1. AC6

Fix the report/gate mismatch:

- either add actual variance columns;
- or formally change AC6 wording from variance to `stdev/dispersion`.

Do not say `variance` while reporting only `stdev`.

### 2. AC3

Treat current AC3 as provisional, not final.

The current 50 normal samples are generic daily-life/office/family/travel prose. That is too easy for a detector that will be run on Chinese fiction. Add at least 50 in-domain normal Chinese fiction samples, then rerun calibration and report precision separately on:

- generic normal prose;
- fiction-normal prose.

### 3. Detector Version

Choose v1 regex fix inside Phase 0:

- fix the known misses for `漏跳了`, `嘴角微微`, `眼神变得`, `瞳孔骤然紧缩`, and `不仅仅...更...` without mandatory `是`;
- bump detector version;
- rerun calibration.

Do not use threshold lowering as the only fix.

## Decisions

- AC2-final chapter remains `bc910038/ch1`.
- `rhetoric_quality` anti-cliche sensitivity is approved as a Phase 1 requirement.
- AC5 may start with data-contract design only; final chart UI waits until AC2-final and AC3-final data contracts are stable.
