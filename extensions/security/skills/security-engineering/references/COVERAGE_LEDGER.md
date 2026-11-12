# Optional coverage-led audit (Cloudflare-inspired)

Adapts only **coverage and evidence discipline** from [cloudflare/security-audit-skill](https://github.com/cloudflare/security-audit-skill/tree/c1c8a8c1471069fb0e188eeaff69b8e8db6564a8) (MIT, © Cloudflare, Inc.). This is an original, reduced Toolkit record format, **not** the upstream schema, an installed skill or a replacement audit engine.

Only for an **explicitly requested, scoped security audit**. Existing `security-engineering` threat modeling, authorized execution boundaries and independent review rules take precedence. No production probing, foreign targets, new permissions, automated agent spawning, session collection or writes into the shared Toolkit repository.

## Procedure

1. Freeze the **exact source Git SHA** and explicit in-scope paths/subsystems; assign `unit` entries per trust boundary and attack class. Excluded and unchecked areas must remain visible.
2. Track every unit as `planned`, `covered`, `deferred` or `out_of_scope`. `covered` needs actual inspection/test evidence and an evidence level. `deferred` and `out_of_scope` require reasons; no unit may disappear to make coverage look complete.
3. Record findings as `confirmed`, `needs_validation` or `rejected`. Bind each to a unit, location and current source SHA. Unresolved findings have a precise `blocker`, no severity. Rejected claims require `disproof`.
4. A structurally `confirmed` record requires evidence, reproduction, observed outcome, impact, severity, non-`SOURCE_ONLY` evidence level and different hunter/verifier IDs. **Different strings do not prove distinct people, fresh agents or real tests.** Independently inspect those artifacts before accepting findings.
5. Report measured scope, `coverage_plan_complete` and deferred/unverified units, plus actual execution and reviewer provenance. `coverage_plan_complete` only describes the recorded plan, **not** security completeness.

## Fictional ledger

```json
{
  "scope": "fictional-notes/authz-only",
  "source_sha": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "units": [
    {"id": "u1", "boundary": "client-to-service", "attack_class": "IDOR", "source_location": "fixture/notes.py:12", "status": "covered", "evidence": "synthetic allow/deny oracle", "evidence_level": "SYNTHETIC_TESTED"},
    {"id": "u2", "boundary": "client-to-service", "attack_class": "expired-session", "source_location": "fixture/notes.py:20", "status": "planned"}
  ],
  "findings": [
    {"id": "F1", "unit_id": "u2", "source_sha": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "source_location": "fixture/notes.py:20", "verdict": "needs_validation", "blocker": "No expiry test evidence"}
  ]
}
```

Store any real audit record **outside Toolkit** in an explicitly authorized destination. Run read-only:

```sh
python scripts/validate_security.py --coverage-json /path/to/ledger.json
python scripts/validate_security.py --coverage-json /path/to/ledger.json --require-complete
```

First returns `coverage_plan_complete=false`; second fails until coverage and findings are actually resolved. The existing no-argument `python scripts/validate_security.py` continues unchanged.

## Pilot and rollback

`tests/test_security_coverage.py` compares existing threat/control validation with this **opt-in structural gate** on fictional security cases, rejects missing coverage, self-verification and stale source evidence. Neither this synthetic pilot nor the validator establishes real agent independence, exploitability, audit accuracy or cost savings: `NOT_MEASURED`. Revert this PR to remove the optional capability; no client or runtime installation is needed.
