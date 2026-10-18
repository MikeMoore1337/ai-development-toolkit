# Make Feature integration

Full Make Feature 0.3.0 source is included as an **opt-in** extension, not installed by default. It includes state/budget/workspace helpers, templates, references and unit tests. The original nested agent metadata was converted to the string-valued Agent Skills metadata format. See `extensions/make-feature/skills/make-feature/PORTABILITY_NOTES.md`.

Never activate Make Feature and `feature-delivery` as simultaneous task controllers. Project rules, user approvals, permissions and quality gates remain authoritative. No current client discovery, CI production run or multi-agent execution is claimed.
