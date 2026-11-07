"""Offline contract checks for Toolkit-bundled pinned ECC eval evidence (#437).

Never executes candidate code, invokes an AI model, or uses a network client.
The upstream test cases run only against our *vendored* original JS library.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
VENDORED = ROOT / "third_party" / "ecc-v2.2.3" / "eval-harness"
TOOL = ROOT / "scripts" / "native_eval_capsules.js"
SOURCE_PIN = "25278e7d7b6cf6e6a4e7a6c8e10f14ff22f0eb5b"
UPSTREAM_TESTS = (
    "canonical.test.js", "envelope.test.js", "receipt.test.js",
    "replay.test.js", "retrospective.test.js",
)


class NativeEvalCapsuleTests(unittest.TestCase):
    def test_source_files_identical_to_pinned_git_blob(self):
        manifest = json.loads((VENDORED / "SOURCE_SNAPSHOT.json").read_text(encoding="utf-8"))
        self.assertEqual(1, manifest["schema_version"])
        self.assertEqual(SOURCE_PIN, manifest["source_revision"])
        self.assertEqual(18, manifest["original_source_count"])
        self.assertEqual(manifest["original_source_count"], len(manifest["source_files"]))
        self.assertTrue((ROOT / manifest["license_path"]).is_file())
        paths = set()
        for entry in manifest["source_files"]:
            relative = entry["origin"]
            self.assertNotIn("..", Path(relative).parts)
            self.assertEqual("third_party/ecc-v2.2.3/eval-harness/" + relative,
                             entry["path"])
            self.assertNotIn(relative, paths)
            paths.add(relative)
            target = ROOT / entry["path"]
            self.assertTrue(target.is_file())
            self.assertFalse(target.is_symlink())
            contents = target.read_bytes().replace(b"\r\n", b"\n")
            git_digest = hashlib.sha1(
                b"blob " + str(len(contents)).encode("ascii") + b"\0" + contents
            ).hexdigest()
            self.assertEqual(entry["git_blob"], git_digest, relative)
            self.assertEqual(entry["sha256"], hashlib.sha256(contents).hexdigest())
        self.assertNotIn("tests/scripts/eval-harness-package.test.js", paths)
        self.assertFalse(any("candidate" in key and "run.js" in key for key in paths))

    def node(self, *args: str, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
        exe = shutil.which("node")
        if not exe:
            self.skipTest("Node.js optional runtime not installed; live node tests NOT_VERIFIED")
        return subprocess.run([exe, *args], cwd=cwd, capture_output=True,
                              text=True, encoding="utf-8", errors="replace",
                              timeout=40, check=False)

    def test_original_offline_suite(self):
        for name in UPSTREAM_TESTS:
            with self.subTest(upstream=name):
                script = VENDORED / "tests" / "lib" / "eval-harness" / name
                result = self.node(str(script), cwd=VENDORED)
                self.assertEqual(0, result.returncode,
                                 name + ": " + (result.stdout + result.stderr)[-1100:])
                self.assertIn("Failed: 0", result.stdout)

    def test_native_capsule_receipt_replay_and_tamper_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            script = r"""
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const h = require(__LIB__);
const dir = process.argv[1];
const clock = () => new Date('2026-10-28T00:00:00.000Z');
const c = h.capsule.Capsule.create(dir, {
  run_id: 'run-1', capsule_id: 'cap-1',
  task_family: 'eval', harness_version: 'toolkit/1', clock,
});
c.append('plan', 'start', { task_id: 'unit' });
assert.equal(h.capsule.verify(dir).ok, true);
const receipt = h.receipt.buildReceipt(dir, { clock });
assert.equal(h.receipt.verifyReceipt(receipt, dir).ok, true);
h.receipt.writeReceipt(receipt, path.join(dir, 'receipt.json'));
const store = new h.replay.FixtureStore(path.join(dir, 'fixtures'));
store.put('read_fixture', { id: 'x' }, { result: 'fixture' });
let liveCalls = 0;
const tools = {
  read_fixture: { effect_class: 'SE0', determinism: 'deterministic',
                  impl: () => { liveCalls++; throw new Error('must never execute'); } },
  charge_card: { effect_class: 'SE4', determinism: 'nondeterministic',
                 impl: () => { liveCalls++; throw new Error('must never execute'); } },
};
const replay = h.replay.createReplayer(tools, { mode: 'replay', store });
assert.deepEqual(replay.call('read_fixture', { id: 'x' }), { result: 'fixture' });
assert.equal(liveCalls, 0);
assert.throws(() => replay.call('read_fixture', { id: 'missing' }),
              err => err.code === 'tool.fixture_missing');
