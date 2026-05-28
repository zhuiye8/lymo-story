# Decision: communication skill scope

| Field | Value |
|---|---|
| Decider | PM / supervisor |
| Date | 2026-04-26 |
| Status | approved |
| Related proposal | `workspace/inbox/from-engineer/2026-04-26-question-skill-improvements.md` |

## Decision

The reusable skill must be a generic PM/engineer collaboration protocol, not a novel-rearchitecture or story-generation supervisor skill.

## Rationale

The user's goal is to improve communication efficiency between supervisor and developer, then reuse that communication protocol in other projects. The Story Engine rewrite is the first project using the protocol, but its architecture choices must remain project-local.

## Options Considered

| Option | Result | Reason |
|---|---|---|
| Keep `novel-rearchitecture-supervisor` as the skill | rejected | It mixes communication process with one project's domain architecture. |
| Create generic `pm-engineer-collaboration` skill | accepted | It captures handoffs, decisions, phase gates, evidence, and defaults in a reusable way. |
| Split into generic skill plus novel-specific extension now | deferred | Possible later, but not needed for the current communication protocol. |

## Conditions

- Project-specific architecture rules stay in `project-brief.md`, `supervision-board.md`, and `decisions/standing/`.
- The generic skill may include templates and evidence rules, but not Story Engine architecture opinions.
- The archived novel-specific skill draft is not the active skill.

## Revisit Trigger

Revisit after this protocol is used through one full project phase or reused in a second project.

## Follow-Up

- [x] Create `skill-draft/pm-engineer-collaboration/`.
- [x] Archive the old novel-specific skill draft.
- [x] Update workspace README and supervision board to separate generic process from project-specific rules.
- [ ] After Phase 0, decide whether to install this as a global Codex skill.
