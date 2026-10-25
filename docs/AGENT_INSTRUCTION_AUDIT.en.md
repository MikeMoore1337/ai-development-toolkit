# AGENTS.md / CLAUDE.md structural audit (#376)

Method inspiration: [kjmagnan1s/claude-md-creator](https://github.com/kjmagnan1s/claude-md-creator) pinned at `742314bcc5f190b40ae04f6332026d6f6bc77085`; MIT © 2026 Kevin Magnan. No upstream installer or code was executed or copied.

Existing `scripts/profile_metrics.py` measures skill/profile size, not local agent-instruction duplication or broken references. This addition is a **separate opt-in read-only inspection**, not a new skill manager or instruction writer.

Run `python scripts/audit_agent_instructions.py --root .`. JSON output contains relative file paths, line numbers and coarse finding codes, never original rule text. Flags exact normalized cross-file duplicate bullets; broken/out-of-bounds `path.ext:line` references; unsafe symlink, oversized and unreadable instruction files. Duplicate text is NOT proof of contradictory meaning. No findings is NOT a semantic correctness or security guarantee.

The scanner is bounded (256 files, 256 KiB each), ignores generated directories, rejects a root symlink and never modifies files. No paid API, network, hooks, auto-installation, remote logging, or changes to other projects. Rule length guidance is advisory, never a mandatory override of project owner gates. Tests: `python -m unittest discover -s tests -p test_audit_agent_instructions.py -v`. To revert, remove this independent optional scanner, tests and documentation.
