"""Regression coverage for opt-in ruleset configuration without network calls."""

import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "configure_required_checks.py"
spec = importlib.util.spec_from_file_location("configure_required_checks", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def example_ruleset():
    return {
        "name": "Protect main",
        "target": "branch",
        "enforcement": "active",
        "conditions": {"ref_name": {"include": ["~DEFAULT_BRANCH"], "exclude": []}},
        "bypass_actors": [],
        "rules": [
            {"type": "deletion"},
            {"type": "non_fast_forward"},
            {"type": "pull_request", "parameters": {"required_approving_review_count": 0}},
            {
                "type": "required_status_checks",
                "parameters": {
                    "strict_required_status_checks_policy": True,
                    "do_not_enforce_on_create": False,
                    "required_status_checks": [],
                },
            },
        ],
    }


class RequiredChecksTests(unittest.TestCase):
    def test_preserves_unrelated_rules(self):
        original = example_ruleset()
        payload, changed = module.prepare_update(original)
        self.assertTrue(changed)
        self.assertEqual(original["rules"][:3], payload["rules"][:3])
        self.assertEqual(original["rules"][3]["parameters"]["required_status_checks"], [])
        self.assertEqual(
            payload["rules"][3]["parameters"]["required_status_checks"],
            module.desired_status_checks(),
        )

    def test_idempotent(self):
        payload, _ = module.prepare_update(example_ruleset())
        after, changed = module.prepare_update(payload)
        self.assertFalse(changed)
        self.assertEqual(after, payload)

    def test_refuses_wrong_branch(self):
        item = example_ruleset()
        item["conditions"]["ref_name"]["include"] = ["refs/heads/dev"]
        with self.assertRaisesRegex(RuntimeError, "default/main"):
            module.prepare_update(item)

    def test_refuses_missing_bypass_visibility(self):
        item = example_ruleset()
        del item["bypass_actors"]
        with self.assertRaisesRegex(RuntimeError, "bypass actors"):
            module.prepare_update(item)

    @patch.object(module, "detect_repo", return_value="Example/repo")
    @patch.object(module, "gh_json")
    def test_preview_never_sends_mutation(self, gh, _repo):
        gh.side_effect = [
            [{"name": "Protect main", "source_type": "Repository", "id": 42}],
            example_ruleset(),
        ]
        self.assertEqual(module.main([]), 0)
        self.assertEqual(gh.call_count, 2)


if __name__ == "__main__":
    unittest.main()
