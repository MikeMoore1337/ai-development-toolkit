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
const lib = require('../third_party/ecc-v2.2.3/eval-harness/scripts/lib/eval-harness');

const usage = () => {
  process.stderr.write('native_eval_capsules: unsupported command or arguments\n');
  process.exitCode = 2;
};
const output = value => process.stdout.write(JSON.stringify(value, null, 2) + '\n');

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
    const result = action === 'verify'
      ? lib.capsule.verify(rest[0]) : lib.capsule.writeProjection(rest[0]);
    output(result);
    if (action === 'verify' && !result.ok) process.exitCode = 1;
    return;
  }
  if (group === 'receipt' && action === 'build') {
    if (rest.length < 1 || !rest[0] || rest[0].startsWith('--')) return usage();
    const artifact = artifactArgs(rest.slice(1));
    const result = lib.receipt.buildReceipt(rest[0], { artifact_path: artifact });
    output(result);
    return;
  }
  if (group === 'receipt' && action === 'verify') {
    if (rest.length < 2 || rest[0].startsWith('--') || rest[1].startsWith('--')) return usage();
    const artifact = artifactArgs(rest.slice(2));
    const file = rest[0];
    if (fs.lstatSync(file).isSymbolicLink()) throw Object.assign(new Error('linked input'), { code: 'INVALID_INPUT' });
    const bytes = fs.readFileSync(file);
    if (bytes.length > 32768) throw Object.assign(new Error('oversized receipt'), { code: 'INVALID_INPUT' });
    const value = JSON.parse(bytes.toString('utf8'));
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
