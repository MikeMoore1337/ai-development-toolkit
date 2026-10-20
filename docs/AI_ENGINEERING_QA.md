# AI Engineering & QA (Issue #57)

[Русская версия](ru/AI_ENGINEERING_QA.md) | [Optional skill](../extensions/ai/skills/ai-engineering-qa/SKILL.md)

LLM evaluation checks specified observable behavior against independent reference criteria, rather than trusting one plausible answer. A versioned dataset with stable case IDs and SHA256 makes failures reproducible. Prompt regression protects required fields, constraints, errors and safety behavior when instructions change. RAG means retrieving evidence for an answer: retrieval relevance is **different** from grounding individual claims in passages. Tool-use testing separately checks arguments, scopes, write permissions, approvals and ambiguous retries.

## First try (no paid API)

Beginner request: "I made an AI assistant. Help me define six tests, including missing facts and fake references, with expected results and explain what I can prove offline."

Expert request: "Create a versioned LLM/RAG/tool-use evaluation contract with gold retrieval labels, independent oracles, prompt versions, authorization negatives and baseline/candidate comparability."

Optional profile: ai-engineering-qa. Preview before installing; never modify a user's project without consent. In a Toolkit development checkout run:

~~~sh
python scripts/validate_ai_contracts.py
python -m unittest tests.test_ai_contracts -v
python scripts/skill_routing_eval.py --strict
~~~

All fixtures are invented. Offline checks can validate dataset hashes, missing IDs, prompt field invariants, retrieval ranking calculations, citation membership, tool arguments, permissions, unsafe retries and evidence status. They cannot measure a live AI client's activation, a real retriever's relevance, semantic grounding, model quality, actual latency, tokens or provider cost. Actual provider cost is UNKNOWN without billing and rate evidence. The Issue #11 owner zero-spend execution lock remains in force; no alternative model runner exists.

Use [Evaluation](../extensions/ai/skills/ai-engineering-qa/references/EVALUATION.md), [Prompts](../extensions/ai/skills/ai-engineering-qa/references/PROMPTS.md), [RAG](../extensions/ai/skills/ai-engineering-qa/references/RAG.md), and [Tool-use](../extensions/ai/skills/ai-engineering-qa/references/TOOLS.md). Reuse existing QA contract-testing, test-analysis-design, security-boundaries and agent_eval_review.py. User-generated artifacts stay in chat or a destination explicitly authorized by the user, **never** in Toolkit sources. Do not copy private user data or run provider APIs.

Technical evidence boundaries: offline oracle PASS is not model effectiveness; citation membership PASS is not semantic grounding; tool contract PASS is not actual authorized execution. Effectiveness and real-client activation are NOT_MEASURED.

## Reuse-first decision record

| Concern | Existing foundation | Issue #57 result |
| --- | --- | --- |
| Paired skill evaluation | Issue #11 skill_eval.py, agent_eval_runner.py | REUSE, execution remains locked |
| Evidence review | agent_eval_review.py | REUSE, no second review runner |
| Offline fixtures | agent_eval_fixtures.py, agent_eval_offline_smoke.py | REUSE approach, NEW synthetic AI cases |
| Prompt regression | QA test-analysis-design, contract-testing | REFINE structured versioned invariants |
| Dataset versioning | Issue #11 fixture identifiers | NEW portable dataset SHA and metadata |
| RAG retrieval quality | research-verification | NEW labelled offline metrics |
| Grounded answering | research-verification | REFINE citation checks; semantics NOT_MEASURED |
| Tool-call contracts | api-design, contract-testing | REFINE permission and retry contracts |
| Tool authorization | security-boundaries | REUSE with synthetic negative tests |
| Hallucination handling | research-verification | REFINE missing-evidence checks |
| Cost/token reporting | Issue #11 evidence reports | REUSE evidence discipline: UNKNOWN/NOT_MEASURED |

One optional AI skill, no new controller, retriever, runner, model judge or mandatory dependency.