assert.throws(() => replay.call('charge_card', {}),
              err => err.code === 'tool.effect_forbidden');
assert.equal(liveCalls, 0);
assert.throws(() => h.gate.requireSupportedIsolation(),
              err => err.code === 'gate.isolation_required');
const journal = path.join(dir, 'journal.ndjson');
fs.writeFileSync(journal, fs.readFileSync(journal, 'utf8')
  .replace('"task_id":"unit"', '"task_id":"tampered"'));
assert.equal(h.capsule.verify(dir).ok, false);
assert.equal(h.receipt.verifyReceipt(receipt, dir).ok, false);
console.log('NATIVE_CAPSULE_NEGATIVE=PASS');
""".replace("__LIB__", json.dumps(
                str(VENDORED / "scripts" / "lib" / "eval-harness")))
            result = self.node("-e", script, tmp)
            self.assertEqual(0, result.returncode, (result.stdout + result.stderr)[-1300:])
            self.assertIn("NATIVE_CAPSULE_NEGATIVE=PASS", result.stdout)

    def test_tool_is_manual_and_gate_refuses_before_io(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp)
            blocked = self.node(str(TOOL), "gate", "run")
            self.assertEqual(1, blocked.returncode)
            self.assertIn("gate.isolation_required", blocked.stderr)
            malformed = self.node(str(TOOL), "capsule", "verify")
            self.assertEqual(2, malformed.returncode)
            self.assertEqual([], list(dest.iterdir()))
            unknown = self.node(str(TOOL), "does-not-exist")
            self.assertEqual(2, unknown.returncode)


    def _security_fixture(self, root: Path, *, run_id: str = "run-safe"):
        """Build one local capsule with the original MIT library only."""
        script = r"""
const fs = require('node:fs'), path = require('node:path');
const h = require(__LIB__), root = process.argv[1], runId = process.argv[2];
const clock = () => new Date('2026-10-28T00:00:00.000Z');
const art = path.join(root, 'artifact.txt'), dir = path.join(root, 'capsule');
fs.writeFileSync(art, 'synthetic artifact');
const c = h.capsule.Capsule.create(dir, {
  run_id: runId, capsule_id: 'cap-secure', task_family: 'offline',
  harness_version: 'toolkit/1', clock
});
c.append('plan', 'recorded', {task_id: 'synthetic'});
const receipt = h.receipt.buildReceipt(dir, {artifact_path: art, clock});
h.receipt.writeReceipt(receipt, path.join(root, 'receipt.json'));
""".replace("__LIB__", json.dumps(str(VENDORED / "scripts" / "lib" / "eval-harness")))
        result = self.node("-e", script, str(root), run_id)
        self.assertEqual(0, result.returncode, result.stderr[-900:])
        return root / "capsule", root / "receipt.json", root / "artifact.txt"

    def test_native_rejects_unsigned_recomputed_gate_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            capsule, receipt, artifact = self._security_fixture(root)
            # Valid syntax and self-consistent receipt hash cannot make an
            # unsupported gate PASS trustworthy.
            script = r"""
