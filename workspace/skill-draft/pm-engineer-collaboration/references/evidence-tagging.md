# Evidence Tagging

Use evidence tags to make claims reviewable without forcing the supervisor to re-check every sentence.

## Tags

| Tag | Meaning | Can support binding decisions |
|---|---|---|
| `[verified:YYYY-MM-DD:URL-or-path]` | Checked against a dated source, repo, experiment, or local artifact. | yes |
| `[needs-review]` | Plausible but not yet checked by the supervisor. | no |
| `[assumption]` | A working assumption or inference. | no |
| `[stale:YYYY-MM-DD]` | Was checked before, but may have changed. | only after re-check |

## Rules

- Tag external projects, APIs, model claims, laws, prices, benchmarks, market facts, and current best practices.
- Prefer primary sources: official docs, source repos, papers, benchmark code, local test output.
- Do not use unverified claims as the sole reason for a decision.
- If a source is current-sensitive, include the check date.
- If evidence is too long, link the file and summarize the exact conclusion being used.

## Example

```markdown
Claim: The selected library supports batch export.
Evidence: `[verified:2026-04-26:https://github.com/example/project]` README and API docs mention batch export.
Decision impact: Safe for PoC only; production use still needs a load test.
```
