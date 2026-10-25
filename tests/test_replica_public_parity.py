"""Source pin, opt-in and public evidence regression tests without model APIs."""
from __future__ import annotations

import csv
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "replica_public_parity.py"
SPEC = importlib.util.spec_from_file_location("replica_public_parity", SCRIPT)
assert SPEC and SPEC.loader
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


def git(root: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(root), *args], check=True,
                          capture_output=True, text=True).stdout.strip()


class ReplicaAuditTests(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.root = Path(self.t.name)
        self.upstream = self.root / "source"
        self.upstream.mkdir()
        git(self.upstream, "init", "-q")
        for path in MOD.UPSTREAM_BLOBS:
            dest = self.upstream / path
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text("print('UPSTREAM_PARITY_RUN=YES')\n" if path.endswith("parity.py") else "synthetic")
        git(self.upstream, "add", ".")
        git(self.upstream, "-c", "user.name=QA", "-c", "user.email=qa@example.test", "commit", "-qm", "test")
        self.sha = git(self.upstream, "rev-parse", "HEAD")
        self.blobs = {p: git(self.upstream, "rev-parse", f"HEAD:{p}") for p in MOD.UPSTREAM_BLOBS}
        self.matrix = self.root / "sample.csv"
        self.write_matrix([{"feature":"workout log", "area":"workout", "priority":"must",
                            "original":"yes", "clone":"no", "notes":"", "evidence_url":"https://example.org/public",
                            "target_evidence":""}])
        self.p1 = patch.object(MOD, "UPSTREAM_SHA", self.sha)
        self.p2 = patch.object(MOD, "UPSTREAM_BLOBS", self.blobs)
        self.p1.start(); self.p2.start()

    def tearDown(self):
        self.p2.stop(); self.p1.stop(); self.t.cleanup()

    def write_matrix(self, rows):
        with self.matrix.open("w", newline="") as file:
            writer=csv.DictWriter(file,fieldnames=["feature", "area", "priority", "original", "clone", "notes", "evidence_url", "target_evidence"])
            writer.writeheader(); writer.writerows(rows)

    def cli(self, *args):
        out, err = StringIO(), StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = MOD.main(["--upstream", str(self.upstream), *args])
        return rc, out.getvalue(), err.getvalue()

    def test_readonly_source_preflight(self):
        rc, out, _=self.cli()
        self.assertEqual(rc,0); self.assertIn("EXECUTION=NOT_RUN",out)

    def test_bounded_original_parity_invocation(self):
        rc, out, _=self.cli("--matrix",str(self.matrix))
        self.assertEqual(rc,0); self.assertIn("UPSTREAM_PARITY_RUN=YES",out)

    def test_dirty_upstream_refused(self):
        (self.upstream/"replica-diff/parity.py").write_text("print('modified')")
        rc,_,e=self.cli()
        self.assertEqual(rc,2); self.assertIn("checkout must be clean",e)

    def test_extra_upstream_file_refused(self):
        (self.upstream/"untracked.py").write_text("print('x')")
        rc,_,_=self.cli(); self.assertEqual(rc,2)

    def test_wrong_upstream_sha_refused(self):
        with patch.object(MOD,"UPSTREAM_SHA","0"*40):
            rc,_,e=self.cli(); self.assertEqual(rc,2); self.assertIn("Unpinned",e)

    def test_no_evidence_refused(self):
        self.write_matrix([{"feature":"X","area":"workout","priority":"must","original":"yes",
                            "clone":"no","notes":"","evidence_url":"","target_evidence":""}])
        rc,_,e=self.cli("--matrix",str(self.matrix))
        self.assertEqual(rc,2); self.assertIn("HTTPS evidence",e)

    def test_unverified_yfc_claim_refused(self):
        self.write_matrix([{"feature":"X","area":"workout","priority":"must","original":"yes",
                            "clone":"yes","notes":"","evidence_url":"https://example.org/feature","target_evidence":""}])
        rc,_,_=self.cli("--matrix",str(self.matrix)); self.assertEqual(rc,2)

    def test_unknown_is_not_scored_as_absence(self):
        self.write_matrix([{"feature":"X","area":"workout","priority":"must","original":"yes",
                            "clone":"unknown","notes":"","evidence_url":"https://example.org/feature","target_evidence":""}])
        rc,_,e=self.cli("--matrix",str(self.matrix)); self.assertEqual(rc,2); self.assertIn("UNKNOWN",e)

    def test_readonly_matrix_persistence(self):
        before=self.matrix.read_bytes(); rc,_,_=self.cli("--matrix",str(self.matrix))
        self.assertEqual(rc,0); self.assertEqual(self.matrix.read_bytes(),before)

    def test_non_root_upstream_refused(self):
        with self.assertRaises(MOD.Refusal): MOD.verified_upstream(str(self.upstream/"replica-diff"))


if __name__=="__main__":unittest.main()
