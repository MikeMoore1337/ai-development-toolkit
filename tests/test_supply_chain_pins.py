"""Offline regression checks for immutable CI action refs and pinned tooling."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"

PINNED = {
    "actions/checkout": {
        "3d3c42e5aac5ba805825da76410c181273ba90b1",
        "11d5960a326750d5838078e36cf38b85af677262",
    },
    "actions/setup-python": {
        "6d4fd22b20465ccc0f7354476588e8df7c9ca0e0",
        "a26af69be951a213d495a4c3e4e4022e16d87065",
    },
    "actions/setup-node": {
        "49933ea5288caeca8642d1e84afbd3f7d6820020",
    },
    "actions/upload-artifact": {
        "ea165f8d65b6e75b540449e92b4886f43607fa02",
    },
    "affaan-m/agentshield": {
        "b0891303bdcd6037376a94263d45cfd2ff3dfb98",
    },
    "astral-sh/setup-uv": {
        "c771a70e6277c0a99b617c7a806ffedaca235ff9",
    },
}
ACTION = re.compile(r"^\s*(?:-\s*)?uses:\s*(\S+)", re.MULTILINE)


def valid_action(value: str) -> bool:
    if "@" not in value:
        return False
    name, revision = value.rsplit("@", 1)
    return revision in PINNED.get(name, set())


class SupplyChainPinTests(unittest.TestCase):
    def test_all_workflows_use_only_approved_full_immutable_commit_pins(self):
        paths = sorted(WORKFLOWS.glob("*.yml"))
        # Explicitly reviewed workflow inventory: a new job is a supply-chain change.
        expected = {
            "cisco-mcp-smoke.yml", "episodic-memory-windows.yml",
            "personal-mcp-optin-discovery-smoke.yml", "pinned-skill-discovery-smoke.yml",
            "publish-integration-sources.yml", "release-archive.yml",
            "validate.yml", "replica-public-parity.yml", "harness2-upstream.yml",
            "ecc-agentshield.yml", "ecc-memory-vault.yml",
        }
        self.assertEqual(expected, {path.name for path in paths})
        observed = {}
        for path in paths:
            references = ACTION.findall(path.read_text(encoding="utf-8"))
            self.assertTrue(references, path.as_posix())
            for value in references:
                with self.subTest(path=path.name, reference=value):
                    self.assertTrue(valid_action(value), value)
                    self.assertRegex(value.rsplit("@", 1)[1], r"^[0-9a-f]{40}$")
                    observed.setdefault(value.split("@", 1)[0], set()).add(value.split("@")[1])
        self.assertEqual(set(PINNED), set(observed))

    def test_negative_unpinned_and_unapproved_sources(self):
        for candidate in ("actions/checkout@v7", "actions/setup-python@v5",
                          "actions/upload-artifact@main", "actions/checkout@deadbeef",
                          "evil/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1",
                          "actions/checkout@0000000000000000000000000000000000000000",
                          "actions/checkout"):
            with self.subTest(candidate=candidate):
                self.assertFalse(valid_action(candidate))

    def test_dependency_constraint_is_exact_and_cross_platform(self):
        self.assertEqual("PyYAML==6.0.3",
                         (ROOT / "requirements-dev.txt").read_text(encoding="utf-8").strip())


if __name__ == "__main__":
    unittest.main()
