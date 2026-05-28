# Evidence Tagging

External claims must be tagged so reviewers can tell fact from assumption quickly.

## Tags

| Tag | Meaning | Review handling |
|---|---|---|
| `[verified:YYYY-MM-DD:URL]` | The author checked the source on that date. | Usable, but sample-check before major decisions. |
| `[needs-review]` | Unverified memory, summary, second-hand claim, or uncertain source. | Cannot enter a binding decision. |
| `[assumption]` | Reasoned inference without external proof. | Allowed only for low-risk planning. |
| `[stale:YYYY-MM-DD]` | Previously verified but now outside the freshness window. | Treat as `needs-review`. |
| `[tested:YYYY-MM-DD:<artifact>]` | Verified by local test, script, benchmark, or code inspection. | Usable if artifact is available. |

## Must Tag

- Repository activity, maintenance, API support, pricing, rate limits, model capability, benchmark results, paper claims, and current product claims.
- Any claim that could change over time.

## Does Not Need Tagging

- Local code facts directly inspected in the current workspace.
- Local test results when the command and output summary are included.
- Explicit PM/user decisions already recorded in `decisions/`.

## Rule

No untagged external claim may be used as the basis for a decision.

