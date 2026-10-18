"""Intentional failure to verify protected branch rules. Never merge this file."""
import unittest


class BranchProtectionProbe(unittest.TestCase):
    def test_required_ci_prevents_merge(self):
        self.fail("EXPECTED FAIL: branch-protection verification only; DO NOT MERGE")


if __name__ == "__main__":
    unittest.main()
