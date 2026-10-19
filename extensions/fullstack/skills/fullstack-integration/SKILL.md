---
name: fullstack-integration
description: "Use when aligning frontend and backend contracts and coordinating deployments across layers."
---

# fullstack integration

Inspect the existing project boundaries, technology and deployment constraints before proposing a change. Follow project approval gates.

1. Trace a real user action through UI state, network, service, storage and response or event.
2. Confirm field formats, nullable behavior, error mapping, credentials, cache rules and correlation identifiers at each seam.
3. Plan rollout for old/new clients when frontend and backend can be deployed independently.
4. Check timeouts, cancellation, duplicate requests, stale results and partial success end-to-end.
5. Verify success and failure with a real seam where available; label mocks, local and staging evidence distinctly. Do not supersede a feature-delivery controller.

**Output:** Cross-layer sequence, contracts, rollout order and verified seam behavior.
