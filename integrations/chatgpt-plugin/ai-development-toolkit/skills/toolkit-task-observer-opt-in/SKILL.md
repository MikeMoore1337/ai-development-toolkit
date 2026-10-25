---
name: toolkit-task-observer-opt-in
description: Explicitly requested, sanitized task/skill improvement observations; no automatic recording, file watching, scheduling or paid API.
---

# Task Observer — privacy-preserving ChatGPT adapter (opt-in)

**Origin:** Eoghan Henn, *One Skill to Rule Them All / Task Observer*,
`rebelytics/one-skill-to-rule-them-all`, mirrored at
`iamneilroberts/claude-skills@947953f2a0664ac95996a4c7b35794a7cc8fc93a`
(`skills/task-observer`). Original licensed **CC BY 4.0**:
https://creativecommons.org/licenses/by/4.0/ .
**Changes:** original per-session always-on observer, persistent file log,
weekly automatic review and automatic skill updates are DISABLED here. This
is a short adapted workflow, not an unchanged original copy or resident agent.
Full license and attribution: [UPSTREAM.md](references/UPSTREAM.md).

## Trigger and scope

Activate **only** when the user asks to track skill gaps, reflect on repeated
workflow errors, review observations, or improve a Toolkit skill. Merely
performing engineering work must NOT enable observation.

Use current user-provided or explicitly authorized **public** evidence, not
private conversation history, hidden chat logs, system prompts or other
connected content without permission. No background service, no cron, no
Claude hooks, no user-wide automatic activation, and no paid AI provider.

## Method adapted from original Task Observer

1. Identify actionable friction: wrong skill selection, missing evidence,
   repeated step, failed regression, policy mismatch, or unclear documentation.
2. Check against Toolkit's current skill catalog, existing Issues, and
   `scripts/skill_observation_review.py` to avoid duplicate functionality.
3. Assemble **only a sanitized structured packet** accepted by that existing
   validator: `schema_version=1`, `observations` with `observation_id`,
   `skill_id`, `category`, `source_url` (canonical, public GitHub
   issue/PR/check/run/commit URL). Do not copy raw transcripts, user prompts,
   private files, API keys or full tool outputs.
4. Use Toolkit's read-only validator, when a safe execution tool is
   authorized and present, to reject malformed/deduplicated records. The
   result is **MANUAL_REVIEW_REQUIRED**, never automatically VERIFIED.
5. Suggest the smallest specific change and existing test, naming its
   expected measurable benefit. Get approval before writing Issues, editing
   Skills or scheduling any recurring review. Preserve prior user decisions.

## Report

`Observation ID | skill ID | sanitized public reference | evidence status | proposed improvement`

If no authorized observable source exists, do not create a packet or
invent facts; report `NOT_OBSERVED`. Make no persistence claims without
a completed explicit write action. This skill contains no standalone
observer daemon or permission to self-modify.
