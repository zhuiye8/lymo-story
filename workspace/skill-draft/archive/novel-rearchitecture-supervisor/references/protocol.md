# Novel Rearchitecture Supervision Protocol

## Architecture Vocabulary

- `Story Contract`: reader promise, genre contract, pacing expectation, forbidden drift.
- `Scene Card`: scene-level drama unit with desire, obstacle, turn, cost, and hook.
- `Context Compiler`: builds minimal scene context from canon, memory, evidence, and POV knowledge.
- `Prose Renderer`: writes prose only after scene and context are prepared.
- `Critic Room`: continuity, drama, style, pacing, reader, and market review.
- `Revision Loop`: targeted rewrite from critique, not blind full regeneration.
- `World Simulation`: offscreen actors, faction goals, clocks, and candidate events.
- `Narrative Director`: selects what the chapter shows, hides, delays, or pays off.

## Review Checklist

Use this checklist for every proposal:

```text
[ ] Does it improve the editorial-office architecture?
[ ] Does it reduce writer responsibility?
[ ] Does it improve scene-level drama?
[ ] Does it improve context selection?
[ ] Does it improve memory/canon correctness?
[ ] Does it add measurable evaluation?
[ ] Does it include cost and rollback?
[ ] Does it distinguish verified evidence from assumptions?
```

## Decision Priority

When time is limited, decide in this order:

1. Architecture invariants.
2. Phase scope.
3. Evaluation method.
4. Data model.
5. External dependency.
6. UI polish.

## Recommended Phase Gate

No phase should start unless it has:

- one-sentence goal
- non-goals
- data model or artifact schema
- acceptance criteria
- test/evaluation method
- cost bound
- rollback or exit condition

