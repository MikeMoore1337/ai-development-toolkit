# Optional editorial worker adapter

`EDITORIAL_STYLE_PROMPT.txt` is a short style layer for a generic text-processing worker. It does not install tools, call services or deploy anything.

Before use, verify the host application's exact input/output schema, factual grounding, source restrictions, permissions and approval gates. Benchmark against unchanged input on real authorized and synthetic examples; roll back on regressions.
