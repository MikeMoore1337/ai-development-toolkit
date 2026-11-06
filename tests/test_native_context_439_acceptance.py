"""#439: eight synthetic, offline context-selection acceptance scenarios.

Source UTF-8 bytes are measured, not model tokens or native client activation.
No project files, user settings, external tools or model providers are modified.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "integrations/personal-mcp/adt-personal/mcp"))
sys.path.insert(0, str(ROOT / "scripts"))
import adt_mcp  # noqa: E402
import profile_metrics  # noqa: E402

# Labels are synthetic identifiers, not claims about real client execution.
SCENARIOS = (
    ("python-fix", "Исправь баг в Python-функции", "codex-feature", "implementation"),
    ("pytest-tests", "Напиши pytest-тесты для Python-функции", "qa-python", "pytest-test-design"),
    ("fastapi-endpoint", "Реализуй FastAPI endpoint с валидацией", "backend", "api-design"),
    ("react-fix", "Исправь баг в React-компоненте формы", "frontend", "component-architecture"),
    ("mcp-security", "Проведи проверку безопасности MCP-сервера", "security-engineering", "security-review"),
    ("ux-ui", "Спроектируй интерфейс приложения и покажи макет", "ui-orchestra", "ux-ui-design-orchestra"),
    ("api-docs", "Обнови документацию API и примеры ответов", "docs-technical", "documentation-maintenance"),
    ("fullstack", "Разработай fullstack-функцию с FastAPI backend и React frontend", "fullstack", "fullstack-integration"),
)


class NativeContext439Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
        cls.toolkit = adt_mcp.Toolkit(ROOT)

    def test_eight_auto_routes_preserve_task_required_skills(self):
        self.assertEqual(8, len(SCENARIOS))
        for label, task, expected_profile, required_skill in SCENARIOS:
            with self.subTest(scenario=label):
                route = self.toolkit.route(task)
                self.assertEqual(expected_profile, route["profile"])
                self.assertIn(required_skill, route["skills"])
                self.assertEqual(len(route["skills"]), len(set(route["skills"])))
                self.assertEqual([], route["unavailable"])
                self.assertEqual("NOT_OBSERVED", route["routing_decision"]["client_activation"])
                self.assertEqual("NOT_RUN", route["routing_decision"]["execution"])
                self.assertFalse(route["routing_decision"]["installation_performed"])

    def test_eight_source_byte_baselines_and_deferred_loading(self):
        report = []
        for label, task, profile, required_skill in SCENARIOS:
            with self.subTest(scenario=label):
                route = self.toolkit.route(task)
                preview = profile_metrics.preview_metadata_budget(ROOT, self.manifest, profile, 8000)
                compact = self.toolkit.prepare_task(task, existing_skills=[],
                                                    existing_roles=[], max_skills=3)
                baseline = [self.toolkit.read("skill", name, limit=32000)
                            for name in route["skills"]]
                self.assertFalse(any(item["truncated"] for item in baseline))
                self.assertFalse(any(item["truncated"] for item in compact["loaded_skills"]))
                full_bytes = sum(len(item["content"].encode("utf-8")) for item in baseline)
                loaded_bytes = sum(len(item["content"].encode("utf-8"))
                                   for item in compact["loaded_skills"])
                self.assertEqual(loaded_bytes, compact["context_load_metrics"]["skill_source_bytes"])
                self.assertLessEqual(loaded_bytes, full_bytes)
                self.assertIn(required_skill, route["skills"])
                self.assertEqual(route["skills"], compact["selected_skills"])
                self.assertTrue(preview["within_budget"])
                self.assertEqual(self.manifest["profiles"][profile],
                                 [row["skill"] for row in preview["skill_metadata"]])
                self.assertEqual(0, compact["context_load_metrics"]["reference_files_preloaded"])
                self.assertEqual("NOT_MEASURED", compact["context_load_metrics"]["model_tokens"])
                self.assertFalse(compact["installation_performed"])
                self.assertFalse(compact["project_files_changed"])
                report.append({
                    "scenario": label,
                    "route": route["profile"],
                    "full_skill_bytes": full_bytes,
                    "first_three_skill_bytes": loaded_bytes,
                    "deferred_skill_count": compact["context_load_metrics"]["deferred_skill_count"],
                    "yaml_metadata_bytes": preview["eager_metadata_bytes"],
                    "loaded": [r["name"] for r in compact["loaded_skills"]],
                    "mandatory_retained": required_skill in route["skills"],
                    "model_tokens": "NOT_MEASURED",
                })
        print("NATIVE_CONTEXT_439_MEASURED_UTF8_BYTES=" +
              json.dumps(report, ensure_ascii=False, sort_keys=True), flush=True)

    def test_unaffordable_budget_does_not_discard_required_skills(self):
        for _, _, profile, required in SCENARIOS:
            with self.subTest(profile=profile):
                preview = profile_metrics.preview_metadata_budget(ROOT, self.manifest, profile, 1)
                self.assertFalse(preview["within_budget"])
                self.assertGreater(preview["over_budget_bytes"], 0)
                self.assertIn(required, [row["skill"] for row in preview["skill_metadata"]])
                self.assertFalse(preview["automatic_pruning"])
                self.assertFalse(preview["applied"])
                self.assertEqual("NOT_MEASURED", preview["tokens"])

    def test_backend_implementation_remains_backend_with_docs_mentioned(self):
        task = "Разработай FastAPI endpoint и обнови документацию API"
        self.assertEqual("backend", self.toolkit.route(task)["profile"])

    def test_repeated_read_only_routing_and_existing_inventory(self):
        task = SCENARIOS[2][1]
        baseline = self.toolkit.route(task)
        self.assertEqual(baseline, self.toolkit.route(task))
        output = self.toolkit.prepare_task(
            task, existing_skills=["api-design"], existing_roles=[], max_skills=3)
        self.assertIn("api-design", output["already_available_skills"])
        self.assertNotIn("api-design", [item["name"] for item in output["loaded_skills"]])
        self.assertEqual("PROVIDED_BY_CLIENT_NOT_VERIFIED", output["existing_skills_status"])
        self.assertFalse(output["installation_performed"])


if __name__ == "__main__":
    unittest.main()
