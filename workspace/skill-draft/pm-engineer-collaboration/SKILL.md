---
name: pm-engineer-collaboration
description: Coordinate efficient asynchronous PM/engineer collaboration for software projects. Use when Codex needs to supervise developers, structure handoffs, review proposals, define phase gates, record decisions, answer implementation questions, manage risk escalations, or create reusable communication protocols across projects.
---

# PM Engineer Collaboration

Use this skill to keep project communication short, auditable, and hard to misinterpret. This is a communication protocol, not a domain architecture skill.

## Core Rules

- Separate generic process from project-specific policy. Put reusable workflow in the skill; put project architecture, product goals, and technical constraints in the project's workspace.
- Treat the board as the entry point. Read the current board before reviewing plans, reports, or questions.
- Keep messages short. Put detailed evidence in linked files instead of long inbox threads.
- Make decisions durable. Binding decisions go into `decisions/`; chat and inbox messages are not final authority.
- Require a default action for every question. If no answer arrives by the stated time, the requester must be able to proceed safely.
- Tag evidence before using it for decisions. External claims need `verified`, `needs-review`, `assumption`, or `stale` status.
- Use phase gates before implementation starts. A phase needs goal, non-goals, artifact schema, acceptance criteria, cost bound, and rollback trigger.
- Use standing decisions sparingly. They are for rules that should not be re-litigated every week.

## Workflow

1. Read the active board, usually `workspace/supervision-board.md` or equivalent.
2. Classify the artifact:
   - proposal
   - phase gate
   - phase report
   - decision request
   - question
   - risk escalation
   - review request
3. Check the matching template in `assets/templates/`.
4. Review for owner, deadline, default action, evidence, acceptance criteria, risks, cost, rollback, and standing-decision conflicts.
5. Respond with one status:
   - `approve`
   - `approve-with-conditions`
   - `revision-needed`
   - `reject`
   - `blocked-pending-evidence`
6. Update the durable artifact:
   - `decisions/` for binding outcomes
   - `inbox/` for short questions and replies
   - the board for current state and next action

## Workspace Shape

Recommended project workspace:

```text
workspace/
├── README.md
├── supervision-board.md
├── project-brief.md
├── templates/
├── plans/
├── decisions/
│   └── standing/
└── inbox/
    ├── from-pm/
    └── from-engineer/
```

Keep `README.md` generic. Put domain-specific review rules in `project-brief.md`, `decisions/standing/`, or the active board.

## When To Read References

- Read `references/protocol.md` when setting up or repairing the collaboration workspace.
- Read `references/evidence-tagging.md` when reviewing research, vendor claims, benchmarks, or current web/project claims.
- Read `references/standing-decisions.md` when creating or checking long-lived decisions.
- Read `references/engineer-side.md` when writing instructions for the developer or reviewing whether a handoff is well-formed.

## Templates

Copy from `assets/templates/` when creating artifacts:

- `proposal.md`
- `phase-gate.md`
- `phase-report.md`
- `decision-record.md`
- `question.md`
- `review-request.md`

If a project already has equivalent templates, preserve its naming and adapt the required fields rather than forcing a rename.
