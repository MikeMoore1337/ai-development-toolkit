# Replica Skill - public evidence-bound feature comparison

Toolkit Issue #373. Reuse [Jakeschincariol/replica-skill](https://github.com/Jakeschincariol/replica-skill) pinned to `77c9436fb3d18c3d58169efb8caf4fe906b0dc51`; the upstream LICENSE contains MIT terms. No third-party executable code is copied into Toolkit, no automatic skill installation, inference or API use.

Selective source references: `replica-recon/SKILL.md` maps public screens/flows/states; `replica-diff/SKILL.md` and original `replica-diff/parity.py` compare evidence-backed feature matrices; `replica-test/SKILL.md` provides QA ideas **for the target application only**. This does not install the clone/build/payment/deploy stack or a second orchestrator. No proprietary assets, private APIs, unauthorized accounts or competitor load tests.

## Explicit offline use

```sh
git clone https://github.com/Jakeschincariol/replica-skill.git /tmp/replica-skill-pinned
git -C /tmp/replica-skill-pinned checkout --detach 77c9436fb3d18c3d58169efb8caf4fe906b0dc51
python scripts/replica_public_parity.py --upstream /tmp/replica-skill-pinned
python scripts/replica_public_parity.py --upstream /tmp/replica-skill-pinned --matrix /path/to/reviewed_features.csv
```

The UTF-8 CSV must have `feature,area,priority,original,clone,notes,evidence_url,target_evidence` headers. Allowed priorities are must/should/could; source feature status yes/no; the target application status yes/partial/no/skip. For competitor features reported as present, provide a public HTTPS evidence URL. Claims that the target application supports a feature require source/test/screenshot evidence. **UNKNOWN must not be scored as NO**. Missing evidence causes refusal, not a fabricated parity percentage.

The adapter verifies a clean, exact pinned upstream commit and the source Git blobs; it invokes only original `parity.py` through isolated Python, emits stdout and does not modify files. CSV cap: 1 MiB/250 rows. No network/API activity by the adapter. Existing the target application product/UI changes require separate approval.

## Evidence boundary

Run `python -m unittest discover -s tests -p test_replica_public_parity.py -v` for offline adapter regression tests. These do not prove the target application parity or execute the original upstream against a real competitor. Close #373 only after pinned upstream execution, independently sourced public pilot and exact-head/post-merge CI.
