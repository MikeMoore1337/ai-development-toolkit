"""Issue #61: independent synthetic DevOps safety oracles."""
from __future__ import annotations

import ast
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from install import skill_sources  # noqa: E402
from skill_manager import operate, read_state  # noqa: E402
import validate_devops as devops  # noqa: E402


class DevOpsContracts(unittest.TestCase):
    def test_reference_and_all_independent_negative_cases(self):
        packet = devops.fixtures()
        self.assertEqual("1.0.0", packet["fixture_version"])
        self.assertEqual("SYNTHETIC_CONTRACT_ONLY", packet["nature"])
        self.assertEqual([], devops.validate(packet["reference"]))
        self.assertGreaterEqual(len(packet["negative"]), 12)
        seen = set()
        for case in packet["negative"]:
            with self.subTest(case=case["id"]):
                self.assertNotIn(case["id"], seen)
                seen.add(case["id"])
                mutant = devops.mutate(packet["reference"], case["path"], case["value"])
                self.assertNotEqual(packet["reference"], mutant)
                self.assertIn(case["code"], devops.validate(mutant))
        report = devops.run_cases()
        self.assertEqual("PASS", report["result"])
        self.assertEqual(len(seen), report["negatives_rejected"])
        self.assertEqual("NOT_RUN", report["real_deployment"])

    def test_status_cannot_be_promoted_from_green_ci(self):
        reference = devops.fixtures()["reference"]
        for state in ("APPLY_AUTHORIZED", "APPLIED", "POST_APPLY_VERIFIED"):
            bad = copy.deepcopy(reference)
            bad["deployment"]["state"] = state
            self.assertIn("MISSING_APPROVAL", devops.validate(bad))
        bad = copy.deepcopy(reference)
        bad["approval"] = {"scoped": True, "target": "ci", "evidence": "fictional"}
        bad["deployment"]["state"] = "APPLIED"
        self.assertIn("FALSE_APPLY_CLAIM", devops.validate(bad))
        bad["deployment"]["state"] = "POST_APPLY_VERIFIED"
        self.assertIn("MISSING_POST_VERIFICATION", devops.validate(bad))
        bad["deployment"]["evidence"] = "DEPLOYMENT_VERIFIED"
        self.assertIn("EVIDENCE_INFLATION", devops.validate(bad))

    def test_missing_contract_fields_are_blocked(self):
        reference = devops.fixtures()["reference"]
        self.assertEqual(["INVALID_CONTRACT"], devops.validate({}))
        for name in sorted(devops.REQUIRED):
            with self.subTest(missing=name):
                bad = copy.deepcopy(reference)
                del bad[name]
                self.assertIn("INVALID_CONTRACT", devops.validate(bad))

    def test_secret_not_disclosed(self):
        bad = copy.deepcopy(devops.fixtures()["reference"])
        marker = "SYNTHETIC_CANARY_MUST_NOT_LEAK"
        bad["secrets"]["embedded_value"] = marker
        findings = devops.validate(bad)
        self.assertIn("SECRET_EXPOSURE", findings)
        self.assertNotIn(marker, json.dumps(findings))

    def test_no_external_commands_or_uncontrolled_storage(self):
        source = (ROOT / "scripts/validate_devops.py").read_text(encoding="utf-8")
        module = ast.parse(source)
        imported = {n.name.split(".")[0] for x in ast.walk(module)
                    if isinstance(x, ast.Import) for n in x.names}
        imported |= {x.module.split(".")[0] for x in ast.walk(module)
                     if isinstance(x, ast.ImportFrom) and x.module}
        self.assertFalse(imported & {"socket", "urllib", "requests", "http",
                                     "subprocess", "asyncio", "aiohttp",
                                     "docker", "boto3", "terraform"})
        with tempfile.TemporaryDirectory() as folder:
            initial = list(Path(folder).iterdir())
            self.assertEqual("PASS", devops.run_cases()["result"])
            self.assertEqual(initial, list(Path(folder).iterdir()))

    def test_dockerfile_positive_and_negative_static_contract(self):
        """Inspect Dockerfile text only; never build or execute either fixture."""
        base = ROOT / "fixtures/devops/docker"

        def assess(path):
            directory = base / path
            text = (directory / "Dockerfile").read_text(encoding="utf-8")
            instructions = [line.strip() for line in text.splitlines()
                            if line.strip() and not line.lstrip().startswith("#")]
            issues = set()
            if "USER 10001" not in instructions:
                issues.add("REQUIRED_NON_ROOT")
            if "COPY . /srv" in instructions and (
                directory / "fixture_debug_config.txt"
            ).exists():
                issues.add("UNSCOPED_BUILD_CONTEXT")
            command = next((line[4:].strip() for line in instructions
                            if line.startswith("CMD ")), "")
            try:
                argv = json.loads(command)
            except json.JSONDecodeError:
                argv = []
            if argv != ["python", "/srv/app.py"] or not (
                directory / "app.py"
            ).is_file():
                issues.add("INVALID_STARTUP")
            health = next((line for line in instructions
                           if line.startswith("HEALTHCHECK CMD ")), "")
            if ("EXPOSE 8080" not in instructions or
                    "127.0.0.1:8080/health" not in health):
                issues.add("INVALID_HEALTH_CONTRACT")
            return issues

        self.assertEqual(set(), assess("good"))
        self.assertEqual(
            {"REQUIRED_NON_ROOT", "UNSCOPED_BUILD_CONTEXT",
             "INVALID_STARTUP", "INVALID_HEALTH_CONTRACT"},
            assess("bad"),
        )

    def test_optional_profile_preview_apply_and_source_boundary(self):
        manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
        names = manifest["profiles"]["devops-infrastructure"]
        self.assertEqual(
            ["devops-infrastructure", "release-safety",
             "security-boundaries", "architecture-decisions"], names
        )
        self.assertNotIn("devops-infrastructure", manifest["profiles"]["general"])
        source = skill_sources(manifest)["devops-infrastructure"]
        self.assertEqual(
            ROOT / "extensions/devops/skills/devops-infrastructure", source
        )
        original = (source / "SKILL.md").read_bytes()
        with tempfile.TemporaryDirectory() as directory:
            for layout in ("codex", "claude"):
                dest = Path(directory) / layout
                dest.mkdir()
                existing = dest / "AGENTS.md"
                existing.write_text("unmanaged\n", encoding="utf-8")
                preview = operate("install", dest, names=names, layout=layout)
                self.assertFalse(preview["applied"])
                self.assertEqual("unmanaged\n", existing.read_text(encoding="utf-8"))
                applied = operate("install", dest, names=names, layout=layout,
                                  apply=True)
                self.assertTrue(applied["applied"])
                self.assertEqual(set(names), set(read_state(dest, layout)["skills"]))
                self.assertEqual("unmanaged\n", existing.read_text(encoding="utf-8"))
        self.assertEqual(original, (source / "SKILL.md").read_bytes())


if __name__ == "__main__":
    unittest.main()
