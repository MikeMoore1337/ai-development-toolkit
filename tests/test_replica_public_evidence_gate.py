"""Deterministic safety and evidence checks for #373."""
import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "replica_public_evidence_gate.py"
spec = importlib.util.spec_from_file_location("replica_public_evidence_gate", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

SHA = "77c9436fb3d18c3d58169efb8caf4fe906b0dc51"


def sample():
    return {
        "schema": 1,
        "mode": "PUBLIC_READ_ONLY",
        "upstream_sha": SHA,
        "features": [{
            "feature": "История тренировок",
            "competitor": "VERIFIED",
            "competitor_source": "https://example.org/public-feature",
            "yfc": "UNVERIFIED",
            "yfc_source": "https://github.com/MikeMoore1337/your-fitness-coach/issues/1166",
            "gap": "CANDIDATE",
        }],
    }


class ReplicaEvidenceGateTests(unittest.TestCase):
    def test_valid_public_packet(self):
        self.assertEqual(module.validate(sample())["decision"], "PASS")

    def test_unverified_is_not_gap_proof(self):
        p = sample()
        p["features"][0]["gap"] = "VERIFIED"
        self.assertEqual(module.validate(p)["decision"], "BLOCKED")

    def test_no_local_or_insecure_source(self):
        for url in ("http://example.org/a", "https://localhost/a", "https://127.0.0.1/a", "https://internal.local/a", "https://user:pass@example.org/a"):
            with self.subTest(url=url):
                p = sample()
                p["features"][0]["competitor_source"] = url
                self.assertEqual(module.validate(p)["decision"], "BLOCKED")

    def test_requires_provenance(self):
        p = sample()
        p["features"][0].pop("yfc_source")
        self.assertEqual(module.validate(p)["decision"], "BLOCKED")

    def test_blocks_sensitive_field(self):
        p = sample()
        p["features"][0]["access_token"] = "synthetic"
        self.assertEqual(module.validate(p)["decision"], "BLOCKED")

    def test_blocks_wrong_scope(self):
        p = sample()
        p["mode"] = "SCRAPE_AND_CLONE"
        self.assertEqual(module.validate(p)["decision"], "BLOCKED")

    def test_blocks_unpinned_source(self):
        p = sample()
        p["upstream_sha"] = "main"
        self.assertEqual(module.validate(p)["decision"], "BLOCKED")

    def test_blocks_overlong_packet(self):
        p = sample()
        p["features"] *= 101
        self.assertEqual(module.validate(p)["decision"], "BLOCKED")

    def test_rejects_bad_shapes(self):
        for p in ([], None, {}, {"features": []}):
            with self.subTest(p=p):
                self.assertEqual(module.validate(p)["decision"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
