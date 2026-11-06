"""#299: reproducible source-byte and safety regression audit, no AI clients."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import profile_context_audit as audit


class ProfileContextAuditTests(unittest.TestCase):
    def test_first_three_vs_five_actual_returned_text(self):
        result = audit.inspect(ROOT)
        self.assertEqual(5, len(result["examples"]))
        self.assertEqual("NOT_MEASURED", result["model_tokens"])
        self.assertEqual("NOT_RUN", result["runtime_invocation"])
        self.assertEqual("NOT_MEASURED", result["client_benefit"])
        self.assertFalse(result["project_files_changed"])
        self.assertTrue(result["same_role_and_safety_instructions"])
        self.assertEqual("NOT_PROVIDED", result["missing_inventory"])
        self.assertEqual(0, result["preloaded_references"])
        for row in result["examples"]:
            with self.subTest(profile=row["profile"]):
                self.assertEqual("NOT_MEASURED", row["model_tokens_saved"])
                self.assertEqual("NOT_MEASURED", row["quality_effect"])
                self.assertGreater(row["compact_source_bytes"], 0)
                self.assertGreaterEqual(row["extended_source_bytes"],
                                        row["compact_source_bytes"])
                self.assertEqual(row["difference_returned_source_bytes"],
                                 row["extended_source_bytes"] - row["compact_source_bytes"])
                self.assertEqual(row["first_three_loaded"],
                                 row["first_five_loaded"][:len(row["first_three_loaded"])])
                self.assertTrue(row["same_role_and_policies"])
                self.assertFalse(set(row["first_three_loaded"]) &
                                 set(row["deferred_after_three"]))
        self.assertEqual("create-design",
                         next(x for x in result["examples"]
                              if x["profile"] == "ui-orchestra")["visual_phase"])

    def test_explicit_ui_orchestra_cannot_bypass_visual_acceptance(self):
        tk = audit.adt_mcp.Toolkit(ROOT)
        self.assertEqual(
            "create-design",
            tk.route("Создай сайт с отличающимся дизайном", profile="ui-orchestra")["visual_phase"],
        )
        self.assertEqual(
            "create-design",
            tk.route("Создай сайт с отличающимся дизайном")["visual_phase"],
        )

    def test_existing_client_skill_is_not_loaded_again(self):
        tk = audit.adt_mcp.Toolkit(ROOT)
        result = tk.prepare_task(
            "Build a compatible REST API endpoint", profile="backend",
            existing_skills=["api-design"], existing_roles=[], max_skills=5,
        )
        self.assertIn("api-design", result["already_available_skills"])
        self.assertNotIn("api-design", [x["name"] for x in result["loaded_skills"]])
        self.assertFalse(result["installation_performed"])

    def test_controller_incompatibility_stays_single(self):
        tk = audit.adt_mcp.Toolkit(ROOT)
        tk.profiles = dict(tk.profiles)
        tk.profiles["controller-collision-fixture"] = [
            "feature-delivery", "adaptive-delivery", "make-feature", "qa-strategy"]
        selected = tk.route("Implement a new feature", profile="controller-collision-fixture")
        chosen = audit.adt_mcp.CONFLICT_GROUP & set(selected["skills"])
        self.assertEqual(1, len(chosen))
        self.assertIn("qa-strategy", selected["skills"])

    def test_safety_instruction_removal_fails_closed(self):
        unmodified = audit.adt_mcp.Toolkit.prepare_task

        for marker in ("Never write Toolkit skills",
                       "Install missing task-required skills and tools through the host",
                       "Honor explicit no-install/reference-only requests"):
            with self.subTest(marker=marker):
                def tampered(self, *args, **kwargs):
                    response = unmodified(self, *args, **kwargs)
                    if kwargs.get("profile") == "backend" and kwargs.get("max_skills") == 3:
                        response["instructions"] = [
                            s for s in response["instructions"] if marker not in s
                        ]
                    return response

                with patch.object(audit.adt_mcp.Toolkit, "prepare_task", tampered):
                    with self.assertRaisesRegex(audit.AuditError, "Mandatory instructions"):
                        audit.inspect(ROOT)

    def test_loaded_skill_mutation_fails_closed(self):
        unmodified = audit.adt_mcp.Toolkit.prepare_task

        def tampered(self, *args, **kwargs):
            response = unmodified(self, *args, **kwargs)
            if kwargs.get("profile") == "backend" and kwargs.get("max_skills") == 3:
                response["loaded_skills"][0]["truncated"] = True
            return response

        with patch.object(audit.adt_mcp.Toolkit, "prepare_task", tampered):
            with self.assertRaisesRegex(audit.AuditError, "truncated"):
                audit.inspect(ROOT)

    def test_offline_cli_never_claims_tokens_or_quality(self):
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts/profile_context_audit.py")],
            capture_output=True, text=True, encoding="utf-8", timeout=45,
            check=False,
        )
        self.assertEqual(0, proc.returncode, proc.stderr)
        result = json.loads(proc.stdout)
        self.assertEqual(5, len(result["examples"]))
        self.assertEqual("NOT_MEASURED", result["model_tokens"])
        print("CONTEXT_THREE_VS_FIVE=" + json.dumps({
            row["profile"]: {
                "three_bytes": row["compact_source_bytes"],
                "five_bytes": row["extended_source_bytes"],
                "difference": row["difference_returned_source_bytes"],
                "skills_3": row["first_three_loaded"],
                "skills_5": row["first_five_loaded"],
            } for row in result["examples"]
        }, ensure_ascii=False, sort_keys=True), flush=True)


# Independent #439 source-only acceptance cases. No additional router or model.
SCENARIOS_439 = (
    ("python-fix", "Исправь баг в Python-функции", "codex-feature", "implementation"),
    ("pytest-tests", "Напиши pytest-тесты для Python-функции", "qa-python", "pytest-test-design"),
    ("fastapi-endpoint", "Реализуй FastAPI endpoint с валидацией", "backend", "api-design"),
    ("react-fix", "Исправь баг в React-компоненте формы", "frontend", "component-architecture"),
    ("mcp-security", "Проведи проверку безопасности MCP-сервера", "security-engineering", "security-review"),
    ("ux-ui", "Спроектируй интерфейс приложения и покажи макет", "ui-orchestra", "ux-ui-design-orchestra"),
    ("api-docs", "Обнови документацию API и примеры ответов", "docs-technical", "documentation-maintenance"),
    ("fullstack", "Разработай fullstack-функцию с FastAPI backend и React frontend", "fullstack", "fullstack-integration"),
)


class IndependentContext439Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tk = audit.adt_mcp.Toolkit(ROOT)
        cls.manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))

    def test_eight_synthetic_routes_and_mandatory_skills(self):
        self.assertEqual(8, len(SCENARIOS_439))
        for label, task, expected, mandatory in SCENARIOS_439:
            with self.subTest(scenario=label):
                route = self.tk.route(task)
                self.assertEqual(expected, route["profile"])
                self.assertIn(mandatory, route["skills"])
                self.assertEqual(len(route["skills"]), len(set(route["skills"])))
                self.assertEqual([], route["unavailable"])
                self.assertEqual("NOT_OBSERVED", route["routing_decision"]["client_activation"])

    def test_actual_returned_source_bytes_and_low_budget(self):
        rows = []
        for label, task, expected, mandatory in SCENARIOS_439:
            with self.subTest(scenario=label):
                route = self.tk.route(task)
                compact = self.tk.prepare_task(task, existing_skills=[],
                                               existing_roles=[], max_skills=3)
                full = [self.tk.read("skill", name, limit=32000)
                        for name in route["skills"]]
                self.assertFalse(any(x["truncated"] for x in full + compact["loaded_skills"]))
                full_bytes = sum(len(x["content"].encode("utf-8")) for x in full)
                compact_bytes = sum(len(x["content"].encode("utf-8"))
                                    for x in compact["loaded_skills"])
                self.assertEqual(compact_bytes,
                                 compact["context_load_metrics"]["skill_source_bytes"])
                self.assertLessEqual(compact_bytes, full_bytes)
                self.assertEqual(route["skills"], compact["selected_skills"])
                self.assertEqual(0, compact["context_load_metrics"]["reference_files_preloaded"])
                self.assertEqual("NOT_MEASURED", compact["context_load_metrics"]["model_tokens"])
                self.assertFalse(compact["installation_performed"])
                self.assertFalse(compact["project_files_changed"])
                preview = audit.profile_metrics.preview_metadata_budget(
                    ROOT, self.manifest, expected, 8000)
                limited = audit.profile_metrics.preview_metadata_budget(
                    ROOT, self.manifest, expected, 1)
                self.assertTrue(preview["within_budget"])
                self.assertFalse(limited["within_budget"])
                self.assertGreater(limited["over_budget_bytes"], 0)
                self.assertIn(mandatory, [x["skill"] for x in preview["skill_metadata"]])
                self.assertFalse(limited["automatic_pruning"])
                self.assertFalse(limited["applied"])
                self.assertEqual("NOT_MEASURED", limited["tokens"])
                rows.append({
                    "scenario": label, "routed_profile": route["profile"],
                    "all_selected_skill_bytes": full_bytes,
                    "first_three_skill_bytes": compact_bytes,
                    "yaml_metadata_bytes": preview["eager_metadata_bytes"],
                    "deferred_count": compact["context_load_metrics"]["deferred_skill_count"],
                    "first_three": [x["name"] for x in compact["loaded_skills"]],
                    "required_preserved": mandatory in route["skills"],
                    "model_tokens": "NOT_MEASURED",
                })
        print("NATIVE_CONTEXT_439_SOURCE_BYTES=" +
              json.dumps(rows, sort_keys=True, ensure_ascii=False), flush=True)

    def test_docs_mention_does_not_override_backend_implementation(self):
        self.assertEqual(
            "backend",
            self.tk.route("Разработай FastAPI endpoint и обнови документацию API")["profile"],
        )

    def test_determinism_and_no_duplicate_installed_skills(self):
        task = SCENARIOS_439[2][1]
        self.assertEqual(self.tk.route(task), self.tk.route(task))
        prepared = self.tk.prepare_task(
            task, existing_skills=["api-design"], existing_roles=[], max_skills=3)
        self.assertIn("api-design", prepared["already_available_skills"])
        self.assertNotIn("api-design", [x["name"] for x in prepared["loaded_skills"]])
        self.assertFalse(prepared["installation_performed"])


if __name__ == "__main__":
    unittest.main()
