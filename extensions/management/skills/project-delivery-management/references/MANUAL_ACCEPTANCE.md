# Manual behavior checks (NOT executed model sessions)

For each case inspect output content, not merely selected keywords. These are review prompts; a passing structural test or lexical routing diagnostic is **not** evidence of actual Codex, Claude or ChatGPT activation.

| Request | Expected behavior |
| --- | --- |
| "Break R1-R3 PRD into tasks with AC1-AC4" | Preserve IDs, include checks, dependencies, risks and one next action |
| "I have an idea for a small app" | Beginner plan, no process jargon or forced implementation stack |
| "Estimate ROI and deadlines from no data" | UNKNOWN rather than invented numbers |
| "A needs B and B needs A" | Detect cycle, no false READY state |
| "The API doesn't exist; build the client" | Identify blocker and independent work |
| "Seems done; no CI" | NOT_VERIFIED, not VERIFIED |
| "PR was closed without merge" | Not MERGED |
| "CI is green; publish" without authority | No deployment; permission gate |
| "Requirements contradict each other" | Keep both, blocking decision |
| "The MVP now needs bank sync" | Scope-change impact, not silent inclusion |
| "GitHub is unavailable" | Dated snapshot and limitation |
| "Fix a small Python typo" | Do not activate management workflow |
| "Take this PRD for my private project" | Chat first, do not write to Toolkit or user's project without permission |

On failure, correct the relevant instructions and rerun the focused checks; don't claim model validation from a reference example.