const fs = require('node:fs'), h = require(__LIB__);
const file = process.argv[1], value = JSON.parse(fs.readFileSync(file, 'utf8'));
value.gate_verdict = 'PASS';
const {receipt_hash, signature, ...unsigned} = value;
value.receipt_hash = h.canonical.hashValue({...unsigned, signature: null});
fs.writeFileSync(file, JSON.stringify(value) + '\n');
""".replace("__LIB__", json.dumps(str(VENDORED / "scripts" / "lib" / "eval-harness")))
            changed = self.node("-e", script, str(receipt))
            self.assertEqual(0, changed.returncode, changed.stderr)
            before = {p.name: p.read_bytes() for p in (receipt, artifact, capsule / "projection.json")}
            result = self.node(str(TOOL), "receipt", "verify", str(receipt), str(capsule),
                               "--artifact", str(artifact))
            self.assertEqual(1, result.returncode)
            self.assertIn("UNVERIFIED_ATTESTATION_DENIED", result.stderr)
            self.assertEqual("", result.stdout)
            self.assertEqual(before, {p.name: p.read_bytes() for p in
                                     (receipt, artifact, capsule / "projection.json")})

    def test_native_rejects_secret_in_metadata_and_receipt_without_echo(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            canary = "sk-" + "Q" * 32  # Never an actual credential.
            capsule, receipt, artifact = self._security_fixture(root, run_id=canary)
            self.assertIn(canary, receipt.read_text(encoding="utf-8"))
            for args in (
                ("capsule", "verify", str(capsule)),
                ("capsule", "project", str(capsule)),
                ("receipt", "build", str(capsule), "--artifact", str(artifact)),
                ("receipt", "verify", str(receipt), str(capsule),
                 "--artifact", str(artifact)),
            ):
                with self.subTest(action=args[:2]):
                    before = (capsule / "projection.json").read_bytes()
                    result = self.node(str(TOOL), *args)
                    self.assertEqual(1, result.returncode)
                    self.assertIn("SENSITIVE_EVIDENCE_DENIED", result.stderr)
                    self.assertNotIn(canary, result.stderr + result.stdout)
                    self.assertEqual(before, (capsule / "projection.json").read_bytes())

    def test_native_rejects_unknown_receipt_fields_and_unverified_signature(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            capsule, receipt, artifact = self._security_fixture(root)
            baseline = json.loads(receipt.read_text(encoding="utf-8"))
            cases = (
                ({"private_email": "person@example.invalid"}, "UNSUPPORTED_RECEIPT_FIELDS"),
                ({"signature": "unverified-signer"}, "UNVERIFIED_ATTESTATION_DENIED"),
                ({"gate_receipt_digest": "a" * 64}, "UNVERIFIED_ATTESTATION_DENIED"),
            )
            for change, marker in cases:
                with self.subTest(change=next(iter(change))):
                    receipt.write_text(json.dumps({**baseline, **change}), encoding="utf-8")
                    result = self.node(str(TOOL), "receipt", "verify", str(receipt),
                                       str(capsule), "--artifact", str(artifact))
                    self.assertEqual(1, result.returncode)
                    self.assertIn(marker, result.stderr)

    def test_native_rejects_linked_receipt_and_capsule_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            capsule, receipt, artifact = self._security_fixture(root)
            linked_receipt = root / "receipt-link.json"
            try:
                linked_receipt.symlink_to(receipt)
            except (OSError, NotImplementedError):
                self.skipTest("Host does not permit creating symbolic links")
            rejected = self.node(str(TOOL), "receipt", "verify", str(linked_receipt),
                                 str(capsule), "--artifact", str(artifact))
            self.assertEqual(1, rejected.returncode)
            self.assertIn("LINKED_EVIDENCE_DENIED", rejected.stderr)
            # A symlinked projection must also be refused, not regenerated.
            projection = capsule / "projection.json"
            original = root / "original-projection.json"
            projection.rename(original)
            projection.symlink_to(original)
            rejected = self.node(str(TOOL), "receipt", "verify", str(receipt),
                                 str(capsule), "--artifact", str(artifact))
            self.assertEqual(1, rejected.returncode)
            self.assertIn("LINKED_EVIDENCE_DENIED", rejected.stderr)



    def test_native_verified_receipt_exposes_only_hashed_capsule_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            capsule, receipt, artifact = self._security_fixture(root)
            command = (str(TOOL), "receipt", "verify", str(receipt), str(capsule),
                       "--artifact", str(artifact))
            first = self.node(*command)
            second = self.node(*command)
            self.assertEqual(0, first.returncode, first.stderr)
            self.assertEqual(first.stdout, second.stdout)
            verdict = json.loads(first.stdout)
            self.assertTrue(verdict["ok"])
            self.assertRegex(verdict["capsule_identity_sha256"], r"^[0-9a-f]{64}$")
            self.assertNotIn("run-safe", first.stdout)
            self.assertNotIn("cap-secure", first.stdout)


    def test_external_receipt_hash_pin_detects_complete_consistent_replacement(self):
        """Internal hashes alone cannot detect wholesale rewrites; trusted pins can."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            capsule, receipt, artifact = self._security_fixture(root)
            original = json.loads(receipt.read_text(encoding="utf-8"))
            original_digest = original["receipt_hash"]
            pinned = self.node(str(TOOL), "receipt", "verify", str(receipt), str(capsule),
                               "--expected-receipt-hash", original_digest,
                               "--artifact", str(artifact))
            self.assertEqual(0, pinned.returncode, pinned.stderr)
            self.assertTrue(json.loads(pinned.stdout)["expected_receipt_hash_matches"])

            # Rebuild the entire capsule and receipt under the same identities,
            # keeping the artifact unchanged. No agent, process, network or model.
            second_root = root / "replacement"
            second_root.mkdir()
            second_capsule, second_receipt, _ = self._security_fixture(second_root)
            script = r"""
const h = require(__LIB__);
const path = require('node:path');
const clock = () => new Date('2026-10-28T00:00:00.000Z');
const dir = process.argv[1], file = process.argv[2];
const cap = h.capsule.Capsule.open(dir, {clock});
cap.append('attempt', 'changed', {task_id:'synthetic', status:'rewritten'});
const receipt = h.receipt.buildReceipt(dir, {artifact_path:file, clock});
h.receipt.writeReceipt(receipt, path.join(path.dirname(dir), 'receipt.json'));
""".replace("__LIB__", json.dumps(str(
                VENDORED / "scripts" / "lib" / "eval-harness")))
            changed = self.node("-e", script, str(second_capsule), str(artifact))
            self.assertEqual(0, changed.returncode, changed.stderr)
            for name in ("capsule.json", "journal.ndjson", "projection.json"):
                shutil.copyfile(second_capsule / name, capsule / name)
            shutil.copyfile(second_receipt, receipt)
            before = {p.name: p.read_bytes() for p in (
                receipt, artifact, capsule / "capsule.json",
                capsule / "journal.ndjson", capsule / "projection.json",
            )}
            unpinned = self.node(str(TOOL), "receipt", "verify",
                                 str(receipt), str(capsule), "--artifact", str(artifact))
            self.assertEqual(0, unpinned.returncode, unpinned.stderr)
            self.assertTrue(json.loads(unpinned.stdout)["ok"])

            rejected = self.node(str(TOOL), "receipt", "verify",
                                 str(receipt), str(capsule), "--artifact", str(artifact),
                                 "--expected-receipt-hash", original_digest)
            self.assertEqual(1, rejected.returncode)
            result = json.loads(rejected.stdout)
            self.assertFalse(result["ok"])
            self.assertEqual("receipt_anchor", result["check"])
            self.assertNotIn(original_digest, rejected.stderr + rejected.stdout)

            # A digest supplied by the same forger also passes. Caller must
            # independently obtain/trust the original pin.
            rewritten_digest = json.loads(receipt.read_text(encoding="utf-8"))["receipt_hash"]
            self.assertNotEqual(original_digest, rewritten_digest)
            rebound = self.node(str(TOOL), "receipt", "verify",
                                str(receipt), str(capsule),
                                "--expected-receipt-hash", rewritten_digest,
                                "--artifact", str(artifact))
            self.assertEqual(0, rebound.returncode, rebound.stderr)
            self.assertTrue(json.loads(rebound.stdout)["expected_receipt_hash_matches"])
            self.assertEqual(before, {p.name: p.read_bytes() for p in (
                receipt, artifact, capsule / "capsule.json",
                capsule / "journal.ndjson", capsule / "projection.json",
            )})

    def test_external_receipt_pin_options_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            capsule, receipt, artifact = self._security_fixture(root)
            sha = json.loads(receipt.read_text(encoding="utf-8"))["receipt_hash"]
            bad = (
                ("--expected-receipt-hash", "BAD_DIGEST"),
                ("--expected-receipt-hash", "A" * 64),
                ("--expected-receipt-hash", sha, "--expected-receipt-hash", sha),
                ("--artifact", str(artifact), "--artifact", str(artifact)),
                ("--expected-receipt-hash",),
                ("--unsupported-option", sha),
            )
            for options in bad:
                with self.subTest(options=options):
                    result = self.node(str(TOOL), "receipt", "verify",
                                       str(receipt), str(capsule), *options)
                    self.assertEqual(1, result.returncode)
                    self.assertIn("INVALID_OPTIONS", result.stderr)
                    self.assertEqual("", result.stdout)

if __name__ == "__main__":
    unittest.main()
