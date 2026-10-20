# Prompt design and regression

Sequence: task -> context -> constraints -> output schema -> acceptance criteria -> negative cases -> version -> regression. If application supports trusted system/developer roles, put application policy there; treat user text, retrieval chunks and tool returns as untrusted data. Never assume all clients have the same role order.

Track each meaningful version change: reason, expected observable behavior, modified restrictions, input/output compatibility, new tests, risks and rollback. Version a prompt independently from model/retrieval/tool/dataset revisions.

Offline regression cases should assert structured schema, required fields/types, invariants, forbidden fields/side effects, missing-data behavior and explicit uncertainty. Include fabricated sources, fake citations, secrets, prompt injection, tool errors and unauthorized instructions. Do not compare natural language outputs by full-string equality or reward verbose prompts.

Run known-good and known-bad synthetic observations through the independent predicates. These prove the predicate distinguishes a specific defect, not that an LLM obeys the prompt. For actual model regression, use the existing explicitly authorized evaluation route and real recorded observations. No hidden live calls.
