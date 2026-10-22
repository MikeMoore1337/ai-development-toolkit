"""Offline, cross-platform tests of personal MCP opt-in public Skill metadata discovery."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "mcp"))
import adt_discovery as discovery
from adt_mcp import Toolkit, process


class DiscoveryContractTests(unittest.TestCase):
    SHA = "a" * 40
    TREE = "b" * 40
    URL = "https://github.com/example/approved-skills@" + SHA

    def setUp(self):
        self.calls: list[tuple] = []

    def fetch(self, owner, repo, resource, sha):
        self.calls.append((owner, repo, resource, sha))
        if resource == "git/commits":
            return {"sha": self.SHA, "tree": {"sha": self.TREE}}
        return {"sha": self.TREE, "truncated": False, "tree": [
            {"path": ".agents/skills/qa-strategy/SKILL.md", "type": "blob", "mode": "100644"},
            {"path": ".agents/skills/ui-design/SKILL.md", "type": "blob", "mode": "100644"},
            {"path": "../private/qa/SKILL.md", "type": "blob", "mode": "100644"},
            {"path": ".agents/skills/qa-shadow/SKILL.md", "type": "blob", "mode": "120000"},
            {"path": "scripts/install.sh", "type": "blob", "mode": "100755"},
        ]}

    def test_no_explicit_consent_never_calls_network(self):
        with patch.object(discovery, "_get", side_effect=AssertionError("NETWORK")):
            out = discovery.discover("qa", False, None)
        self.assertEqual(out["status"], "NO_NETWORK")
        self.assertEqual(out["installation"], "NOT_AUTHORIZED")
        self.assertEqual(out["candidates"], [])
        self.assertFalse(out["content_downloaded"])

    def test_pinned_consented_public_path_only(self):
        out = discovery.discover("QA", True, [self.URL], self.fetch)
        self.assertEqual(out["status"], "REVIEW_ONLY")
        self.assertEqual(2, len(self.calls))
        self.assertEqual(self.calls[0][2:], ("git/commits", self.SHA))
        self.assertEqual(self.calls[1][2:], ("git/trees", self.TREE))
        self.assertEqual([x["path"] for x in out["candidates"]],
                         [".agents/skills/qa-strategy/SKILL.md"])
        self.assertEqual(out["candidates"][0]["revision"], self.SHA)
        self.assertEqual(out["candidates"][0]["license"], "NOT_VERIFIED")
        self.assertEqual(out["candidates"][0]["content"], "NOT_DOWNLOADED")
        self.assertEqual(out["security_gate"], "NOT_RUN")
        self.assertEqual(out["installation"], "NOT_AUTHORIZED")

    def test_explicit_consent_and_allowlist_required(self):
        for consent, repos in ((False, [self.URL]), ("true", [self.URL]),
                              (True, None), (True, []), (True, [self.URL] * 4),
                              (1, [self.URL])):
            with self.subTest(consent=consent, repos=repos):
                self.assertEqual("REJECT", discovery.discover(
                    "qa", consent, repos, self.fetch)["status"])
        self.assertEqual(self.calls, [])

    def test_invalid_redirectable_or_mutable_url_refused_before_network(self):
        bad = [
            "https://github.com/example/approved-skills@main",
            "https://github.com/example/approved-skills",
            "https://github.com.evil.invalid/example/repo@" + self.SHA,
            "https://github.com@example.org/example/repo@" + self.SHA,
            "https://github.com/example/repo?token=abc@" + self.SHA,
            "https://github.com/example/repo#fragment@" + self.SHA,
            "http://github.com/example/repo@" + self.SHA,
            "https://github.com/../secret@" + self.SHA,
            "https://github.com/owner/%2e%2e@" + self.SHA,
        ]
        for url in bad:
            with self.subTest(url=url):
                out = discovery.discover("qa", True, [url], self.fetch)
                self.assertEqual(out["status"], "REJECT")
        self.assertEqual(self.calls, [])

    def test_duplicate_sources_refused_before_network(self):
        out = discovery.discover("qa", True, [self.URL, self.URL], self.fetch)
        self.assertEqual(out["reason"], "DUPLICATE_REPOSITORY")
        self.assertEqual(self.calls, [])

    def test_wrong_commit_or_untrusted_tree_fail_closed(self):
        def mismatch(owner, repo, kind, sha):
            if kind == "git/commits":
                return {"sha": "c" * 40, "tree": {"sha": self.TREE}}
            self.fail("Tree lookup after invalid pin")
        out = discovery.discover("qa", True, [self.URL], mismatch)
        self.assertEqual(out["status"], "REJECT")
        self.assertEqual(out["reason"], "COMMIT_SHA_NOT_VERIFIED")
        for blob in (
            {"sha": self.TREE, "truncated": True, "tree": []},
            {"sha": "d" * 40, "truncated": False, "tree": []},
            {"sha": self.TREE, "truncated": False, "tree": [{}] * 5001},
        ):
            with self.subTest(tree=blob.get("truncated")):
                def altered(owner, repo, kind, sha):
                    return self.fetch(owner, repo, kind, sha) if kind == "git/commits" else blob
                out = discovery.discover("qa", True, [self.URL], altered)
                self.assertEqual(out["status"], "REJECT")
                self.assertEqual(out["candidates"], [])

    def test_network_error_cannot_return_partial_candidates(self):
        def failure(*args):
            raise OSError("network disconnected")
        out = discovery.discover("qa", True, [self.URL], failure)
        self.assertEqual(out["status"], "REJECT")
        self.assertEqual(out["reason"], "GITHUB_METADATA_UNAVAILABLE")
        self.assertFalse(out["content_downloaded"])

    def test_empty_path_matches_do_not_claim_semantic_absence(self):
        out = discovery.discover("unmatched-workflow-zzzzz", True, [self.URL], self.fetch)
        self.assertEqual(out["status"], "REVIEW_ONLY")
        self.assertEqual(out["matching"], "LEXICAL_ONLY_NOT_SEMANTIC")
        self.assertEqual(out["candidates"], [])

    def test_fixed_host_no_auth_and_no_redirect(self):
        calls = []
        class Response:
            status = 302
            def getheader(self, header):
                return None
        class Connection:
            def __init__(self, host, timeout, context):
                calls.append(("init", host, timeout))
            def request(self, method, path, headers):
                calls.append(("request", method, path, headers))
            def getresponse(self):
                return Response()
            def close(self):
                calls.append(("close",))
        with patch.object(discovery.http.client, "HTTPSConnection", Connection):
            with self.assertRaises(discovery.DiscoveryDenied):
                discovery._get("example", "repo", "git/commits", self.SHA)
        self.assertEqual(calls[0][1], "api.github.com")
        self.assertEqual(calls[1][1], "GET")
        self.assertNotIn("Authorization", calls[1][3])
        self.assertEqual(calls[-1], ("close",))


class MCPDiscoveryIntegrationTests(unittest.TestCase):
    SHA = "a" * 40
    TREE = "b" * 40
    URL = "https://github.com/example/approved-skills@" + SHA

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "MANIFEST.json").write_text(json.dumps({
            "package": "ai-development-toolkit", "version": "5.5.3",
            "core_skills": ["qa-strategy"], "extension_skills": [],
            "core_roles": [], "profiles": {"general": ["qa-strategy"]},
        }), encoding="utf-8")
        folder = self.root / ".agents/skills/qa-strategy"
        folder.mkdir(parents=True)
        (folder / "SKILL.md").write_text("---\nname: qa-strategy\n---\nQA", encoding="utf-8")
        self.tk = Toolkit(self.root)

    def test_rpc_default_is_off_and_tool_is_discoverable(self):
        with patch.object(discovery, "_get", side_effect=AssertionError("NETWORK")):
            listing = process(self.tk, {"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
            specs = {x["name"]: x for x in listing["result"]["tools"]}
            self.assertIn("toolkit_discover_external_skill_candidates", specs)
            self.assertTrue(specs["toolkit_discover_external_skill_candidates"]["annotations"]["openWorldHint"])
            q = {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                 "params": {"name": "toolkit_discover_external_skill_candidates",
                            "arguments": {"query": "qa-strategy"}}}
            response = process(self.tk, q)
        result = response["result"]["structuredContent"]
        self.assertEqual(result["local_skill_coverage"]["coverage"], "FOUND_LOCAL")
        self.assertEqual(result["external_discovery"]["status"], "NO_NETWORK")
        self.assertEqual(result["external_skill_install"], "NOT_AUTHORIZED")

    def test_rpc_explicit_consent_and_mocked_pinned_source(self):
        def mock(owner, repo, resource, sha):
            if resource == "git/commits":
                return {"sha": self.SHA, "tree": {"sha": self.TREE}}
            return {"sha": self.TREE, "truncated": False, "tree": [
                {"type": "blob", "mode": "100644",
                 "path": ".agents/skills/qa-strategy/SKILL.md"}]}
        with patch.object(discovery, "_get", side_effect=mock):
            result = process(self.tk, {"jsonrpc": "2.0", "id": 17,
                "method": "tools/call", "params": {
                    "name": "toolkit_discover_external_skill_candidates",
                    "arguments": {"query": "qa", "consent": True,
                                  "allowed_repos": [self.URL]}}})
        body = result["result"]["structuredContent"]
        self.assertEqual(body["external_discovery"]["status"], "REVIEW_ONLY")
        self.assertEqual(body["security_gate"], "NOT_RUN")
        self.assertEqual(body["external_skill_install"], "NOT_AUTHORIZED")
        self.assertEqual(body["next_step"], "MANUAL_SOURCE_AND_LICENSE_VERIFICATION")


if __name__ == "__main__":
    unittest.main()
