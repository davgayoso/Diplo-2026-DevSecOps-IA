"""Policy regression tests, independent of Docker, Trivy and live CVE databases."""

import copy
import importlib.util
import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("trivy_policy_gate", ROOT / "scripts/check_trivy.py")
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)


class TrivyPolicyTests(unittest.TestCase):
    def setUp(self):
        self.policy = json.loads((ROOT / "security/trivy-exceptions.json").read_text())
        self.today = date.fromisoformat(self.policy["approved_on"])
        self.report = {
            "SchemaVersion": 2,
            "ArtifactType": "container_image",
            "Metadata": {
                "OS": {"Family": "debian", "Name": "13.6"},
                "ImageConfig": {"architecture": "amd64"},
            },
            "Results": [
                {"Class": "os-pkgs", "Type": "debian", "Vulnerabilities": []},
                {"Class": "lang-pkgs", "Type": "python-pkg"},
            ],
        }
        self.findings = self.report["Results"][0]["Vulnerabilities"]
        for entry in self.policy["exceptions"]:
            self.findings.append(
                {
                    "VulnerabilityID": entry["id"],
                    "PkgName": entry["package"],
                    "InstalledVersion": entry["version"],
                    "Severity": entry["severity"],
                }
            )

    def evaluate(self):
        return gate.evaluate(self.report, self.policy, self.today)

    def test_current_baseline_is_accepted(self):
        total, accepted, blocked = self.evaluate()
        self.assertEqual((total, len(accepted), len(blocked)), (16, 16, 0))

    def test_no_exceptions_blocks_all_high_and_critical(self):
        self.policy["exceptions"] = []
        self.assertEqual(len(self.evaluate()[2]), 16)

    def test_new_high_or_critical_blocks_even_without_fix(self):
        for severity in ("HIGH", "CRITICAL"):
            with self.subTest(severity=severity):
                self.findings.append(
                    {**self.findings[0], "VulnerabilityID": "CVE-2099-99999", "Severity": severity}
                )
                self.assertEqual(len(self.evaluate()[2]), 1)
                self.findings.pop()

    def test_fixed_version_overrides_each_exception(self):
        for finding in self.findings:
            with self.subTest(cve=finding["VulnerabilityID"], package=finding["PkgName"]):
                finding["FixedVersion"] = "test-patched-version"
                self.assertEqual(len(self.evaluate()[2]), 1)
                del finding["FixedVersion"]

    def test_expiry_blocks_on_boundary(self):
        self.today = date.fromisoformat(self.policy["expires_on"])
        self.assertEqual(len(self.evaluate()[2]), 16)

    def test_exception_cannot_apply_before_approval(self):
        self.today = date(2026, 1, 1)
        self.assertEqual(len(self.evaluate()[2]), 16)

    def test_changed_package_or_version_or_severity_blocks(self):
        for field, value in (
            ("PkgName", "other-package"),
            ("InstalledVersion", "9.9"),
            ("Severity", "CRITICAL"),
        ):
            with self.subTest(field=field):
                previous = self.findings[0][field]
                self.findings[0][field] = value
                self.assertEqual(len(self.evaluate()[2]), 1)
                self.findings[0][field] = previous

    def test_different_architecture_blocks(self):
        self.report["Metadata"]["ImageConfig"]["architecture"] = "arm64"
        self.assertEqual(len(self.evaluate()[2]), 16)

    def test_different_os_version_blocks(self):
        self.report["Metadata"]["OS"]["Name"] = "14"
        self.assertEqual(len(self.evaluate()[2]), 16)

    def test_python_never_inherits_os_exceptions(self):
        self.report["Results"][1]["Vulnerabilities"] = [copy.deepcopy(self.findings[0])]
        self.assertEqual(len(self.evaluate()[2]), 1)

    def test_lower_severity_is_counted_not_blocked(self):
        self.findings.append({**self.findings[0], "Severity": "MEDIUM"})
        self.assertEqual(self.evaluate()[0], 17)
        self.assertEqual(len(self.evaluate()[2]), 0)

    def test_clean_report_passes_after_exception_expiry(self):
        self.findings.clear()
        self.today = date(2030, 1, 1)
        self.assertEqual(self.evaluate(), (0, [], []))

    def test_missing_python_scan_fails_closed(self):
        self.report["Results"].pop()
        with self.assertRaises(ValueError):
            self.evaluate()

    def test_empty_results_fail_closed(self):
        self.report["Results"] = []
        with self.assertRaises(ValueError):
            self.evaluate()

    def test_unsupported_schema_fails_closed(self):
        self.report["SchemaVersion"] = 999
        with self.assertRaises(ValueError):
            self.evaluate()

    def test_malformed_findings_fail_closed(self):
        self.report["Results"][0]["Vulnerabilities"] = {}
        with self.assertRaises(ValueError):
            self.evaluate()

    def test_suppressed_findings_fail_closed(self):
        self.report["Results"][0]["ExperimentalModifiedFindings"] = [{"Status": "ignored"}]
        with self.assertRaises(ValueError):
            self.evaluate()

    def test_eol_os_fails_closed(self):
        self.report["Metadata"]["OS"]["EOSL"] = True
        with self.assertRaises(ValueError):
            self.evaluate()

    def test_duplicate_policy_rule_fails_closed(self):
        self.policy["exceptions"].append(copy.deepcopy(self.policy["exceptions"][0]))
        with self.assertRaises(ValueError):
            self.evaluate()

    def test_missing_reason_fails_closed(self):
        self.policy["exceptions"][0]["reason"] = ""
        with self.assertRaises(ValueError):
            self.evaluate()

    def test_cli_missing_and_invalid_files_return_error(self):
        with TemporaryDirectory() as directory, redirect_stderr(io.StringIO()):
            path = Path(directory) / "invalid.json"
            self.assertEqual(gate.main([str(path)]), 2)
            path.write_text("not json")
            self.assertEqual(gate.main([str(path)]), 2)

    def test_cli_exit_codes(self):
        with TemporaryDirectory() as directory, redirect_stdout(io.StringIO()):
            report_path = Path(directory) / "report.json"
            policy_path = Path(directory) / "policy.json"
            # Dates are kept valid only in this temporary fixture, never in the real policy.
            self.policy["approved_on"] = "2000-01-01"
            self.policy["expires_on"] = "9999-01-01"
            policy_path.write_text(json.dumps(self.policy))
            report_path.write_text(json.dumps(self.report))
            args = [str(report_path), "--policy", str(policy_path)]
            self.assertEqual(gate.main(args), 0)
            self.findings[0]["FixedVersion"] = "patched"
            report_path.write_text(json.dumps(self.report))
            self.assertEqual(gate.main(args), 1)


if __name__ == "__main__":
    unittest.main()
