# #373 / Бounded Replica pilot: Hevy vs YFC (source-based only)

**Evidence snapshot: 2026-10-25.** Pinned YFC `main@605fe95b5c6643427d13edbc5bd48733809ee95b` and pinned Replica `77c9436fb3d18c3d58169efb8caf4fe906b0dc51`. The prototype is public **source inspection**, not signed-in usage or a live browser test.

Public independent original feature descriptions: [Hevy Track Workouts](https://www.hevyapp.com/features/track-workouts/) documents marking sets complete, weight/reps logging, previous workout references and rest timing. The [Hevy help centre](https://help.hevyapp.com/hc/en-us/articles/33106320824727-Everything-You-Need-to-Know-About-the-Hevy-App-2026-Features-Guide) describes the 2026 workout features.

Existing YFC repository evidence: [TodayWorkout.tsx @ exact YFC SHA](https://github.com/MikeMoore1337/your-fitness-coach/blob/605fe95b5c6643427d13edbc5bd48733809ee95b/frontend/src/features/workouts/TodayWorkout.tsx) includes `Завершить подход` control, a contextual `Предыдущий подход` result, and active rest journal. The [workout history UI](https://github.com/MikeMoore1337/your-fitness-coach/blob/605fe95b5c6643427d13edbc5bd48733809ee95b/frontend/src/features/workouts/WorkoutHistory.tsx) shows measured rest records. Existing [YFC UX requirements](https://github.com/MikeMoore1337/your-fitness-coach/blob/605fe95b5c6643427d13edbc5bd48733809ee95b/docs/ux/post-release-reset/CORE_FLOW_SPEC.md) specify the intended active workout behavior but are **not test evidence**.

## Pilot matrix

File: `pilot.csv`. Two features: set completion (must) and recent workout context (should). Both explicitly `clone=partial` to represent **only confirmed source/UI evidence**, not that half of each feature works in production. Parity.py's weighted percentage is a **synthetic demonstration of arithmetic**, not a measured feature-parity or production-readiness percentage. **No numeric comparison should be quoted externally**. Actual user flow, screenshots, loading/error states, latency and persisted results: `NOT_TESTED`.

## Confirmed technical capability

The original `replica-diff/parity.py` runs without dependency installation. The Toolkit `scripts/replica_public_parity.py` additionally enforces source provenance, explicit URLs, no false `UNKNOWN -> NO` substitution and opt-in. GitHub workflow `.github/workflows/replica-public-parity.yml` pins and runs the *actual original* upstream in a temporary Linux job with synthetic/public input. It does not log in to Hevy, crawl pages, install plugins or modify YFC.

## Scope boundary

This acceptance covers portable method/source and an auditable public **source comparison** only; it does **not** establish production UX equivalence. Real screenshot/browser comparison and any proposed YFC UI change require separate reviewed approval and are **NOT_RUN** here. Neither competitor assets nor screenshots are shipped.
