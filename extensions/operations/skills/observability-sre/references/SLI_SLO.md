# SLI, SLO and error budget: measured populations

**SLI** is a precisely measured quality ratio for a specified user journey; **SLO** is an owner-approved target for that indicator over an agreed window. HTTP 200 does not prove a committed business operation. A complete period is a prerequisite for any completed-period verdict.

Event-based specification fields: `indicator_id`, `service`, `user_journey`, `eligible_events`, `good_events`, `exclusions`, `measurement_source`, `time_window`, `objective`, `data_quality`, `actual_result` and `evidence`. Declare denominator and numerator using identical event identities and population semantics. Never silently exclude retries, timeouts or bad events. If no owner requirement exists, label objective `PROPOSED`; do not claim it is adopted.

For `N > 0` fully observed eligible operations, `G` good and `B=N-G` bad, use **exact decimal arithmetic**:
- `SLI=G/N`;
- `allowed_bad=N*(1-SLO)` (real-valued equivalent, preserve decimals);
- `spent_bad=B`;
- `remaining=allowed_bad-spent_bad`; if negative, the budget is exhausted.
- If operationalizing an integer maximum, `floor(allowed_bad)` is the maximum compliant bad-event count. Rounding UP can hide an objective miss. Never round computed results before the comparison.

The fictional reference has `N=500`, `G=488`, `B=12`, synthetic SLO `0.99`: SLI `97.6%`, allowed `5`, spent `12`, remaining `-7`. None of these are live product metrics.

Reject zero denominator, negative counts, overlapping categories, numerator outside denominator, incomplete window, incompatible revisions, unspecified sampling and an unapproved objective. For time-based SLO use durations of eligible and good intervals, not request counts. Error-budget burn indicates reliability impact **not root cause**. Real objective, alert thresholds and release-policy use require owner approval.
