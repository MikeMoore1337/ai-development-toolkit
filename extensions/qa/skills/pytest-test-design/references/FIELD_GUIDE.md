# Deterministic pytest matrix

These are synthetic, stack-conditional examples, not executed project evidence. Inspect the target repository, actual contract, tool version and permissions before applying. Keep Toolkit copies read-only when operating on another project; put reports in chat unless an output location is explicitly requested. Record unavailable evidence as NOT_VERIFIED/NOT_RUN, never PASS.

## Worked situation

A pure discount function should reject negative input and cap the discount to a documented maximum.

## Procedure and decision

Separate unit and integration fixtures, use parametrization for observable partitions, keep fixture scopes as narrow as state requires, and clear changed state. Inspect installed pytest/plugins before calling APIs.

## Observable oracle

Documented edge cases are asserted with exact values; a deliberately wrong implementation fails at least one case.

## Failure or exclusion

Do not use an autouse fixture to conceal global state changes, retry all failures or skip tests to satisfy CI.

## Handoff contract

`case ID | fixture scope | input partition | expected | observed | source revision | teardown proof`

## Illustrative example

```python
# Synthetic example: replace policy and import with project-specific contract.
import pytest

@pytest.mark.parametrize('amount,expected', [(0, 0), (100, 10)])
def test_discount_by_contract(amount, expected):
    assert discount(amount) == expected
```
