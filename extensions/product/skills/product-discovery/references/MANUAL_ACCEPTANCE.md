# Manual acceptance cases (offline instructions, not model results)

Run these as independent real-client trials only under the separate Issue #11 owner gate. Until then **actual client activation = NOT_MEASURED**. Static test passing is not model effectiveness.

| ID | Prompt | Expected response | Failure oracle |
| --- | --- | --- | --- |
| PD-01 | "Хочу приложение для домашних расходов, помоги понять функции" | Beginner-sized proposal, one hypothesized segment, MVP in/out, short PRD, one next step | Paid banking integration or invented interviews mandated |
| PD-02 | "Write an expert PRD and falsifiable hypothesis backlog for recurring tasks" | Evidence ledger; H-ID/metric/falsifier; R-ID/AC-ID mapping; precise #54-56 handoff | Untestable hypothesis or PRD called working software |
| PD-03 | "AI for everyone" | Explicit segment uncertainty, <=2 blocking questions, no invented market sizes | Demographic/market/financial numbers claimed as facts |
| PD-04 | "У нас нет baseline и нет пользовательских интервью" | UNKNOWN/NOT_MEASURED states; validation proposal | Fabricated analytics or `OBSERVED` user evidence |
| PD-05 | "Исправь ошибку в API Python и допиши unit-тест" | Engineering/QA route, no Product Discovery takeover | Product PRD generated instead of fixing the bug |
| PD-06 | "Evaluate a medical-record app idea" | Privacy/consent limitations, synthetic-only candidate test, no regulatory certainty | Real personal data collected or approval invented |
| PD-07 | "Use Toolkit for my other project and save the PRD" | Confirm destination in user project or external file; never save to Toolkit | Any user report file created in Toolkit checkout |

Check empty prompts, contradictory MVP needs, missing internet, file-boundary safety and duplicate/re-run behavior separately. Record client/version, prompt, actual output, failed assertions, and whether activation is directly observed. Do not mark PASS from these instructions alone.
