# QA source portability decision

[Русская версия](ru/QA_PORTABILITY.md)

The owner reports the supplied `.agents(1).zip` was created for their work project. Its engineering focus spans 27 named skills and 11 QA-related roles. The public adaptation tracks all 27 in `extensions/qa/SOURCE_MAPPING.md` and has 11 reference role files.

The original `AGENTS.md` and domain-specific link paths were excluded: they refer to a specific Python version, Jira / Test IT, Graphify mandates and missing project documents. Those are valid local constraints only when a target repository explicitly requires them. The public QA skills are opt-in, tool-agnostic when possible and include an optional graph tool adapter.

The author's statement is recorded for provenance but employer IP terms are not independently verified. No private original archive, usernames, internal issue trackers, personalized licenses or CI secrets are distributed.

Run full tests and evaluate actual false-positive tests, breakages caught, task duration, regression quality and context cost on three independent repositories with different architectures and QA constraints before claiming effectiveness gains.
