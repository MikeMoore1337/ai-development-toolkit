# #373 / Public source-backed Replica comparison pilot

This source-only pilot uses an independently published competitor description and a **separately inspected target project's public source tree**. The specific target source revision, internal file names and claims are maintained in [Toolkit Issue #373](https://github.com/MikeMoore1337/ai-development-toolkit/issues/373), not in generic public-toolkit documentation.

The public original reference is [Hevy Track Workouts](https://www.hevyapp.com/features/track-workouts/) and its [2026 features guide](https://help.hevyapp.com/hc/en-us/articles/33106320824727-Everything-You-Need-to-Know-About-the-Hevy-App-2026-Features-Guide). The first-party publisher describes set completion and previous performance contexts. No sign-in, paywall bypass, page scraping, assets or screenshots are used.

The accompanying `pilot.csv` records two **source-backed** items with public source links, an explicit `partial` placeholder and `NOT_TESTED` runtime. The original `replica-diff/parity.py` yields a **demonstration of scoring arithmetic**, not an observed percentage of live product parity or production readiness. Never quote its synthetic numeric result as a measured product comparison.

The Toolkit opt-in adapter runs only an exactly pinned, clean original upstream `77c9436fb3d18c3d58169efb8caf4fe906b0dc51`. The optional [source-only CI workflow](../../.github/workflows/replica-public-parity.yml) checks and executes the original upstream in a disposable runner. No paid API, model calls, hooks, auto-installs or changes to any consuming project.

Actual user-flow execution, screenshots, browser errors, saved results, accessibility and performance measurements: **NOT_TESTED**. Any target product/UI change requires separate approval. See [RU guide](../../docs/ru/REPLICA_PUBLIC_PARITY.md) and [EN guide](../../docs/en/REPLICA_PUBLIC_PARITY.md).
