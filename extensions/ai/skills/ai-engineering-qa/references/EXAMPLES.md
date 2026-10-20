# Three synthetic offline examples

- LLM feature: fixtures/ai/feature.json - fictional text extraction, missing fields, inconsistent status and untrusted instruction. Schema predicates operate on static observations, not a model.
- RAG: fixtures/ai/rag.json - fictional help center, ranked chunks, relevance labels, no answer, conflicting revisions, fake citation and embedded prompt injection. Retrieval metrics use supplied rankings; semantic entailment NOT_MEASURED.
- Tool use: fixtures/ai/tool.json - imaginary notes tool with read and write capabilities; read-only scope, unauthorized write, unknown operation, duplicate, timeout/unsafe retry, missing approval, cross-user scope, injection in note contents as inert data.

python scripts/validate_ai_contracts.py

For each synthetic fixture the expected negative verdict is FAIL and must be *detected* by the contract; the whole test suite can PASS because defect detection worked. This is not model effectiveness, safe autonomous execution, semantic grounding or a real measured cost.
