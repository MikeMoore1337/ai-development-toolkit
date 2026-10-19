# Account preferences: one vertical slice

**Goal:** An authenticated user edits the preferred language. Only that user's preference changes; UI reflects the saved server value.

| Boundary | Contract | Error/observation |
| --- | --- | --- |
| UI -> API | PUT /me/preferences {"language":"fi"} with current version | Loading state; block duplicate submit or use safe conditional update |
| API -> auth | Resolve caller from existing session; do not trust a supplied user_id | 401 missing identity, 403 insufficient permission |
| Service -> storage | Update one caller-owned row, version = expected version | 409 on stale version; no unrelated row changed |
| Storage -> response | 200 {"language":"fi","version":8} after committed write | Explicit canonical server value |
| Response -> UI | Commit acknowledged language and version only for current request | Ignore obsolete request completion; show retry/conflict if needed |

**Negative path:** User in another tenant sends a crafted identifier; backend must not update someone else's preference. Two tabs update version 7 concurrently: one wins, other receives conflict instead of silently overwriting.

**Verification:** seed two isolated users, send allowed update, assert persisted value and response; attempt foreign update and assert no side effect; race two versions; force 500 and confirm UI retains edit plus actionable recovery. Separate mocked UI assertions from real API/database evidence.

**Compatibility:** old clients may omit version until contract rollout is planned; do not silently require a new field while such clients remain. Prefer existing protocol conventions.

**Limits:** This is a proposed example, not deployed code or measured end-to-end runtime behavior.
