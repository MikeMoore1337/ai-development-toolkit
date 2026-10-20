# Persistence and migration checks

These are synthetic, stack-conditional examples, not executed project evidence. Inspect the target repository, actual contract, tool version and permissions before applying. Keep Toolkit copies read-only when operating on another project; put reports in chat unless an output location is explicitly requested. Record unavailable evidence as NOT_VERIFIED/NOT_RUN, never PASS.

## Worked situation

A migration adds a non-null column with a default to an existing table.

## Procedure and decision

Inspect migration and real schema version before running it. On an isolated disposable database, test empty and populated fixtures, uniqueness, nullability, referential integrity, locks, idempotent rerun and rollback path where supported.

## Observable oracle

Existing rows retain business values, defaults are applied as specified, invalid foreign keys are rejected, and the migration state is observable.

## Failure or exclusion

Do not execute arbitrary SELECT-able functions to prove read-only behavior: database functions can write. Never assume transaction rollback reverses external effects.

## Handoff contract

`schema revision | fixture | invariant | query/result | migration/rollback evidence | residual risk`
