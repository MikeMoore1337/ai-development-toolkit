# Toolkit adaptation notes

The original Make Feature 0.3.0 is by Artemiy Miller (see LICENSE and SOURCES.md). Its source, templates, scripts and unit tests are included with a minor portable Agent Skills metadata conversion: nested `metadata.hermes.tags` is flattened into `metadata.original-agent-tags`. The personal issued license document and recipient metadata are deliberately excluded. The Toolkit owner states that the rights holder has separately authorized publication and modification; this statement was not independently verified in this build. Keep source attribution and review authorization before publishing publicly.

Activation is explicit via `--profile make-feature`; do not combine with `feature-delivery` as a competing orchestrator. Running its scripts is never implicit. This package does not grant deploy or production permissions.
