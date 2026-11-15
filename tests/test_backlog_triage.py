"""Offline regression tests for read-only backlog inventory. No API credentials required."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import subprocess

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("backlog_triage", ROOT / "scripts" / "backlog_triage.py")
bot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bot)


def item(number, *, title="safe PR", kind="pull"):
    return {"html_url": f"https://github.com/Garrettc123/repo/{kind}/{number}",
            "title": title, "updated_at": "2026-11-14T00:00:00Z"}


def result(rows, complete=True):
    return {"total_count": len(rows), "items": rows, "complete": complete}


class BacklogTriageTests(unittest.TestCase):
    def test_priority_and_safety_flags(self):
        self.assertEqual(bot.classify("remove auto merge approval bypass")[0], "P0_REVIEW_SECURITY")
        self.assertEqual(bot.classify("fix checkout paid delivery")[0], "P1_REVENUE")
        self.assertEqual(bot.classify("restore CI runner")[0], "P1_CI")
        self.assertEqual(bot.classify("mesh signed heartbeat")[0], "P2_INTEGRATION")

    def test_full_snapshot_is_scoped_not_automatically_merged(self):
        prs = result([item(1, title="patch auth bypass")])
        issues = result([item(9, title="fix CI", kind="issues")])
        linear = [
            {"status": "Done", "title": "Finished work", "url": "https://linear.app/team/issue/GAR-1"},
            {"status": "In Progress", "title": "Verify webhook", "url": "https://linear.app/team/issue/GAR-2"},
        ]
        r = bot.build_snapshot(prs, issues, linear)
        self.assertEqual(r["coverage"], "COMPLETE_FOR_ACCESSIBLE_GITHUB_REPOS")
        self.assertEqual(len(r["items"]), 3)
        self.assertTrue(r["no_write_actions"])
        self.assertTrue(r["no_merges_or_deployments"])
        self.assertEqual(r["linear_issues_observed_open"], 1)

    def test_partial_results_never_claim_full_coverage(self):
        r = bot.build_snapshot({"total_count": 146, "items": [item(1)], "complete": True},
                               result([item(7, kind="issues")]))
        self.assertEqual(r["coverage"], "PARTIAL")

    def test_duplicate_urls_fail_full_coverage(self):
        r = bot.build_snapshot({"total_count": 2, "items": [item(1), item(1)], "complete": True},
                               result([]))
        self.assertEqual(r["coverage"], "PARTIAL")

    def test_gh_pagination_uses_read_only_get_and_detects_total(self):
        calls = []
        def fake(cmd, **kwargs):
            calls.append(cmd)
            page = int(cmd[-1].split("=")[-1])
            rows = [item(n) for n in range(1, 101)] if page == 1 else [item(101)]
            payload = {"total_count": 101, "items": rows, "incomplete_results": False}
            return subprocess.CompletedProcess(cmd, 0, stdout=json.dumps(payload))
        r = bot.fetch_github("user:Garrettc123 is:pr is:open", runner=fake)
        self.assertEqual(len(calls), 2)
        self.assertEqual(r["total_count"], 101)
        self.assertTrue(r["complete"])
        for cmd in calls:
            self.assertEqual(cmd[:5], ["gh", "api", "-X", "GET", "search/issues"])

    def test_failed_github_query_blocks_without_synthetic_status(self):
        def fails(cmd, **kwargs):
            raise subprocess.CalledProcessError(1, cmd)
        with self.assertRaises(RuntimeError):
            bot.fetch_github("test", runner=fails)

    def test_offline_cli_writes_only_requested_evidence(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            fixture = root / "snapshot.json"
            fixture.write_text(json.dumps({
                "github_prs": result([item(1)]),
                "github_issues": result([item(3, kind="issues")])
            }), encoding="utf-8")
            output = root / "evidence"
            rc = bot.main(["--snapshot", str(fixture), "--output", str(output)])
            self.assertEqual(rc, 0)
            report = json.loads((output / "backlog.json").read_text())
            self.assertEqual(report["github_prs_reported"], 1)
            self.assertIn("read-only", (output / "TRIAGE.md").read_text().lower())

    def test_partial_cli_exits_nonzero_even_after_evidence_written(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            fixture = root / "partial.json"
            fixture.write_text(json.dumps({
                "github_prs": {"total_count": 10, "items": [item(1)], "complete": False},
                "github_issues": result([]),
            }), encoding="utf-8")
            rc = bot.main(["--snapshot", str(fixture), "--output", str(root / "out")])
            self.assertEqual(rc, 2)
            self.assertTrue((root / "out" / "backlog.json").exists())


if __name__ == "__main__":
    unittest.main()
