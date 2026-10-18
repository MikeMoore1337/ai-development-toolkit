# Test design worksheet

| ID | Requirement | Partition / transition | Setup | Action | Observable oracle | Risk |
|---|---|---|---|---|---|---|
| T-01 | R-01 | Valid user | Active account | Submit request | State transitions to accepted and event has correct correlation ID | High |

Boundary checklist: minimum/maximum, just outside the range, empty and malformed, absent/unknown role, retries, concurrent requests where meaningful. Remove inapplicable cases deliberately. Do not claim coverage without execution evidence.
