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
            contents = target.read_bytes()
            git_digest = hashlib.sha1(
                b"blob " + str(len(contents)).encode("ascii") + b"\\0" + contents
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


if __name__ == "__main__":
    unittest.main()
