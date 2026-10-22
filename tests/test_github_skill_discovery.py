"""Offline contract tests for pinned GitHub skill discovery (#199/#200)."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import github_skill_discovery as discovery  # noqa: E402


class GitHubSkillDiscoveryTests(unittest.TestCase):
    URL = "https://github.com/example/sample-skills"
    SHA = "a" * 40
    TREE = "b" * 40

    def setUp(self):
        self.calls = []

    def fetcher(self, owner, repo, resource, revision):
        self.calls.append((owner, repo, resource, revision))
        if resource == "commits":
            return {"sha": self.SHA, "commit": {"tree": {"sha": self.TREE}}}
        return {"sha": self.TREE, "truncated": False, "tree": [
            {"type": "blob", "path": "skills/backend/SKILL.md"},
            {"type": "blob", "path": "skills/design/SKILL.md"},
            {"type": "tree", "path": "skills/backend"},
            {"type": "blob", "path": "../secret/SKILL.md"},
            {"type": "blob", "path": "scripts/install.sh"},
        ]}

    def run_discovery(self, **kw):
        return discovery.discover("backend API", opt_in=True,
            allowed_sources=(self.URL+"@"+self.SHA,), fetch_json=self.fetcher, **kw)

    def test_no_flag_means_no_network_even_with_query(self):
        with patch.object(discovery, "_request", side_effect=AssertionError("NETWORK_CALLED")):
            result = discovery.discover("qa-strategy")
        self.assertEqual("NO_NETWORK", result["status"])
        self.assertEqual("FOUND_LOCAL", result["local_skill_coverage"]["coverage"])
        self.assertEqual("NOT_AUTHORIZED", result["installation"])

    def test_pinned_allowlist_yields_only_lexical_paths(self):
        result = self.run_discovery()
        self.assertEqual("REVIEW_ONLY", result["status"])
        self.assertEqual(1, len(result["candidates"]))
        self.assertEqual("skills/backend/SKILL.md", result["candidates"][0]["path"])
        self.assertEqual(self.SHA, result["candidates"][0]["revision"])
        self.assertEqual("NOT_VERIFIED", result["candidates"][0]["license"])
        self.assertEqual("NOT_DOWNLOADED", result["candidates"][0]["content"])
        self.assertEqual("NOT_RUN", result["remote_security_gate"])
        self.assertEqual("NOT_AUTHORIZED", result["installation"])
        self.assertEqual(2, len(self.calls))

    def test_optin_and_pin_required(self):
        source = self.URL+"@"+self.SHA
        for opt_in, allowed in ((False, (source,)), (True, ()), (True, (source,)*4)):
            with self.subTest(opt_in=opt_in, sources=allowed):
                result = discovery.discover("backend", opt_in=opt_in, allowed_sources=allowed,
                                            fetch_json=self.fetcher)
                self.assertEqual("REJECT", result["status"])
        self.assertEqual([], self.calls)

    def test_host_confusion_and_mutable_revision_fail_without_network(self):
        bad = [
            self.URL+"@main",
            "https://evil.example/owner/repo@"+self.SHA,
            "https://github.com.evil.test/example/repo@"+self.SHA,
            "https://github.com/owner/repo?x=1@"+self.SHA,
            "https://github.com/owner/repo#fragment@"+self.SHA,
            "https://github.com@evil.example/owner/repo@"+self.SHA,
            "http://github.com/owner/repo@"+self.SHA,
            "https://github.com/../repo@"+self.SHA,
            "https://github.com/owner/%2e%2e@"+self.SHA,
        ]
        for value in bad:
            with self.subTest(value=value):
                result = discovery.discover("backend", opt_in=True,
                                            allowed_sources=(value,), fetch_json=self.fetcher)
                self.assertEqual("REJECT", result["status"])
        self.assertEqual([], self.calls)

    def test_duplicate_source_rejected_case_insensitive(self):
        result = discovery.discover("backend", opt_in=True,
            allowed_sources=(self.URL+"@"+self.SHA,
                             self.URL.upper().replace("HTTPS://","https://").replace("GITHUB.COM","github.com")+"@"+self.SHA),
            fetch_json=self.fetcher)
        self.assertEqual("REJECT", result["status"])
        self.assertEqual([], self.calls)

    def test_commit_sha_mismatch_and_no_partial_results(self):
        def bad(owner, repo, kind, sha):
            if kind == "commits":
                return {"sha": "b"*40, "commit": {"tree": {"sha": self.TREE}}}
            self.fail("Tree must not be queried")
        out = discovery.discover("backend", opt_in=True, allowed_sources=(self.URL+"@"+self.SHA,),
                                 fetch_json=bad)
        self.assertEqual("REJECT", out["status"])
        self.assertEqual("REVISION_NOT_VERIFIED", out["reason"])
        self.assertEqual([], out["candidates"])

    def test_truncated_oversize_and_tree_sha_mismatch_fail_closed(self):
        def run_tree(value):
            def fetch(owner, repo, kind, sha):
                if kind == "commits":
                    return self.fetcher(owner, repo, kind, sha)
                return value
            return discovery.discover("backend", opt_in=True,
                allowed_sources=(self.URL+"@"+self.SHA,), fetch_json=fetch)
        for bad in [
            {"sha": self.TREE, "truncated": True, "tree": []},
            {"sha": self.TREE, "truncated": False, "tree": [{}] * (discovery.MAX_TREE_ENTRIES+1)},
            {"sha": "c"*40, "truncated": False, "tree": []},
        ]:
            with self.subTest(kind=str(bad.keys())):
                self.assertEqual("REJECT", run_tree(bad)["status"])

    def test_unknown_and_unmatched_paths_do_not_claim_missing_semantic_capability(self):
        out = discovery.discover("mysterious-zqxw", opt_in=True,
            allowed_sources=(self.URL+"@"+self.SHA,), fetch_json=self.fetcher)
        self.assertEqual("REVIEW_ONLY", out["status"])
        self.assertEqual([], out["candidates"])
        self.assertEqual("LEXICAL_ONLY_NOT_SEMANTIC", out["query_match"])

    def test_fetch_errors_never_install_or_return_partial_candidates(self):
        def bad(*args):
            raise OSError("simulated unavailable network")
        out = discovery.discover("backend", opt_in=True,
            allowed_sources=(self.URL+"@"+self.SHA,), fetch_json=bad)
        self.assertEqual("REJECT", out["status"])
        self.assertEqual("GITHUB_METADATA_UNAVAILABLE", out["reason"])
        self.assertFalse(out["skills_content_downloaded"])
        self.assertEqual("NOT_AUTHORIZED", out["installation"])

    def test_http_client_fixed_host_no_auth_no_redirect(self):
        calls = []
        class Response:
            status = 302
            def getheader(self, key):
                return None
        class Conn:
            def __init__(self, host, timeout, context):
                calls.append(("init", host, timeout))
            def request(self, method, target, headers):
                calls.append(("request", method, target, headers))
            def getresponse(self):
                return Response()
            def close(self):
                calls.append(("close",))
        with patch.object(discovery.http.client, "HTTPSConnection", Conn):
            with self.assertRaisesRegex(discovery.DiscoveryError, "GITHUB_METADATA_UNAVAILABLE"):
                discovery._request("example", "repo", "commits", self.SHA)
        self.assertEqual("api.github.com", calls[0][1])
        self.assertEqual("GET", calls[1][1])
        self.assertEqual("/repos/example/repo/commits/"+self.SHA, calls[1][2])
        self.assertFalse(any("authorization" in k.lower() for k in calls[1][3]))
        self.assertEqual(("close",), calls[-1])


if __name__ == "__main__":
    unittest.main()
