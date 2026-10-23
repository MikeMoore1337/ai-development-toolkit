"""Guard public documentation against product-owner project fingerprints.

Third-party client compatibility names (for example NousResearch Hermes Agent)
are intentionally not banned. This checks current source text, not Git history,
issues, binaries, private data, or arbitrary code/fixture identifiers.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCUMENT_EXTENSIONS = {".md", ".mdx", ".markdown", ".rst", ".adoc", ".txt"}
OWNER_PROJECT = re.compile(
    r"(?i)(?:"
    r"(?<![a-z0-9])yfc(?=$|[^a-z0-9])|"
    r"your[-_\s]*fitness[-_\s]*coach|"
    r"second[-_\s]*brain|secondbrain|"
    r"hermes[-_\s]*control[-_\s]*center|"
    r"mike(?:moore)?1337/hermes|"
    r"(?<![a-z0-9])(?:mango|манго)(?![a-z0-9])"
    r")"
)


class PublicDocumentationPrivacyTests(unittest.TestCase):
    def test_no_owner_project_references_in_current_docs(self):
        scanned = 0
        findings: list[str] = []
        for path in sorted(ROOT.rglob("*")):
            if not path.is_file() or path.is_symlink():
                continue
            if ".git" in path.parts or path.suffix.lower() not in DOCUMENT_EXTENSIONS:
                continue
            scanned += 1
            text = path.read_text(encoding="utf-8")
            for match in OWNER_PROJECT.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                findings.append(f"{path.relative_to(ROOT)}:{line} [{match.group(0)}]")
        self.assertGreaterEqual(scanned, 400)
        self.assertEqual([], findings)

    def test_third_party_compatibility_names_are_not_owner_projects(self):
        self.assertIsNone(OWNER_PROJECT.search("NousResearch/hermes-agent"))
        self.assertIsNone(OWNER_PROJECT.search("Hermes Agent skill compatibility"))
        self.assertIsNotNone(OWNER_PROJECT.search("your-fitness-coach"))
        self.assertIsNotNone(OWNER_PROJECT.search("Second Brain"))
        self.assertIsNotNone(OWNER_PROJECT.search("Hermes Control Center"))


if __name__ == "__main__":
    unittest.main()
