#!/usr/bin/env python3
"""Issue #62: deterministic, offline accessibility fixture and evidence checks.

Not a browser, CSS layout engine, ARIA implementation or WCAG conformance evaluator.
"""
from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WCAG_LEVELS = {
    "1.1.1": "A", "1.3.1": "A", "1.4.1": "A",
    "1.4.3": "AA", "1.4.4": "AA", "1.4.10": "AA",
    "1.4.11": "AA", "2.1.1": "A", "2.1.2": "A",
    "2.2.2": "A", "2.3.1": "A", "2.4.3": "A",
    "2.4.7": "AA", "2.4.11": "AA", "2.4.12": "AAA",
    "2.5.3": "A", "2.5.7": "AA", "2.5.8": "AA",
    "3.3.1": "A", "3.3.2": "A", "3.3.3": "AA",
    "4.1.2": "A", "4.1.3": "AA",
}
STATUSES = {
    "PASS", "FAIL", "NOT_RUN", "BLOCKED", "NOT_APPLICABLE",
    "NEEDS_MANUAL_REVIEW", "INCONCLUSIVE",
}
METHODS = {"STATIC", "CONTRACT", "BROWSER", "KEYBOARD", "ASSISTIVE_TECH", "MANUAL"}
RUNTIME = {"BROWSER", "KEYBOARD", "ASSISTIVE_TECH", "MANUAL"}
SEVERITIES = {"BLOCKER", "HIGH", "MEDIUM", "LOW"}
FINDING_STATES = {
    "POTENTIAL", "CONFIRMED", "FIX_PROPOSED", "FIX_IMPLEMENTED",
    "RETEST_PASS", "RETEST_FAIL", "NOT_TESTED",
}
TEST_FIELDS = {
    "test_id", "source_requirement", "user_goal", "target_interface",
    "interaction", "guideline", "criterion", "level", "preconditions",
    "input", "expected", "oracle", "method", "environment",
    "technology", "evidence", "status", "severity", "remediation",
    "retest", "limitations",
}
FINDING_FIELDS = {
    "finding_id", "component", "user_flow", "source_requirement",
    "criterion", "applicability", "expected", "actual", "evidence",
    "method", "severity", "impact", "steps", "remediation",
    "retest_oracle", "status", "limitations",
}
HEX = re.compile(r"#[0-9a-fA-F]{6}\Z")


