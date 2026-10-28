"""Deterministic lexical-routing checks: no model calls or external dependencies."""
from __future__ import annotations

import json
import re
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import skill_routing_eval as routing


class SkillRoutingTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.catalog = {
            "code-review": "Review proposed code changes for correctness and regressions.",
            "api-testing": "Test API HTTP behavior, responses and failure cases.",
            "clear-voice": "Rewrite writing and editorial copy in a natural voice.",
        }
        self.cases = [{
            "id": "review",
            "target": "code-review",
            "positive": ["Review a code diff for correctness and regressions."],
            "negative": ["Rewrite editorial copy with a natural voice."],
        }]
        self.path = self.root / "cases.json"
        self.save()

    def save(self):
        self.path.write_text(json.dumps({"schema_version": 1, "cases": self.cases}),
                             encoding="utf-8")

    def test_cyrillic_description_tokens(self):
        self.assertIn("естественные", routing.terms("Нужны естественные русские тексты"))

    def test_positive_and_negative_separation(self):
        report = routing.evaluate(self.catalog, self.cases, top_k=1)
        self.assertEqual(2, report["prompt_count"])
        self.assertEqual(0, report["failed"], report["observations"])
        self.assertEqual("NOT_MEASURED", report["actual_skill_activation"])
        self.assertEqual("NOT_MEASURED", report["model_effectiveness"])

    def test_ru_aliases_route_without_client_claims(self):
        catalog = {
            "contract-testing": "Contract compatibility validation.",
            "seo-audit": "Search engine optimization review.",
            "code-review": "Review source code regressions.",
        }
        cases = [{
            "id": "russian-api",
            "target": "contract-testing",
            "positive": ["Контрактные тесты совместимости схемы API."],
            "negative": ["SEO аудит сайта: индексация, метатеги."],
        }]
        aliases = {
            "contract-testing": ["контрактные тесты совместимости схемы api"],
            "seo-audit": ["seo аудит сайта индексация метатеги"],
        }
        report = routing.evaluate(catalog, cases, top_k=1, aliases=aliases)
        self.assertEqual(0, report["failed"], report["observations"])
        self.assertEqual(1, report["coverage"]["languages"]["ru"]["tested_target_count"])
        self.assertEqual(2, len(report["coverage"]["uncovered_targets"]))
        self.assertEqual("NOT_OBSERVED", report["client_skill_selection"])
        self.assertEqual("NOT_TESTED", report["client_effectiveness"])

    def test_exclusion_clause_does_not_rank_sql_as_data_engineering(self):
        catalog = {
            "data-engineering": (
                "Build ETL pipelines, lineage, analytics metrics. "
                "Not for ordinary SQL queries, migrations or API fixes."
            ),
            "data-access": "Fix SQL queries, transaction boundaries and persistence code.",
        }
        docs, idf = routing.vectors(catalog)
        self.assertNotIn("sql", docs["data-engineering"])
        self.assertEqual(
            "data-access",
            routing.ranking("Fix an ordinary SQL query", catalog, docs, idf)[0],
        )

    def test_cyrillic_prefix_matching_is_scoped_to_aliases(self):
        self.assertEqual(routing.alias_stem("скриншотом"),
                         routing.alias_stem("скриншот"))
        self.assertEqual(routing.terms("скриншотом"), ["скриншотом"])
        catalog = {
            "screenshot-fidelity": "Compare reference screenshots.",
            "api-testing": "Verify API status codes.",
        }
        cases = [{
            "id": "screen",
            "target": "screenshot-fidelity",
            "positive": ["Сравни интерфейс с эталонным скриншотом."],
            "negative": ["Проверь HTTP статус API."],
        }]
        aliases = {
            "screenshot-fidelity": ["скриншот эталон визуальное сравнение интерфейса"],
            "api-testing": ["проверка http статусы api"],
        }
        report = routing.evaluate(catalog, cases, top_k=1, aliases=aliases)
        self.assertEqual(0, report["failed"], report["observations"])

    def test_explicit_english_aliases_are_supported(self):
        catalog = {
            "make-feature": "Сделай функцию из короткого запроса пользователя.",
            "product-discovery": "Discover the product problem and requirements.",
        }
        docs, idf = routing.vectors(catalog)
        prompt = "Build an entire new function from a short product request."
        self.assertEqual("product-discovery",
                         routing.ranking(prompt, catalog, docs, idf)[0])
        aliases = {
            "make-feature": ["build an entire new function from short product request"],
        }
        self.assertEqual("make-feature",
                         routing.ranking(prompt, catalog, docs, idf, aliases)[0])

    def test_aliases_unknown_skill_and_duplicates_blocked(self):
        (self.root / "aliases.json").write_text(json.dumps({
            "schema_version": 1, "aliases": {"invented": ["проверка схем"]}
        }), encoding="utf-8")
        with self.assertRaisesRegex(routing.RoutingInputError, "Unknown skill alias"):
            routing.read_aliases(self.root / "aliases.json", self.catalog)
        (self.root / "aliases.json").write_text(json.dumps({
            "schema_version": 1,
            "aliases": {"code-review": ["проверка кода", "проверка кода"]}
        }), encoding="utf-8")
        with self.assertRaisesRegex(routing.RoutingInputError, "duplicate alias"):
            routing.read_aliases(self.root / "aliases.json", self.catalog)

    def test_coverage_does_not_overstate_uncovered_skills(self):
        report = routing.evaluate(self.catalog, self.cases)
        self.assertEqual(3, report["coverage"]["catalog_total"])
        self.assertEqual(1, report["coverage"]["curated_targets"])
        self.assertEqual(["api-testing", "clear-voice"],
                         report["coverage"]["uncovered_targets"])
        self.assertEqual(0, report["coverage"]["languages"]["ru"]["tested_target_count"])
        self.assertEqual(1, report["coverage"]["languages"]["en"]["tested_target_count"])

    def test_recommend_compound_request_shows_evidence_without_execution(self):
        catalog = {
            "seo-audit": "Review SEO crawlability, indexing and metadata.",
            "contract-testing": "Check compatibility of API contracts and schemas.",
            "code-review": "Review a source code diff.",
        }
        aliases = {
            "seo-audit": ["seo аудит сайта индексация"],
            "contract-testing": ["api контракты схемы совместимость"],
        }
        manifest = {
            "profiles": {"qa-api": ["contract-testing"], "seo": ["seo-audit"]},
            "core_roles": ["reviewer"],
            "extension_packs": {"qa": {"roles": ["test-designer"]}},
        }
        result = routing.recommend(
            "SEO аудит сайта и API контракты схемы",
            catalog, aliases, manifest, top_k=2,
        )
        self.assertEqual("NOT_CALIBRATED", result["confidence"])
        self.assertEqual("NOT_OBSERVED", result["client_skill_selection"])
        self.assertEqual("NOT_TESTED", result["client_effectiveness"])
        self.assertFalse(result["installs_or_executes"])
        self.assertEqual(2, len(result["segments"]))
        self.assertTrue(result["multiple_distinct_intents"])
        first, second = result["segments"]
        self.assertEqual("seo-audit", first["candidates"][0]["skill"])
        self.assertEqual("contract-testing", second["candidates"][0]["skill"])
        self.assertTrue(first["candidates"][0]["evidence"]["alias_tokens"])
        self.assertIn("qa-api", second["candidates"][0]["candidate_profiles"])
        self.assertIn("test-designer", result["available_roles_not_automatically_selected"])

    def test_chained_prohibitions_never_promote_second_denial(self):
        catalog = {
            "seo-audit": "Audit SEO search indexing and metadata.",
            "api-testing": "Test HTTP API responses and status codes.",
            "code-review": "Review code changes for regressions.",
        }
        manifest = {"profiles": {}, "core_roles": [], "extension_packs": {}}
        for request in (
            "Skip seo-audit: don't run api-testing",
            "Не нужно seo-audit: не делай api-testing",
        ):
            with self.subTest(request=request):
                result = routing.recommend(request, catalog, {}, manifest)
                self.assertEqual("NO_POSITIVE_INTENT", result["status"])
                self.assertEqual([], result["routing_decision"]["primary_skills"])
                self.assertEqual([], result["routing_decision"]["auxiliary_skills"])
                self.assertEqual(2, len(result["routing_decision"]["excluded_clauses"]))

    def test_chained_prohibitions_keep_genuine_positive_tail(self):
        catalog = {
            "seo-audit": "Audit SEO search indexing and metadata.",
            "api-testing": "Test HTTP API responses and status codes.",
            "code-review": "Review code changes for regressions.",
        }
        result = routing.recommend(
            "Skip seo-audit: don't run api-testing: Review code changes for regressions.",
            catalog, {}, {"profiles": {}, "core_roles": [], "extension_packs": {}},
        )
        decision = result["routing_decision"]
        self.assertEqual("SUGGESTIONS_ONLY", result["status"])
        self.assertEqual("code-review", decision["primary_skills"][0])
        self.assertNotIn("seo-audit", decision["primary_skills"] + decision["auxiliary_skills"])
        self.assertNotIn("api-testing", decision["primary_skills"] + decision["auxiliary_skills"])
        self.assertEqual(["Skip seo-audit", "don't run api-testing"], decision["excluded_clauses"])

    def test_cross_client_lexical_decision_contract(self):
        catalog = {
            "seo-audit": "Audit SEO indexing and search metadata.",
            "api-testing": "Test API HTTP behavior and error responses.",
            "code-review": "Review code changes for regressions.",
        }
        manifest = {"profiles": {"qa-api": ["api-testing"]},
                    "core_roles": [], "extension_packs": {}}
        output = routing.recommend(
            "Skip seo-audit; Test API HTTP responses",
            catalog, {}, manifest, top_k=2,
        )
        decision = output["routing_decision"]
        self.assertEqual(1, decision["schema_version"])
        self.assertEqual(output["status"], decision["status"])
        self.assertEqual(["Skip seo-audit"], decision["excluded_clauses"])
        self.assertNotIn("seo-audit", decision["primary_skills"])
        self.assertIn("api-testing", decision["primary_skills"])
        self.assertIsNone(decision["primary_profile"])
        self.assertEqual("LEXICAL_SUPPORT", decision["evidence_basis"])
        self.assertEqual("NOT_OBSERVED", decision["client_activation"])
        self.assertEqual("NOT_RUN", decision["execution"])
        self.assertFalse(decision["project_files_changed"])
        self.assertFalse(decision["installation_performed"])
        empty = routing.recommend("Skip seo-audit", catalog, {}, manifest)
        self.assertEqual("NO_POSITIVE_INTENT", empty["routing_decision"]["status"])
        self.assertEqual([], empty["routing_decision"]["primary_skills"])

    def test_unselected_neighbors_require_positive_lexical_evidence(self):
        catalog = {
            "seo-audit": "Audit search indexing and metadata.",
            "seo-check": "Check SEO indexing crawlability.",
            "database-migrations": "Plan database migrations and rollback.",
            "api-testing": "Test HTTP API error responses.",
            "code-review": "Review source code diffs.",
        }
        result = routing.recommend(
            "Audit SEO indexing", catalog, {},
            {"profiles": {}, "core_roles": [], "extension_packs": {}}, top_k=1,
        )
        segment = result["segments"][0]
        self.assertEqual("seo-audit", segment["candidates"][0]["skill"])
        self.assertEqual(["seo-check"], segment["other_not_selected"])
        self.assertEqual("SUGGESTIONS_ONLY", result["status"])
        self.assertEqual("NOT_OBSERVED", result["client_skill_selection"])
        self.assertFalse(result["installs_or_executes"])

    def test_unselected_neighbors_never_emit_unsupported_alphabetical_fallback(self):
        catalog = {
            "api-testing": "Check HTTP API status codes.",
            "code-review": "Review source diffs for regressions.",
            "database-migrations": "Plan schema migrations.",
            "seo-audit": "Audit site search indexing and crawlability.",
        }
        result = routing.recommend(
            "Audit site search indexing", catalog, {},
            {"profiles": {}, "core_roles": [], "extension_packs": {}}, top_k=1,
        )
        segment = result["segments"][0]
        self.assertEqual("seo-audit", segment["candidates"][0]["skill"])
        self.assertEqual([], segment["other_not_selected"])
        weak = routing.recommend("nonsenseplaceholderxyz", catalog, {}, {}, top_k=1)
        self.assertEqual([], weak["segments"][0]["other_not_selected"])
        self.assertEqual("INSUFFICIENT_EVIDENCE", weak["status"])

    def test_recommend_weak_evidence_does_not_claim_confidence(self):
        manifest = {"profiles": {}, "core_roles": [], "extension_packs": {}}
        result = routing.recommend(
            "unknownplaceholderword", self.catalog, {}, manifest, top_k=2,
        )
        self.assertEqual("INSUFFICIENT_EVIDENCE", result["segments"][0]["status"])
        self.assertEqual([], result["segments"][0]["candidates"])
        self.assertEqual([], result["segments"][0]["other_not_selected"])
        self.assertEqual("INSUFFICIENT_EVIDENCE", result["status"])
        self.assertEqual("NOT_CALIBRATED", result["confidence"])

    def test_recommend_does_not_execute_explicitly_negated_intent(self):
        catalog = {
            "database-migrations": "Plan database migrations and rollback.",
            "accessibility-testing": "Audit keyboard focus and accessibility.",
            "seo-audit": "Check indexing and SEO.",
        }
        manifest = {"profiles": {}, "core_roles": [], "extension_packs": {}}
        report = routing.recommend(
            "Skip database migration planning; audit keyboard focus and accessibility.",
            catalog, {}, manifest, top_k=2,
        )
        self.assertEqual(["Skip database migration planning"],
                         report["excluded_negated_clauses"])
        self.assertEqual(1, len(report["segments"]))
        self.assertEqual("accessibility-testing",
                         report["segments"][0]["candidates"][0]["skill"])
        self.assertNotIn(
            "database-migrations",
            [c["skill"] for c in report["segments"][0]["candidates"]],
        )

    def test_recommend_russian_negation_separates_positive_clause(self):
        catalog = {
            "seo-audit": "SEO and search engine indexing.",
            "clear-voice": "Естественный текст интерфейса без канцеляризмов.",
        }
        manifest = {"profiles": {}, "core_roles": [], "extension_packs": {}}
        result = routing.recommend(
            "Не нужен SEO-аудит: перепиши текст интерфейса понятным языком.",
            catalog, {}, manifest, top_k=2,
        )
        self.assertEqual(["Не нужен SEO-аудит"], result["excluded_negated_clauses"])
        self.assertEqual(1, len(result["segments"]))
        self.assertEqual("clear-voice", result["segments"][0]["candidates"][0]["skill"])

    def test_natural_language_explicit_english_negations_are_not_tasks(self):
        catalog = {
            "seo-audit": "Inspect search indexing and site metadata.",
            "api-testing": "Test HTTP API response status and error handling.",
            "ux-ui-design-orchestra": "Design UX UI pages and workflows.",
        }
        manifest = {"profiles": {}, "core_roles": [], "extension_packs": {}}
        prompts = (
            ("We are not planning a new UI design; test HTTP API response status.",
             "We are not planning a new UI design"),
            ("We're not reviewing search indexing: test HTTP API error handling.",
             "We're not reviewing search indexing"),
            ("I am not designing a landing page; check HTTP API status codes.",
             "I am not designing a landing page"),
            ("No need to inspect search metadata; test HTTP API error handling.",
             "No need to inspect search metadata"),
        )
        for prompt, excluded in prompts:
            with self.subTest(prompt=prompt):
                result = routing.recommend(prompt, catalog, {}, manifest, top_k=3)
                self.assertEqual([excluded], result["excluded_negated_clauses"])
                self.assertEqual(1, len(result["segments"]))
                selected = [row["skill"] for row in result["segments"][0]["candidates"]]
                self.assertIn("api-testing", selected)
                self.assertNotIn("seo-audit", selected)
                self.assertNotIn("ux-ui-design-orchestra", selected)
                self.assertEqual("NOT_OBSERVED", result["client_skill_selection"])
                self.assertFalse(result["installs_or_executes"])

    def test_natural_language_explicit_russian_negations_are_not_tasks(self):
        catalog = {
            "seo-audit": "SEO indexing audits.",
            "api-testing": "Check HTTP API response status and errors.",
        }
        for prompt, excluded in (
            ("Не хочу SEO аудит; проверь HTTP API ответы и ошибки.",
             "Не хочу SEO аудит"),
            ("Мы не сравниваем SEO инструменты: проверь HTTP API ответы.",
             "Мы не сравниваем SEO инструменты"),
            ("Я не планирую SEO аудит: проверь HTTP API ответы.",
             "Я не планирую SEO аудит"),
        ):
            with self.subTest(prompt=prompt):
                result = routing.recommend(prompt, catalog, {}, {}, top_k=2)
                self.assertEqual([excluded], result["excluded_negated_clauses"])
                self.assertEqual(1, len(result["segments"]))
                self.assertEqual("api-testing", result["segments"][0]["candidates"][0]["skill"])
                self.assertNotIn(
                    "seo-audit",
                    [r["skill"] for r in result["segments"][0]["candidates"]],
                )

    def test_negated_gerund_only_abstains_and_uncertainty_is_not_negation(self):
        catalog = {"api-testing": "Test HTTP API status and errors."}
        negative = routing.recommend("We are not testing HTTP APIs.", catalog, {}, {}, top_k=1)
        self.assertEqual("NO_POSITIVE_INTENT", negative["status"])
        self.assertEqual([], negative["segments"])
        uncertain = routing.recommend("We are not sure if the API works.", catalog, {}, {}, top_k=1)
        self.assertNotEqual("NO_POSITIVE_INTENT", uncertain["status"])
        self.assertFalse(uncertain["installs_or_executes"])

    def test_four_clauses_do_not_erase_positive_tasks_after_exclusion(self):
        catalog = {
            "seo-audit": "Inspect SEO search metadata and ranking.",
            "api-testing": "Inspect HTTP API responses and errors.",
            "accessibility-testing": "Audit keyboard focus and navigation.",
            "database-validation": "Validate database constraints and integrity.",
        }
        report = routing.recommend(
            "Skip SEO audit; inspect HTTP API responses; "
            "audit keyboard focus; validate database constraints",
            catalog, {}, {}, top_k=2,
        )
        self.assertEqual(["Skip SEO audit"],
                         report["excluded_negated_clauses"])
        self.assertEqual("SUGGESTIONS_ONLY", report["status"])
        self.assertEqual(3, len(report["segments"]))
        self.assertEqual(
            ["api-testing", "accessibility-testing", "database-validation"],
            [segment["candidates"][0]["skill"] for segment in report["segments"]],
        )
        self.assertNotIn(
            "seo-audit",
            [c["skill"] for s in report["segments"] for c in s["candidates"]],
        )
        self.assertFalse(report["installs_or_executes"])

    def test_explicitly_excluded_skill_is_not_a_secondary_suggestion(self):
        catalog = {
            "seo-audit": "Audit search crawlability and metadata.",
            "api-testing": "Audit HTTP API responses and failures.",
        }
        report = routing.recommend(
            "Don't do SEO audit; audit HTTP API responses",
            catalog, {}, {}, top_k=2,
        )
        self.assertEqual(["Don't do SEO audit"], report["excluded_negated_clauses"])
        self.assertEqual("api-testing",
                         report["segments"][0]["candidates"][0]["skill"])
        self.assertNotIn(
            "seo-audit",
            [c["skill"] for s in report["segments"] for c in s["candidates"]]
            + [n for s in report["segments"] for n in s["other_not_selected"]],
        )

    def test_four_positive_clauses_keep_three_bounded_segments(self):
        catalog = {
            "api-testing": "Inspect HTTP API responses and errors.",
            "accessibility-testing": "Audit keyboard focus and navigation.",
            "database-validation": "Validate database constraints and integrity.",
            "code-review": "Review source code diffs and changes.",
        }
        report = routing.recommend(
            "inspect HTTP API responses; audit keyboard focus; "
            "validate database constraints; review source code diffs",
            catalog, {}, {}, top_k=3,
        )
        self.assertEqual(3, len(report["segments"]))
        self.assertEqual("api-testing", report["segments"][0]["candidates"][0]["skill"])
        self.assertEqual("accessibility-testing",
                         report["segments"][1]["candidates"][0]["skill"])
        tail = {item["skill"] for item in report["segments"][2]["candidates"]}
        self.assertIn("database-validation", tail)
        self.assertIn("code-review", tail)
        self.assertEqual([], report["excluded_negated_clauses"])

    def test_selection_roles_are_stable_and_do_not_claim_activation(self):
        catalog = {
            "seo-audit": "Audit SEO indexing and crawlability.",
            "seo-check": "Check SEO indexing and metadata.",
            "api-testing": "Test HTTP API responses and status codes.",
        }
        report = routing.recommend(
            "Audit SEO indexing and metadata",
            catalog, {}, {}, top_k=3,
        )
        roles = [candidate["selection_role"]
                 for candidate in report["segments"][0]["candidates"]]
        self.assertEqual(["PRIMARY", "AUXILIARY"], roles)
        self.assertEqual("NOT_OBSERVED", report["client_skill_selection"])
        self.assertEqual("NOT_CALIBRATED", report["confidence"])

    def test_diagnostic_roles_and_manual_label_proxies(self):
        catalog = {
            "seo-audit": "Audit SEO indexing and crawlability.",
            "seo-check": "Check SEO indexing and metadata.",
            "api-testing": "Test HTTP API responses and status codes.",
            "database-validation": "Validate database schema constraints.",
        }
        cases = [
            {"id": "hit-primary", "kind": "single",
             "query": "Audit SEO indexing", "expected": ["seo-audit"]},
            {"id": "hit-auxiliary", "kind": "single",
             "query": "Audit SEO indexing", "expected": ["seo-check"]},
            {"id": "miss", "kind": "single",
             "query": "Audit SEO indexing", "expected": ["database-validation"]},
            {"id": "abstain", "kind": "single",
             "query": "nomatchzzzzzzz", "expected": ["api-testing"]},
            {"id": "forbidden", "kind": "negative",
             "query": "Audit SEO indexing", "expected": ["seo-check"],
             "avoid_top1": ["seo-audit"]},
        ]
        report = routing.evaluate_holdout(catalog, {}, {}, cases, top_k=3)
        observed = {row["id"]: row for row in report["observations"]}
        self.assertTrue(observed["hit-primary"]["primary_gold_match"])
        self.assertTrue(observed["hit-auxiliary"]["auxiliary_only_gold_match"])
        self.assertFalse(observed["hit-auxiliary"]["primary_gold_match"])
        self.assertTrue(observed["miss"]["non_gold_primary_choices"])
        self.assertTrue(observed["forbidden"]["forbidden_supported_primary"])
        self.assertTrue(observed["abstain"]["abstained"])
        stats = report["label_diagnostics"]
        self.assertEqual(5, sum(stats[key] for key in (
            "primary_gold_match_cases", "auxiliary_only_gold_match_cases",
            "no_gold_match_cases"
        )))
        self.assertEqual(1, stats["forbidden_supported_primary_cases"])
        self.assertEqual(2, stats["no_gold_match_cases"])
        self.assertEqual(5, report["count"])
        self.assertEqual("NOT_TESTED", report["client_effectiveness"])

    def test_recommend_negative_only_abstains(self):
        catalog = {"database-migrations": "Plan migration rollback.",
                   "api-testing": "Test API responses."}
        result = routing.recommend(
            "Skip database migration planning.", catalog, {}, {},
            top_k=2,
        )
        self.assertEqual("NO_POSITIVE_INTENT", result["status"])
        self.assertEqual([], result["segments"])
        self.assertFalse(result["installs_or_executes"])

    def test_recommend_recovers_supported_skill_beyond_weak_raw_top_k(self):
        # Three one-token description matches outrank the two-token match
        # diluted by nonmatching text; none of them passes the evidence gate.
        noisy = " ".join(f"noise{i}" for i in range(240))
        catalog = {
            "weak-a": "alpha",
            "weak-b": "alpha",
            "weak-c": "alpha",
            "strong-candidate": f"alpha beta {noisy}",
            "supported-alternative": f"alpha beta gamma {noisy}",
        }
        docs, idf = routing.vectors(catalog)
        order = routing.ranking("alpha beta", catalog, docs, idf)
        self.assertEqual(["weak-a", "weak-b", "weak-c"], order[:3])
        advice = routing.recommend("alpha beta", catalog, {}, {}, top_k=1)
        row = advice["segments"][0]
        self.assertEqual("SUGGESTIONS_ONLY", advice["status"])
        self.assertEqual("PRESENT", row["candidates"][0]["lexical_support"])
        self.assertGreater(row["candidates"][0]["rank"], 1)
        self.assertNotIn(row["candidates"][0]["skill"], row["other_not_selected"])
        self.assertTrue(set(row["other_not_selected"]).isdisjoint(
            {item["skill"] for item in row["candidates"]}))
        self.assertFalse(advice["installs_or_executes"])
        wider = routing.recommend("alpha beta", catalog, {}, {}, top_k=3)
        selections = [item["skill"] for item in wider["segments"][0]["candidates"]]
        self.assertEqual(2, len(selections))
        self.assertTrue(all(item["rank"] > 3 for item in
                            wider["segments"][0]["candidates"]))
        self.assertTrue(set(selections).isdisjoint(
            wider["segments"][0]["other_not_selected"]))

    def test_recommend_never_invents_supported_skill_if_all_weak(self):
        catalog = {"a": "alpha", "b": "alpha", "c": "alpha"}
        advice = routing.recommend("alpha beta", catalog, {}, {}, top_k=2)
        self.assertEqual("INSUFFICIENT_EVIDENCE", advice["status"])
        self.assertEqual([], advice["segments"][0]["candidates"])
        self.assertEqual([], advice["segments"][0]["other_not_selected"])
        self.assertEqual("NOT_OBSERVED", advice["client_skill_selection"])
        self.assertEqual("NOT_TESTED", advice["client_effectiveness"])

    def test_recommend_invalid_input_fails_closed(self):
        with self.assertRaises(routing.RoutingInputError):
            routing.recommend(" ", self.catalog, {}, {}, top_k=1)
        with self.assertRaises(routing.RoutingInputError):
            routing.recommend("valid request", self.catalog, {}, {}, top_k=8)

    def test_holdout_reports_unseen_failures_without_fake_confidence(self):
        catalog = {
            "seo-audit": "Search page indexing and crawl errors.",
            "api-testing": "Verify HTTP API response status and errors.",
            "security-testing": "Test authorization and session security.",
        }
        aliases = {}
        manifest = {"profiles": {}, "core_roles": [], "extension_packs": {}}
        heldout = [
            {"id": "single", "kind": "single",
             "query": "Check HTTP API responses.",
             "expected": ["api-testing"]},
            {"id": "compound", "kind": "compound",
             "query": "Check API responses and test session security.",
             "expected": ["api-testing", "security-testing"]},
            {"id": "negative", "kind": "negative",
             "query": "Review page indexing, no HTTP testing.",
             "expected": ["seo-audit"], "avoid_top1": ["api-testing"]},
            {"id": "miss", "kind": "single",
             "query": "Check HTTP API responses.", "expected": ["seo-audit"]},
        ]
        report = routing.evaluate_holdout(catalog, aliases, manifest, heldout, top_k=2)
        self.assertEqual(4, report["count"])
        self.assertEqual("NOT_CALIBRATED", report["confidence"])
        self.assertFalse(report["strict_gate"])
        self.assertEqual("NOT_OBSERVED", report["client_skill_selection"])
        self.assertEqual(1, report["by_kind"]["compound"]["cases"])
        self.assertEqual(1, report["by_kind"]["negative"]["cases"])
        self.assertGreaterEqual(report["failed"], 1)
        self.assertFalse(report["observations"][-1]["pass"])

    def test_holdout_reports_alphabetical_fallback_separately(self):
        catalog = {
            "api-testing": "Validate HTTP status responses.",
            "seo-audit": "Review search indexing and metadata.",
        }
        cases = [{"id": "unknown", "kind": "single",
                  "query": "zzzzqwertyunknown", "expected": ["api-testing"]}]
        report = routing.evaluate_holdout(catalog, {}, {}, cases, top_k=1)
        self.assertEqual(1, report["passed"])  # Legacy alphabetical top-1.
        self.assertEqual(0, report["supported_passed"])
        self.assertEqual(1, report["abstained"])
        self.assertEqual(1, report["unverified_fallback"])
        self.assertEqual(1, report["by_kind"]["single"]["unverified_fallback"])
        self.assertEqual(1, report["by_language"]["en"]["abstained"])
        self.assertTrue(report["observations"][0]["unverified_fallback"])
        self.assertEqual([], report["observations"][0]["supported_candidates"])
        self.assertEqual("NOT_CALIBRATED", report["confidence"])

    def test_holdout_supported_negative_choice_is_distinct_from_legacy(self):
        catalog = {
            "database-migrations": "Plan database migrations and rollback.",
            "accessibility-testing": "Audit keyboard focus and accessibility.",
        }
        cases = [{"id": "negation", "kind": "negative",
                  "query": "Skip database migration planning; audit keyboard focus and accessibility.",
                  "expected": ["accessibility-testing"],
                  "avoid_top1": ["database-migrations"]}]
        report = routing.evaluate_holdout(catalog, {}, {}, cases, top_k=2)
        row = report["observations"][0]
        self.assertEqual(["accessibility-testing"], row["supported_candidates"])
        self.assertTrue(row["supported_negative_control_ok"])
        self.assertTrue(row["supported_pass"])
        self.assertFalse(row["abstained"])
        self.assertEqual(1, report["by_kind"]["negative"]["supported_passed"])

    def test_holdout_refuses_unbounded_top_k_consistently(self):
        catalog = {"code-review": "Review code changes."}
        cases = [{"id": "one", "kind": "single", "query": "Review code",
                  "expected": ["code-review"]}]
        with self.assertRaisesRegex(routing.RoutingInputError, "top_k"):
            routing.evaluate_holdout(catalog, {}, {}, cases, top_k=2)

    def test_holdout_schema_rejects_unknown_targets_and_forbidden_overlap(self):
        test_file = self.root / "holdout.json"
        record = {
            "schema_version": 1, "description": "Synthetic test data",
            "cases": [{"id": "h", "kind": "single", "query": "review code",
                       "expected": ["invented"]}],
        }
        test_file.write_text(json.dumps(record), encoding="utf-8")
        with self.assertRaisesRegex(routing.RoutingInputError, "Unknown or duplicate expected"):
            routing.load_holdout(test_file, self.catalog)
        record["cases"][0] = {
            "id": "h", "kind": "negative", "query": "review code",
            "expected": ["code-review"], "avoid_top1": ["code-review"],
        }
        test_file.write_text(json.dumps(record), encoding="utf-8")
        with self.assertRaisesRegex(routing.RoutingInputError, "overlap"):
            routing.load_holdout(test_file, self.catalog)

    def test_new_untuned_bilingual_probe_is_disjoint_and_diagnostic_only(self):
        catalog = routing.read_catalog(ROOT)
        new = routing.load_holdout(
            ROOT / "fixtures/skill_routing_untuned_20261024.json", catalog)
        self.assertEqual(16, len(new))
        self.assertEqual(16, len({case["query"].casefold() for case in new}))
        self.assertEqual({"single": 8, "compound": 4, "negative": 4},
                         {kind: sum(case["kind"] == kind for case in new)
                          for kind in ("single", "compound", "negative")})
        self.assertEqual(8, sum(case["id"].startswith("untuned-ru-") for case in new))
        self.assertEqual(8, sum(case["id"].startswith("untuned-en-") for case in new))
        prior_queries = set()
        for name in ("skill_routing_holdout.json",
                     "skill_routing_exploratory_20261023.json",
                     "skill_routing_release_probes_20261023.json"):
            for case in routing.load_holdout(ROOT / "fixtures" / name, catalog):
                prior_queries.add(case["query"].strip().casefold())
        curated = routing.load_cases(
            ROOT / "fixtures/skill_routing_cases.json", catalog)
        for case in curated:
            prior_queries.update(q.strip().casefold()
                                 for key in ("positive", "negative")
                                 for q in case[key])
        self.assertTrue({case["query"].strip().casefold()
                         for case in new}.isdisjoint(prior_queries))
        manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
        aliases = routing.read_aliases(
            ROOT / "fixtures/skill_routing_aliases.json", catalog)
        report = routing.evaluate_holdout(catalog, aliases, manifest, new)
        self.assertEqual(16, report["count"])
        self.assertEqual(16, report["supported_passed"] + report["supported_failed"])
        self.assertFalse(report["strict_gate"])
        self.assertEqual("NOT_CALIBRATED", report["confidence"])
        self.assertEqual("NOT_OBSERVED", report["client_skill_selection"])
        self.assertEqual("NOT_TESTED", report["client_effectiveness"])
        self.assertEqual(4, report["by_kind"]["negative"]["cases"])
        self.assertEqual(8, report["by_language"]["ru"]["cases"])
        self.assertEqual(8, report["by_language"]["en"]["cases"])

    def test_holdout_fixture_not_copied_from_curated_routing_cases(self):
        catalog = routing.read_catalog(ROOT)
        curated = routing.load_cases(ROOT / "fixtures/skill_routing_cases.json", catalog)
        holdout = routing.load_holdout(ROOT / "fixtures/skill_routing_holdout.json", catalog)
        source_texts = {item.strip().casefold() for case in curated
                        for key in ("positive", "negative") for item in case[key]}
        queries = [case["query"].strip().casefold() for case in holdout]
        self.assertEqual(len(queries), len(set(queries)))
        self.assertTrue(set(queries).isdisjoint(source_texts))
        self.assertGreaterEqual(len(holdout), 30)
        self.assertEqual({"single", "compound", "negative"},
                         {case["kind"] for case in holdout})
        aliases = routing.read_aliases(ROOT / "fixtures/skill_routing_aliases.json", catalog)
        manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
        report = routing.evaluate_holdout(catalog, aliases, manifest, holdout)
        self.assertEqual(len(holdout), report["count"])
        self.assertEqual(report["count"], report["passed"] + report["failed"])
        self.assertEqual(report["count"], report["supported_passed"] + report["supported_failed"])
        self.assertEqual(report["count"], sum(
            report["by_language"][language]["cases"] for language in ("ru", "en")))
        self.assertEqual(report["count"], sum(
            report["by_kind"][kind]["cases"] for kind in ("single", "compound", "negative")))
        self.assertEqual("untuned_holdout_diagnostic", report["classification"])

    def test_deterministic_results(self):
        first = routing.evaluate(self.catalog, self.cases)
        self.assertEqual(first, routing.evaluate(self.catalog, self.cases))

    def test_wrong_routing_is_detected(self):
        self.cases[0]["positive"] = ["Rewrite editorial copy in a natural voice."]
        report = routing.evaluate(self.catalog, self.cases, top_k=1)
        self.assertEqual(1, report["failed"])
        self.assertEqual(False, report["observations"][0]["pass"])

    def test_unknown_skill_fails_closed(self):
        self.cases[0]["target"] = "invented-skill"
        self.save()
        with self.assertRaisesRegex(routing.RoutingInputError, "Unlisted skill"):
            routing.load_cases(self.path, self.catalog)

    def test_duplicate_case_id_fails_closed(self):
        self.cases.append(self.cases[0].copy())
        self.save()
        with self.assertRaisesRegex(routing.RoutingInputError, "duplicated"):
            routing.load_cases(self.path, self.catalog)

    def test_invalid_prompt_rejected(self):
        self.cases[0]["negative"] = [""]
        self.save()
        with self.assertRaisesRegex(routing.RoutingInputError, "Invalid prompt"):
            routing.load_cases(self.path, self.catalog)

    def test_catalog_is_manifest_driven(self):
        from_manifest = routing.read_catalog(ROOT)
        self.assertEqual(85, len(from_manifest))
        self.assertIn("feature-delivery", from_manifest)
        self.assertIn("make-feature", from_manifest)
        self.assertIn("performance-load-testing", from_manifest)

    def test_real_fixture_is_valid_and_read_only(self):
        catalog = routing.read_catalog(ROOT)
        cases = routing.load_cases(ROOT / "fixtures/skill_routing_cases.json", catalog)
        aliases = routing.read_aliases(ROOT / "fixtures/skill_routing_aliases.json", catalog)
        report = routing.evaluate(catalog, cases, aliases=aliases)
        self.assertGreaterEqual(len(cases), 12)
        self.assertEqual(85, report["coverage"]["catalog_total"])
        # Full RU/EN fixture inventory is not proof of real client activation.
        self.assertEqual(len(catalog), report["coverage"]["curated_targets"])
        self.assertEqual([], report["coverage"]["uncovered_targets"])
        for language in ("ru", "en"):
            self.assertEqual(len(catalog), report["coverage"]["languages"][language]["tested_target_count"])
            self.assertGreaterEqual(report["coverage"]["languages"][language]["positive_prompts"], len(catalog))
            self.assertGreaterEqual(report["coverage"]["languages"][language]["negative_prompts"], len(catalog))
        self.assertEqual("NOT_OBSERVED", report["client_skill_selection"])
        self.assertEqual("NOT_TESTED", report["client_effectiveness"])
        self.assertTrue({"qa-failure-triage-versus-generic-tests",
                         "qa-test-oracle-review-versus-code-review"} <=
                        {case["id"] for case in cases})
        self.assertEqual(len(cases) * 4, report["prompt_count"])
        self.assertEqual("offline_source_diagnostic", report["classification"])

    def test_bilingual_qa_behavior_check_ids(self):
        """Manual cases are parallel in EN/RU; do not mistake them for executed trials."""
        expected_routes = {f"QA-R{i:02d}" for i in range(1, 15)}
        expected_negative = {f"QA-N{i:02d}" for i in range(1, 8)}
        ids = []
        for path in ("docs/SKILL_ROUTING_EVALS.md",
                     "docs/ru/SKILL_ROUTING_EVALS.md"):
            content = (ROOT / path).read_text(encoding="utf-8")
            route_ids = re.findall(r"^\| (QA-R\d{2}) \|", content, re.MULTILINE)
            negative_ids = re.findall(r"^\| (QA-N\d{2}) \|", content, re.MULTILINE)
            self.assertEqual(expected_routes, set(route_ids), path)
            self.assertEqual(expected_negative, set(negative_ids), path)
            self.assertEqual(len(route_ids), len(expected_routes), path)
            self.assertEqual(len(negative_ids), len(expected_negative), path)
            ids.append((route_ids, negative_ids))
        self.assertEqual(ids[0], ids[1])

    def test_qa_advanced_methods_have_bilingual_guidance(self):
        for path in ("docs/CURATED_SKILL_PACKS.md",
                     "docs/ru/CURATED_SKILL_PACKS.md"):
            content = (ROOT / path).read_text(encoding="utf-8")
            for technique in ("Property-based", "Metamorphic",
                              "Model-based", "Mutation"):
                self.assertIn(technique, content, path)
            self.assertIn("ROLLBACK", content, path)
            self.assertIn("test-management", content, path)

    def test_cli_strict_in_synced_checkout(self):
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "skill_routing_eval.py"), "--strict"],
            check=False, capture_output=True, text=True, encoding="utf-8", timeout=20,
        )
        self.assertEqual(0, proc.returncode, proc.stderr + proc.stdout[-4000:])


if __name__ == "__main__":
    unittest.main()
