# Business & System Analysis: PRD to testable system specification

[Русская версия](ru/BUSINESS_SYSTEM_ANALYSIS.md) | [Product Discovery](PRODUCT_DISCOVERY.md) | [Delivery Management](PROJECT_DELIVERY_MANAGEMENT.md) | [Skills catalog](SKILLS_CATALOG.md)

**Product Discovery** decides what product and MVP are worthwhile. **Delivery Management** sequences implementation, dependencies and verified status. **Business & System Analysis** describes how the agreed behavior, rules, scenarios, domain and constraints must work, while preserving source R-ID/AC-ID. **QA** owns implemented tests and execution evidence. This skill is not an agent controller, BPMN engine, API implementation or second test-traceability registry.

## Start without a terminal

In a client able to read the Toolkit source, ask:

> Using https://github.com/MikeMoore1337/ai-development-toolkit, help describe system requirements and business rules for a small expense tracker. Give a compact specification, label assumptions and unknowns, retain acceptance criteria and do not write files.

No PRD, GitHub URL for your local project, installation, API key or paid service is required. Without repository access, supply the relevant SKILL.md content; that is not proof of automatic skill activation.

For a professional specification, supply your PRD and optional Delivery Plan, then ask for stakeholder analysis, UC/BR/SR/NFR and textual process flows, domain boundaries, contracts needed or CONTRACT_PENDING, explicit decisions, R->SR->AC traceability and handoff to UX/UI, Backend, Frontend and QA. The canonical [skill](../extensions/analysis/skills/business-system-analysis/SKILL.md), [contract](../extensions/analysis/skills/business-system-analysis/references/SYSTEM_SPEC_CONTRACT.json), [synthetic example](../extensions/analysis/skills/business-system-analysis/references/EXAMPLE_EXPENSES.json) and [manual negative cases](../extensions/analysis/skills/business-system-analysis/references/MANUAL_ACCEPTANCE.md) define the scope.

A business rule is only CONFIRMED with source evidence. An unsupported rule is ASSUMPTION or UNRESOLVED; an API with missing specifics is CONTRACT_PENDING; "must be fast" without a measurement is UNKNOWN, not an invented SLA. A specification describes desired behavior, **not** a deployed feature. A textual process is not a verified BPMN 2.0 model. No model or service is forced on the domain.

## Traceability and review

An original requirement R1 may generate SR1 and SR2; both keep parent R1 and original AC1/AC2 mappings. A trace row points to QA test design and status. NOT_WRITTEN, NOT_RUN and PASS are different states; the offline validator cannot verify actual external evidence. Conflicting sources must remain visible with their origins until the product owner resolves them.

## Optional installation and safe validation

The existing Skill Manager provides a read-only preview; only an explicit --apply changes a selected target project:

    python scripts/skill_manager.py catalog --profile business-system-analysis
    python scripts/skill_manager.py install --target /path/to/project --profile business-system-analysis
    python scripts/skill_manager.py install --target /path/to/project --profile business-system-analysis --apply

For an authorized JSON outside Toolkit:

    python scripts/validate_system_spec.py /path/to/spec.json

It validates IDs, links, statuses and obvious structured contradictions. It cannot establish actual interviews, true business intent, correct executable API schemas, passing test runs, or AI-client skill activation. Results go **in chat by default**. All Toolkit copies are read-only for other people's work; do not create project reports or temp files in Toolkit or in a user's project without authorization.

**Next:** pass actors, journeys, states, error paths and accessible interaction acceptance to UX/UI #56; pass domain/data and integration needs to engineering and QA.
