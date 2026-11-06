#!/usr/bin/env node
'use strict';

/**
 * Toolkit-native, explicitly invoked offline ECC-MIT eval evidence entrypoint.
 * The bundled library is pinned and byte-for-byte intact in third_party.
 * This is not an ECC runtime dependency or agent executor.
 *
 * Usage:
 *   node scripts/native_eval_capsules.js capsule verify <dir>
 *   node scripts/native_eval_capsules.js capsule project <dir>
 *   node scripts/native_eval_capsules.js receipt build <dir> [--artifact <file>]
 *   node scripts/native_eval_capsules.js receipt verify <receipt-file> <dir> [--artifact <file>]
 *   node scripts/native_eval_capsules.js gate run
 * No automatic writes, network calls, shell execution, model execution or promotion.
 * The project and build commands explicitly write local projection evidence.
 */

const fs = require('node:fs');
const path = require('node:path');
const lib = require('../third_party/ecc-v2.2.3/eval-harness/scripts/lib/eval-harness');

const usage = () => {
  process.stderr.write('native_eval_capsules: unsupported command or arguments\n');
  process.exitCode = 2;
};
const output = value => process.stdout.write(JSON.stringify(value, null, 2) + '\n');
const refuse = code => { throw Object.assign(new Error(code), { code }); };

// Keep native v1 receipts evidence-only. The native CLI has no trusted
// detached-signature verifier, gate receipt input, or OS-isolated gate executor.
// Claiming any of these would let an unsigned, recomputed PASS appear verified.
const RECEIPT_FIELDS = new Set([
  'schema', 'envelope_schema', 'capsule_id', 'run_id', 'capsule_root',
  'entry_count', 'journal_sha256', 'projection_hash', 'artifact_digest',
  'gate_receipt_digest', 'gate_verdict', 'created_at', 'signature', 'receipt_hash',
]);

function assertNoLinks(input) {
  const absolute = path.resolve(input);
  const root = path.parse(absolute).root;
  let cursor = root;
  for (const part of absolute.slice(root.length).split(path.sep).filter(Boolean)) {
    cursor = path.join(cursor, part);
    if (fs.lstatSync(cursor).isSymbolicLink()) refuse('LINKED_EVIDENCE_DENIED');
  }
}

function assertNoLinkedComponentsIfPresent(input) {
  const absolute = path.resolve(input);
  const root = path.parse(absolute).root;
  let cursor = root;
  for (const part of absolute.slice(root.length).split(path.sep).filter(Boolean)) {
    cursor = path.join(cursor, part);
    let stat;
    try { stat = fs.lstatSync(cursor); }
    catch (error) {
      // Let the original verifier return its machine-readable missing-file
      // check. Existing/dangling links remain denied, even before writes.
      if (error.code === 'ENOENT') return;
      throw error;
    }
    if (stat.isSymbolicLink()) refuse('LINKED_EVIDENCE_DENIED');
  }
}

function assertCapsuleFiles(dir) {
  for (const leaf of ['capsule.json', 'journal.ndjson', 'projection.json']) {
    assertNoLinkedComponentsIfPresent(path.join(dir, leaf));
  }
}

function assertNoSensitiveIdentity(dir) {
  const snapshot = lib.capsule.readCapsule(dir);
  if (snapshot.ok && lib.envelope.scanForCanaries(snapshot.meta).length) {
    refuse('SENSITIVE_EVIDENCE_DENIED');
  }
}

function assertNativeReceipt(receipt) {
  if (!receipt || typeof receipt !== 'object' || Array.isArray(receipt)) return;
  if (Object.keys(receipt).some(field => !RECEIPT_FIELDS.has(field))) {
    refuse('UNSUPPORTED_RECEIPT_FIELDS');
  }
  if (lib.envelope.scanForCanaries(receipt).length) {
    refuse('SENSITIVE_EVIDENCE_DENIED');
  }
  // A hash alone cannot witness the origin of PASS or validate an alleged
  // detached signature. The native CLI deliberately cannot verify these claims.
  if (receipt.gate_verdict != null || receipt.gate_receipt_digest != null
      || receipt.signature != null) {
    refuse('UNVERIFIED_ATTESTATION_DENIED');
  }
}

function artifactArgs(rest) {
  if (!rest.length) return undefined;
  if (rest.length !== 2 || rest[0] !== '--artifact' || !rest[1] || rest[1].startsWith('--')) {
    throw Object.assign(new Error('invalid option'), { code: 'INVALID_OPTIONS' });
  }
  return rest[1];
}

function main(args) {
  const [group, action, ...rest] = args;
  if (group === 'gate' && action === 'run') {
    // Deny BEFORE opening a config, capsule or running any candidate.
    if (rest.length) return usage();
    lib.gate.requireSupportedIsolation();
    return;
  }
  if (group === 'capsule' && (action === 'verify' || action === 'project')) {
    if (rest.length !== 1 || !rest[0] || rest[0].startsWith('--')) return usage();
    assertCapsuleFiles(rest[0]);
    assertNoSensitiveIdentity(rest[0]);
    const result = action === 'verify'
      ? lib.capsule.verify(rest[0]) : lib.capsule.writeProjection(rest[0]);
    output(result);
    if (action === 'verify' && !result.ok) process.exitCode = 1;
    return;
  }
  if (group === 'receipt' && action === 'build') {
    if (rest.length < 1 || !rest[0] || rest[0].startsWith('--')) return usage();
    const artifact = artifactArgs(rest.slice(1));
    assertCapsuleFiles(rest[0]);
    assertNoSensitiveIdentity(rest[0]);
    if (artifact) assertNoLinks(artifact);
    const result = lib.receipt.buildReceipt(rest[0], { artifact_path: artifact });
    assertNativeReceipt(result);
    output(result);
    return;
  }
  if (group === 'receipt' && action === 'verify') {
    if (rest.length < 2 || rest[0].startsWith('--') || rest[1].startsWith('--')) return usage();
    const artifact = artifactArgs(rest.slice(2));
    const file = rest[0];
    assertNoLinks(file);
    assertCapsuleFiles(rest[1]);
    if (artifact) assertNoLinks(artifact);
    const bytes = fs.readFileSync(file);
    if (bytes.length > 32768) refuse('INVALID_INPUT');
    const value = JSON.parse(bytes.toString('utf8'));
    assertNativeReceipt(value);
    assertNoSensitiveIdentity(rest[1]);
    const result = lib.receipt.verifyReceipt(value, rest[1], { artifact_path: artifact });
    output(result);
    if (!result.ok) process.exitCode = 1;
    return;
  }
  usage();
}

if (require.main === module) {
  try { main(process.argv.slice(2)); }
  catch (error) {
    // Do not echo external source paths, payload contents or secrets.
    process.stderr.write('native_eval_capsules: ' + (error.code || 'EVIDENCE_REJECTED') + '\n');
    process.exitCode = 1;
  }
}

module.exports = { main };
