# Comparable performance experiment

**Context:** A slow list view has a suspected rendering bottleneck. Define interaction = navigate to list with 1,000 representative items; metric = time to interactive list; device, build, viewport, network, cache and measurement tool fixed.

**Procedure:** Capture at least three baseline runs, then implement a minimal change and capture candidate runs under the same conditions. Retain raw samples, errors and relevant long-task/request traces. Compare median and spread; investigate outliers instead of hiding them.

| Stage | Illustrative measurements (ms) | Median |
| --- | --- | --- |
| Baseline | 410, 430, 390 | 410 |
| Candidate | 305, 295, 315 | 305 |

These values are *fictional teaching data*, not results from this Toolkit or any application. Observed delta in this hypothetical sample = 105 ms lower median (about 26%). It cannot demonstrate real-world benefit without actual comparable collection.

**Negative case:** comparing development build on fast Wi-Fi to production build on a throttled mobile link is invalid. With no baseline, say "optimization implemented; effect NOT_MEASURED", never "performance improved".

**Acceptance:** same instrument/settings, linked raw measurements for real work, working interactions, no correctness regressions and an explicit caveat about sample variability.

**Limits:** Median alone does not capture tails, interaction failure rate, hardware classes or user field performance. Choose metrics appropriate to the user journey.
