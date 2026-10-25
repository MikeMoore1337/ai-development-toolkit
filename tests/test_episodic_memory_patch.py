"""Reproducible offline tests for the pinned Episodic Memory source patch."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/check_episodic_memory_patch.py"
SPEC = importlib.util.spec_from_file_location("check_episodic_memory_patch", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class EpisodicMemoryPatchContract(unittest.TestCase):
    def test_integrity_and_changed_paths(self) -> None:
        MODULE.check()

    def test_modified_patch_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            changed = Path(folder) / "tampered.patch"
            changed.write_bytes(MODULE.PATCH.read_bytes() + b"# tampered\n")
            with patch.object(MODULE, "PATCH", changed):
                with self.assertRaisesRegex(ValueError, "SHA256"):
                    MODULE.check()

    def test_symlinked_patch_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            fake = Path(folder) / "symlink.patch"
            try:
                fake.symlink_to(MODULE.PATCH)
            except (OSError, NotImplementedError):
                self.skipTest("Symlinks not permitted by current runner")
            with patch.object(MODULE, "PATCH", fake):
                with self.assertRaisesRegex(ValueError, "Symlinked"):
                    MODULE.check()


if __name__ == "__main__":
    unittest.main()
