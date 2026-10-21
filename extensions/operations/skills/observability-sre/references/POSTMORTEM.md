# Postmortem and recovery template

Produce one evidence-linked document after a fictional or authorized real investigation, tagging its origin. Use `UNKNOWN` / `UNDETERMINED` rather than fabricating dates, actions or participants.

1. **Summary and source scope:** incident ID, service, environment, exact revision, window, data quality.
2. **Verified user impact:** affected journeys, verified counts or `IMPACT_UNKNOWN`, duration, workaround and data integrity.
3. **Detection and recovery:** detection time and source; actual recovery time **only if verified**.
4. **Timeline:** observed event, source-clock timestamp, observation timestamp, evidence ID, interpretation and uncertainty.
5. **Logs/metrics/traces:** quality, sampling, missing intervals, clock skew, privacy filtering, evidence IDs.
6. **Competing hypotheses:** checks, supporting and contradicting evidence. Confirmed trigger, contributors, cause or `UNDETERMINED`; detection gaps and recovery limits.
7. **Actual response:** proposals, granted owner authority, actions truly executed, verification; do not attribute a synthetic rollback to production.
8. **What helped / hindered:** evidence availability, telemetry blind spots and operational delays, without blame.
9. **Prevention:** each corrective action has unique ID, owner if known, independently verifiable acceptance and test plan.
10. **Open questions / residual risks:** unknowns, future evidence needed and follow-up status.

Recovery oracle requires an explicit pre-agreed affected journey, post-action eligible/good counts and complete consecutive windows, no continuing critical symptom, state/integrity checks when applicable, and timestamps + evidence. A successful synthetic sample, a green CI job or a single successful request is insufficient. In the absence of trustworthy evidence, status remains RECOVERY_OBSERVED or investigation continues. No future task is treated as closed merely because a postmortem exists.

The portable response uses these evidence levels separately: SOURCE_ONLY, CONTRACT_VALIDATED, SYNTHETIC_TESTED, TELEMETRY_OBSERVED, INCIDENT_CORRELATED, ROOT_CAUSE_CONFIRMED, MITIGATION_AUTHORIZED, MITIGATION_EXECUTED, RECOVERY_VERIFIED, NOT_TESTED, UNDETERMINED. Their presence does **not** authorize advancing to the next level.
