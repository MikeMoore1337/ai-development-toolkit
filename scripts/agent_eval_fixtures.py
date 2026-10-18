#!/usr/bin/env python3
"""Three tiny, dependency-free benchmark repositories for REAL agent trials.

These are deliberately imperfect demonstration projects; their acceptance
oracles are held outside agent workspaces until after each attempt.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

FIXTURES = {
    "python-api": {
        "language": "python",
        "task": "Fix parse_retry_after(value) to accept unsigned decimal seconds with surrounding ASCII whitespace; return None for missing, blank, negative or nondecimal values. Keep its public interface and add no dependencies.",
        "files": {
            "retry.py": """def parse_retry_after(value: str | None) -> int | None:
    if value is None:
        return None
    if value.isdigit():
        return int(value)
    return None
""",
            "README.md": "# Retry-After parsing\n\nRun with standard Python. The parser returns seconds or None.\n",
        },
        "oracle_path": "oracle_tests/test_retry.py",
        "oracle": """import unittest
from retry import parse_retry_after


class ParserContract(unittest.TestCase):
    def test_whitespace(self):
        self.assertEqual(parse_retry_after(" 42 "), 42)
    def test_zero(self):
        self.assertEqual(parse_retry_after("0"), 0)
    def test_none(self):
        self.assertIsNone(parse_retry_after(None))
    def test_invalid(self):
        for value in ("", "  ", "-3", "+3", "4.1", "1x"):
            with self.subTest(value=value):
                self.assertIsNone(parse_retry_after(value))


if __name__ == "__main__":
    unittest.main()
""",
        "oracle_command": ["{python}", "-m", "unittest", "discover", "-s", "oracle_tests", "-v"],
    },
    "javascript-ui": {
        "language": "javascript",
        "task": "Fix parsePort(value) to accept only integer TCP ports from 1 to 65535, including surrounding ASCII whitespace. Return null for blanks, invalid, fractional or out-of-range values. Do not add dependencies or change exports.",
        "files": {
            "port.mjs": """export function parsePort(value) {
  const result = Number(value);
  return Number.isInteger(result) ? result : null;
}
""",
            "package.json": '{"name":"port-parser-pilot","private":true,"type":"module","scripts":{"test":"node --test"}}\n',
        },
        "oracle_path": "oracle_tests/port.test.mjs",
        "oracle": """import { test } from 'node:test';
import { strict as assert } from 'node:assert';
import { parsePort } from '../port.mjs';

test('valid boundary ports', () => {
  assert.equal(parsePort('1'), 1);
  assert.equal(parsePort(' 8080 '), 8080);
  assert.equal(parsePort('65535'), 65535);
});
test('reject invalid ports', () => {
  for (const item of ['', '  ', '0', '-1', '65536', '3.5', 'abc']) {
    assert.equal(parsePort(item), null, JSON.stringify(item));
  }
});
""",
        "oracle_command": ["node", "--test", "oracle_tests/port.test.mjs"],
    },
    "go-cli": {
        "language": "go",
        "task": "Fix ParseTimeout(raw) to accept a decimal timeout from 1 to 60000 milliseconds, tolerating surrounding whitespace, and return an error for zero, negative, malformed or out-of-range input. Preserve the function signature and use only Go's standard library.",
        "files": {
            "go.mod": "module example.com/adt-eval-timeout\n\ngo 1.20\n",
            "timeout.go": """package timeout

import "strconv"

func ParseTimeout(raw string) (int, error) {
    return strconv.Atoi(raw)
}
""",
        },
        "oracle_path": "timeout_test.go",
        "oracle": """package timeout

import "testing"

func TestValidTimeout(t *testing.T) {
    for _, tc := range []struct{input string; expected int}{
        {"1", 1}, {" 250 ", 250}, {"60000", 60000},
    } {
        actual, err := ParseTimeout(tc.input)
        if err != nil || actual != tc.expected {
            t.Errorf("%q: got (%d, %v), expected %d", tc.input, actual, err, tc.expected)
        }
    }
}
func TestInvalidTimeout(t *testing.T) {
    for _, input := range []string{"", "  ", "0", "-1", "60001", "1ms", "1.1"} {
        if _, err := ParseTimeout(input); err == nil {
            t.Errorf("%q: expected error", input)
        }
    }
}
""",
        "oracle_command": ["go", "test", "./...", "-count=1"],
    },
}


def materialize(case_id: str, destination: Path, *, include_oracle: bool = False) -> None:
    """Refuse preexisting directories. The hidden oracle is never in an agent copy."""
    case = FIXTURES[case_id]
    if destination.exists():
        raise ValueError(f"Refusing to overwrite fixture directory: {destination}")
    destination.mkdir(parents=True)
    for name, content in case["files"].items():
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")
    if include_oracle:
        oracle = destination / case["oracle_path"]
        oracle.parent.mkdir(parents=True, exist_ok=True)
        oracle.write_text(case["oracle"], encoding="utf-8", newline="\n")


def snapshot_digest(case_id: str) -> str:
    """Stable digest of the initial visible project, distinct from Git commit SHA."""
    case = FIXTURES[case_id]
    digest = hashlib.sha256()
    for name, content in sorted(case["files"].items()):
        digest.update(name.encode("utf-8") + b"\0")
        digest.update(content.encode("utf-8"))
    return digest.hexdigest()


def init_git(workspace: Path) -> str:
    """Pin a real local Git commit, with no remote, hooks or inherited author."""
    no_hooks = workspace / ".empty-hooks"
    no_hooks.mkdir(exist_ok=True)
    env = dict(os.environ, GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
    commands = (
        ["git", "init", "-q", "-b", "main"],
        ["git", "-c", "core.hooksPath=.empty-hooks", "add", "."],
        ["git", "-c", "user.name=Eval Fixture", "-c", "user.email=eval@example.invalid",
         "-c", "commit.gpgsign=false", "-c", "core.hooksPath=.empty-hooks",
         "commit", "-q", "-m", "Pinned synthetic benchmark fixture"],
        ["git", "rev-parse", "HEAD"],
    )
    output = ""
    for command in commands:
        result = subprocess.run(command, cwd=workspace, env=env,
                                capture_output=True, text=True, encoding="utf-8",
                                timeout=30, check=False)
        if result.returncode:
            raise RuntimeError(f"Local Git fixture initialization failed: {result.stderr}")
        output = result.stdout.strip()
    if len(output) != 40:
        raise RuntimeError("Invalid fixture Git commit")
    return output


def oracle_command(case_id: str) -> list[str]:
    import sys
    return [sys.executable if item == "{python}" else item
            for item in FIXTURES[case_id]["oracle_command"]]


if __name__ == "__main__":
    print(json.dumps({k: {"language": v["language"], "snapshot_sha256": snapshot_digest(k)}
                      for k, v in FIXTURES.items()}, indent=2))
