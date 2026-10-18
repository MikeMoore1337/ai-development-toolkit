---
name: motion-quality
description: Review and improve animation purpose, timing, accessibility and performance. Use when adding, auditing or optimizing web or mobile motion.
---

# Motion quality and restraint
1. Define interaction intent: feedback, orientation, continuity or affordance. No motion solely to display technical ability.
2. Check whether existing app animation patterns already cover the desired behavior.
3. For entrances, choose suitable easing and duration; avoid hard-coded universal durations or nonessential large movements.
4. Prefer transform/opacity for frequently animated layers when possible; profile actual slow paths, layout/repaint, scroll jank and low-end devices.
5. Provide usable reduced-motion behavior; animations must not hide actions or block interactions.
6. Inspect trigger/cancellation, interrupted gestures, keyboard navigation and nested scrolling.
7. Verify measured behavior in a browser/device; do not claim frame-rate improvements without measurements.

**Output:** interaction purpose, minimal implementation, reduced-motion fallback, actual performance observations.
