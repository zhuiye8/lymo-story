# Standing Decision arch-001: editorial office architecture

| Field | Value |
|---|---|
| ID | arch-001 |
| Approved | 2026-04-26 by supervisor |
| Source proposal | `docs/rearchitecture_blueprint.md`; `workspace/plans/2026-04-26-rearchitecture/` |
| Status | active |
| Revisit trigger | Phase 0 evidence shows this architecture cannot outperform the current baseline, or PM changes the product objective. |

## Decision

The rewrite must target an AI editorial-office architecture, not a longer linear multi-agent generation pipeline.

## Rationale

The current failure pattern is not simply "agent count is too small". The core problem is weak narrative control: long context drift, prose without focus, writer agents doing too many jobs, and quality checks arriving after the manuscript is already written. The target system must separate story contract, scene design, context compilation, prose rendering, criticism, and revision.

World simulation remains useful, but only as a source of candidate events, pressure, and constraints. It must not become the direct author of chapter outlines or prose.

## Constraints On Future Proposals

- A proposal must preserve scene cards before prose generation.
- A proposal must preserve a context compiler before writer calls.
- A proposal must keep the writer focused on prose rendering.
- A proposal must include critic and revision loops, not only final consistency checks.
- If a proposal makes world simulation central, it must explain how narrative selection and reader experience stay under editorial control.
