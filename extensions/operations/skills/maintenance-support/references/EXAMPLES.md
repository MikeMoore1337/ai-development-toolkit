# Entirely synthetic support journeys

Run `python scripts/validate_maintenance_support.py` from Toolkit root. No real GitHub Issues, customer emails, telemetry, production versions or releases are used.

1. `reference.json`: fictional v1.1 save problem -> report -> local reproduction -> possible duplicate -> engineering Issue/PR -> targeted QA PASS -> published v1.2 -> canary deployment -> user still on v1.1, support message DRAFT, issue remains OPEN.
2. `pre_release.json`: identical code revision with test PASS but no merge/release/deployment, so only FIX_TESTED may be said.
3. `user_verified.json`: an additional scoped synthetic user confirmation can close the report as VERIFIED_FOR_USER.
4. `rollback.json`: synthetic canary rollback revokes current deployment claim but keeps previously confirmed QA and release history.
5. `unreproduced.json`: conflicting reports, two versions, insufficient production access, possible old duplicate, no confirmed cause/fix. A polite DRAFT requests a small additional detail.

`broken_cases.json` declares intentionally invalid mutations; the **same independent `audit()`** must accept correct cases and reject each invalid stage/evidence/permission claim. Real support efficacy, model activation, external send and production fix: NOT_TESTED.