def _luminance(value: str) -> float:
    if not isinstance(value, str) or not HEX.fullmatch(value):
        raise ValueError("Explicit opaque #RRGGBB sRGB required; unknown alpha/background")
    channels = [int(value[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
              for c in channels]
    return sum(x * w for x, w in zip(linear, (0.2126, 0.7152, 0.0722)))


def contrast_ratio(foreground: str, background: str) -> float:
    """Contrast of known *opaque* final colors; never a rendered-element oracle."""
    a, b = sorted((_luminance(foreground), _luminance(background)), reverse=True)
    return (a + 0.05) / (b + 0.05)


def check_contrast(fg: str, bg: str, kind: str,
                   exception: str | None = None) -> dict:
    thresholds = {"normal_text": 4.5, "large_text": 3.0, "ui_component": 3.0}
    if kind not in thresholds:
        raise ValueError("Unknown contrast category")
    if exception is not None:
        applicable = {
            "normal_text": {"incidental", "inactive", "logo", "part_of_picture"},
            "large_text": {"incidental", "inactive", "logo", "part_of_picture"},
            "ui_component": {"inactive", "user_agent", "essential"},
        }
        if exception not in applicable[kind]:
            raise ValueError("Unsupported exception: requires criterion-specific justification")
        return {"status": "NOT_APPLICABLE", "reason": exception}
    ratio = contrast_ratio(fg, bg)
    return {"status": "PASS" if ratio >= thresholds[kind] else "FAIL",
            "ratio": ratio, "threshold": thresholds[kind],
            "source": "DECLARED_OPAQUE_SRGB_PAIR_ONLY"}


class FixtureParser(HTMLParser):
    """Narrow structural oracle for controlled HTML fixtures, not arbitrary DOM."""
    def __init__(self):
        super().__init__()
        self.ids: set[str] = set()
        self.duplicate_ids: set[str] = set()
        self.labels: dict[str, str] = {}
        self.fields: list[dict[str, str | None]] = []
        self.buttons: list[dict] = []
        self.references: list[tuple[str, str]] = []
        self.errors: set[str] = set()
        self.main_found = False
        self._label: str | None = None
        self._button: dict | None = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        ident = attrs.get("id")
        if ident:
            if ident in self.ids:
                self.duplicate_ids.add(ident)
            self.ids.add(ident)
        if tag == "main":
            self.main_found = True
        if tag == "label" and attrs.get("for"):
            self._label = attrs["for"]
            self.labels.setdefault(self._label, "")
        if tag in {"input", "select", "textarea"} and attrs.get("type") != "hidden":
            self.fields.append(attrs)
        if tag == "button":
            self._button = {"attrs": attrs, "text": ""}
            self.buttons.append(self._button)
        for name in ("aria-labelledby", "aria-describedby", "aria-errormessage",
                     "aria-controls"):
            for ref in (attrs.get(name) or "").split():
                self.references.append((name, ref))
        if ident and "error" in (attrs.get("class") or "").split():
            self.errors.add(ident)

    def handle_data(self, data):
        if self._label is not None:
            self.labels[self._label] += data
        if self._button is not None:
            self._button["text"] += data

    def handle_endtag(self, tag):
        if tag == "label":
            self._label = None
        if tag == "button":
            self._button = None


def audit_fixture(html: str) -> list[str]:
    """Only checks explicit, narrow structural properties in synthetic fixtures."""
    p = FixtureParser()
    p.feed(html)
    issues = set()
    if p.duplicate_ids:
        issues.add("DUPLICATE_ID")
    if not p.main_found:
        issues.add("MISSING_MAIN_LANDMARK")
    if any(ref not in p.ids for _, ref in p.references):
        issues.add("INVALID_ARIA_REFERENCE")
    for field in p.fields:
        ident = field.get("id")
        named = (bool((field.get("aria-label") or "").strip())
                 or bool(ident and p.labels.get(ident, "").strip())
                 or bool((field.get("aria-labelledby") or "").strip()
                         and all(ref in p.ids for ref in field["aria-labelledby"].split())))
        if not named:
            issues.add("MISSING_FORM_LABEL")
    for button in p.buttons:
        attrs = button["attrs"]
        named = (bool(button["text"].strip())
                 or bool((attrs.get("aria-label") or "").strip())
                 or bool((attrs.get("aria-labelledby") or "").strip()
                         and all(ref in p.ids for ref in attrs["aria-labelledby"].split())))
        if not named:
            issues.add("MISSING_ACCESSIBLE_NAME")
    field_descriptions = {
        ref for field in p.fields
        for key in ("aria-describedby", "aria-errormessage")
        for ref in (field.get(key) or "").split()
    }
    if p.errors - field_descriptions:
        issues.add("UNLINKED_FORM_ERROR")
    return sorted(issues)


def validate_test(test: object) -> list[str]:
    if not isinstance(test, dict) or not TEST_FIELDS <= test.keys():
        return ["INVALID_TEST_CONTRACT"]
    problems = set()
    for key in ("test_id", "source_requirement", "user_goal", "target_interface",
                "interaction", "guideline", "expected", "oracle", "remediation", "retest"):
        if not isinstance(test[key], str) or not test[key].strip():
            problems.add("INVALID_TEST_CONTRACT")
    if test["criterion"] not in WCAG_LEVELS:
        problems.add("UNKNOWN_CRITERION")
    elif test["level"] != WCAG_LEVELS[test["criterion"]]:
        problems.add("WRONG_CRITERION_LEVEL")
    if test["method"] not in METHODS or test["status"] not in STATUSES:
        problems.add("INVALID_TEST_STATUS_OR_METHOD")
    if test["severity"] not in SEVERITIES:
        problems.add("INVALID_SEVERITY")
    if test["status"] == "NOT_APPLICABLE" and not test["limitations"]:
        problems.add("MISSING_APPLICABILITY_REASON")
    if test["status"] == "PASS":
        evidence = test["evidence"]
        if (not isinstance(evidence, dict) or evidence.get("executed") is not True
                or not isinstance(evidence.get("observation"), str)
                or not evidence["observation"].strip()):
            problems.add("PASS_WITHOUT_EXECUTION")
        else:
            if evidence.get("method") != test["method"]:
                problems.add("EVIDENCE_METHOD_MISMATCH")
            if test["method"] in RUNTIME and (
                    not evidence.get("operator") or not evidence.get("environment")):
                problems.add("RUNTIME_NOT_VERIFIED")
            if test["method"] == "ASSISTIVE_TECH" and (
                    not test["technology"] or not evidence.get("technology")):
                problems.add("ASSISTIVE_TECH_NOT_IDENTIFIED")
    return sorted(problems)


def validate_finding(finding: object) -> list[str]:
    if not isinstance(finding, dict) or not FINDING_FIELDS <= finding.keys():
        return ["INVALID_FINDING"]
    errors = set()
    if finding["severity"] not in SEVERITIES or finding["status"] not in FINDING_STATES:
        errors.add("INVALID_FINDING")
    if not finding["remediation"] or not finding["retest_oracle"]:
        errors.add("MISSING_REMEDIATION")
    if finding["status"] in {"CONFIRMED", "RETEST_PASS"} and not finding["evidence"]:
        errors.add("UNSUPPORTED_FINDING_STATUS")
    if finding["status"] == "RETEST_PASS" and (
            not isinstance(finding["evidence"], dict)
            or finding["evidence"].get("retest_executed") is not True):
        errors.add("RETEST_NOT_EXECUTED")
    return sorted(errors)


def priority(blocks_core_flow: bool, accessible_alternative: bool,
             frequent: bool = False) -> str:
    if blocks_core_flow and not accessible_alternative:
        return "BLOCKER"
    if blocks_core_flow or (frequent and not accessible_alternative):
        return "HIGH"
    return "MEDIUM" if not accessible_alternative else "LOW"


def validate_report(report: object) -> list[str]:
    if not isinstance(report, dict) or not {"tests", "required_criteria",
                                         "assessment"} <= report.keys():
        return ["INVALID_REPORT"]
    if not isinstance(report["tests"], list) or not isinstance(report["required_criteria"], list):
        return ["INVALID_REPORT"]
    errors: set[str] = set()
    by_criterion = {test.get("criterion") for test in report["tests"]
                    if isinstance(test, dict)}
    if any(c not in WCAG_LEVELS for c in report["required_criteria"]):
        errors.add("UNKNOWN_REQUIRED_CRITERION")
    if set(report["required_criteria"]) - by_criterion:
        errors.add("MISSING_REQUIRED_CRITERION")
    for test in report["tests"]:
        errors.update(validate_test(test))
    # This small offline tool never has the scope or evidence of WCAG-EM.
    if report["assessment"] != {"status": "NOT_ASSESSED"}:
        errors.add("FALSE_WCAG_CONFORMANCE")
    return sorted(errors)


def reference_test() -> dict:
    return {
        "test_id": "A11Y-001", "source_requirement": "R-001",
        "user_goal": "Submit the record without a pointer",
        "target_interface": "Synthetic record form",
        "interaction": "Open, edit, validate, submit",
        "guideline": "WCAG 2.2", "criterion": "2.1.1", "level": "A",
        "preconditions": ["Form is open"], "input": {"amount": "12"},
        "expected": "Form can be submitted with keyboard",
        "oracle": "User completes form and sees confirmation",
        "method": "KEYBOARD", "environment": "NOT_TESTED",
        "technology": None, "evidence": None, "status": "NOT_RUN",
        "severity": "HIGH", "remediation": "Restore keyboard activation",
        "retest": "Repeat keyboard-only user journey", "limitations": "Needs real browser",
    }


def run_cases() -> dict:
    base = ROOT / "fixtures/accessibility"
    good = audit_fixture((base / "accessible.html").read_text(encoding="utf-8"))
    bad = audit_fixture((base / "inaccessible.html").read_text(encoding="utf-8"))
    colors = {
        "black_white": check_contrast("#000000", "#ffffff", "normal_text"),
        "boundary_fail": check_contrast("#777777", "#ffffff", "normal_text"),
        "boundary_pass": check_contrast("#767676", "#ffffff", "normal_text"),
    }
    ok = (not good and {"MISSING_FORM_LABEL", "MISSING_ACCESSIBLE_NAME",
          "UNLINKED_FORM_ERROR", "INVALID_ARIA_REFERENCE"} <= set(bad)
          and colors["black_white"]["status"] == "PASS"
          and colors["boundary_fail"]["status"] == "FAIL"
          and colors["boundary_pass"]["status"] == "PASS")
    return {"result": "PASS" if ok else "FAIL", "accessible": good,
            "inaccessible": bad, "color_pairs": colors,
            "browser": "NOT_TESTED", "keyboard": "NOT_TESTED",
            "assistive_technology": "NOT_TESTED",
            "wcag_conformance": "NOT_ASSESSED"}


if __name__ == "__main__":
    print(json.dumps(run_cases(), indent=2, ensure_ascii=False))
    raise SystemExit(0 if run_cases()["result"] == "PASS" else 1)

