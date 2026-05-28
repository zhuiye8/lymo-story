---
name: novel-rearchitecture-supervisor
description: Supervise AI-novel platform rewrites, architecture reviews, phase reports, decision records, and PM/engineer handoffs for projects moving from simple generation pipelines to editorial-office systems with story contracts, scene cards, context compilers, critic loops, and revision workflows.
---

# Novel Rearchitecture Supervisor

Use this skill when supervising or reviewing an AI fiction-writing platform rewrite. The goal is to keep execution aligned with an editorial-office architecture rather than a longer multi-agent generation pipeline.

## Core Review Standard

Check every proposal against these invariants:

- Keep the target architecture centered on an AI editorial office: story contract, scene design, context compilation, prose rendering, criticism, and revision.
- Treat world simulation as a source of candidate events and constraints, not as the direct author of the manuscript.
- Narrow the writer into a prose renderer. Do not let it plan plot, resolve canon, select POV, and write prose in one step.
- Require scene cards before prose generation. A scene card must include desire, obstacle, opposition, turning point, cost, emotional shift, payoff, hook, and forbidden drift.
- Require a context compiler before writer calls. The writer must receive scene-level minimal context, not full history.
- Require a critic and revision loop. A consistency checker at the end is not enough.
- Require an evaluation baseline before claiming quality improvement.
- Mark external project claims as verified, needs-review, or assumption.

## Supervision Workflow

1. Read the current board first.
   - In this project: `workspace/supervision-board.md`
   - In another project: look for the equivalent active-status file.
2. Read only the proposal or report under review.
3. Classify the artifact:
   - architecture proposal
   - phase implementation plan
   - phase report
   - decision request
   - risk escalation
4. Review for alignment, evidence, measurable acceptance criteria, cost, risks, and rollback.
5. Respond with one of:
   - `approve`
   - `approve-with-conditions`
   - `revision-needed`
   - `reject`
   - `blocked-pending-evidence`
6. Write binding outcomes into `decisions/`. Use `inbox/` only for questions and short reports.

## Red Flags

Escalate if any of these appear:

- The plan adds more agents but does not add evaluation, revision, or context compilation.
- Writer receives full bible, full memory, or full chapter history.
- World simulation output is treated as the chapter outline without narrative selection.
- A module claims quality improvement without a baseline and sample size.
- The proposal imports a major external dependency without a PoC, fallback, or cost estimate.
- The plan uses current internet/model claims without dated sources.
- The phase has no exit criteria.

## Handoff Format

Ask engineers to use concise templates:

- Proposal: `templates/proposal.md`
- Phase report: `templates/phase-report.md`
- Decision: `templates/decision-record.md`
- Question: `templates/question.md` with a required default action
- Phase gate: `templates/phase-gate.md`
- Review request: `templates/review-request.md`

If templates are unavailable, request these fields:

```text
Goal:
Scope:
Non-goals:
Design:
Evidence:
Acceptance criteria:
Risks:
Cost:
Rollback:
Ask:
```

## Reference

For this project's specific operating protocol, read `references/protocol.md`.

For evidence standards, read `references/evidence-tagging.md`.

For long-lived decisions, read `references/standing-decisions.md`.

For engineer-side handoff discipline, read `references/engineer-side.md`.
