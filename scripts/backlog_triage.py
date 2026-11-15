#!/usr/bin/env python3
"""Read-only, evidence-first GitHub/Linear backlog inventory. Never merges or deploys.

Requires authenticated gh CLI only with --live. Otherwise reads a JSON snapshot.
Outputs remain local and must not be committed if they contain private issue data.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import sys

MAX_SEARCH_RESULTS = 1000
PAGE_SIZE = 100
OWNER = "Garrettc123"

SECURITY = re.compile(r"auto.?merge|approval.?bypass|auth.?bypass|unauth|credential|access.?control|hmac|token|secrets?|webhook|rbac|permissions?|invoic|payout|security|fail.closed|outbound|fraud", re.I)
REVENUE = re.compile(r"checkout|callback|fulfill|delivery|first.sale|stripe|crm|lead|revenue|payment|customer|sales", re.I)
CI = re.compile(r"ci\b|actions|startup.failure|runner|pytest|test|build|vercel 402", re.I)
INTEGRATION = re.compile(r"mesh|sync|heartbeat|telemetry|worker|deploy|integration|architecture|nwu", re.I)
CLOSED_LINEAR = {"done", "completed", "canceled", "cancelled", "duplicate", "archived"}
GITHUB_ITEM_RE = re.compile(r"^https://github[.]com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/(pull|issues)/[0-9]+$")


def classify(title: str) -> tuple[str, str]:
    if SECURITY.search(title):
        return "P0_REVIEW_SECURITY", "security, authorization or money-movement controls"
    if REVENUE.search(title):
        return "P1_REVENUE", "customer acquisition, payment or fulfillment"
    if CI.search(title):
        return "P1_CI", "test execution or deployment evidence"
    if INTEGRATION.search(title):
        return "P2_INTEGRATION", "integration or observability"
    return "P3_OTHER", "needs technical triage"


def fetch_github(query: str, runner=subprocess.run) -> dict:
    """Search all owner repositories reachable by the gh identity, with pagination."""
    rows = []
    total = None
    incomplete = False
    for page in range(1, 12):
        cmd = ["gh", "api", "-X", "GET", "search/issues",
               "-f", f"q={query}", "-f", f"per_page={PAGE_SIZE}",
               "-f", f"page={page}"]
        try:
            response = runner(cmd, capture_output=True, text=True, timeout=45, check=True)
        except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            raise RuntimeError(f"GitHub query failed (page {page}): {type(exc).__name__}") from exc
        try:
            data = json.loads(response.stdout)
            count = data["total_count"]
            items = data["items"]
            if type(count) is not int or not isinstance(items, list):
                raise ValueError("unexpected GitHub search shape")
        except (ValueError, KeyError, TypeError) as exc:
            raise RuntimeError(f"Unusable GitHub search response (page {page})") from exc
        if total is None:
            total = count
        elif count != total:
            incomplete = True  # results changed during paging
        incomplete = incomplete or bool(data.get("incomplete_results"))
        rows.extend(items)
        if len(items) < PAGE_SIZE or len(rows) >= min(count, MAX_SEARCH_RESULTS):
            break
    dedup = {v.get("html_url", ""): v for v in rows if isinstance(v, dict) and v.get("html_url")}
    return {"total_count": total or 0, "items": list(dedup.values()),
            "complete": not incomplete and total is not None
                        and total <= MAX_SEARCH_RESULTS and len(dedup) == total,
            "source": "GitHub authenticated accessible-repositories search"}


def normalized_items(data: dict, kind: str) -> list[dict]:
    rows = []
    for item in data.get("items", []):
        if not isinstance(item, dict):
            continue
        url = item.get("html_url")
        title = item.get("title")
        if not isinstance(url, str) or not GITHUB_ITEM_RE.fullmatch(url):
            continue
        if not isinstance(title, str) or not title.strip():
            continue
        priority, reason = classify(title)
        rows.append({"kind": kind, "url": url, "title": " ".join(title.split()),
                     "priority": priority, "reason": reason,
                     "updated_at": item.get("updated_at"),
                     "repository": url.split("/")[4] if len(url.split("/")) > 4 else None,
                     "status": "OPEN_UNVERIFIED_TESTS"})
    return rows


def normalize_linear(issues: list[dict]) -> list[dict]:
    rows = []
    for x in issues:
        if not isinstance(x, dict):
            continue
        state = x.get("status") or x.get("statusType") or ""
        if isinstance(state, dict):
            state = state.get("name", "")
        if str(state).strip().lower() in CLOSED_LINEAR:
            continue
        title = x.get("title")
        url = x.get("url")
        if not isinstance(title, str) or not isinstance(url, str) or not url.startswith("https://linear.app/"):
            continue
        priority, reason = classify(title)
        rows.append({"kind": "linear_issue", "url": url, "title": title,
                     "priority": priority, "reason": reason,
                     "updated_at": x.get("updatedAt"), "status": str(state) or "UNKNOWN",
                     "repository": None})
    return rows


def build_snapshot(prs: dict, issues: dict, linear: list[dict] | None = None) -> dict:
    if not isinstance(prs, dict) or not isinstance(issues, dict):
        raise ValueError("Both GitHub search responses are required")
    def complete(part):
        n = part.get("total_count")
        items = part.get("items")
        return (part.get("complete") is True and type(n) is int and
                isinstance(items, list) and all(isinstance(i, dict) and GITHUB_ITEM_RE.fullmatch(str(i.get("html_url", ""))) for i in items) and len({i["html_url"] for i in items}) == n)
    coverage = "COMPLETE_FOR_ACCESSIBLE_GITHUB_REPOS" if complete(prs) and complete(issues) else "PARTIAL"
    rows = normalized_items(prs, "github_pr") + normalized_items(issues, "github_issue") + normalize_linear(linear or [])
    order = {"P0_REVIEW_SECURITY": 0, "P1_REVENUE": 1, "P1_CI": 2,
             "P2_INTEGRATION": 3, "P3_OTHER": 4}
    rows.sort(key=lambda r: (order[r["priority"]], r["kind"], r["url"]))
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "coverage": coverage, "repository_scope": "GitHub repositories accessible to configured gh identity",
        "github_prs_reported": prs.get("total_count"), "github_prs_observed": len(normalized_items(prs, "github_pr")),
        "github_issues_reported": issues.get("total_count"), "github_issues_observed": len(normalized_items(issues, "github_issue")),
        "linear_issues_observed_open": len(normalize_linear(linear or [])),
        "linear_scope": "supplied snapshot only" if linear is not None else "not examined",
        "no_write_actions": True, "no_merges_or_deployments": True, "items": rows,
    }


def make_markdown(report: dict) -> str:
    lines = ["# Garcar evidence-first backlog", "",
             f"Generated (UTC): {report['generated_at_utc']}",
             f"Coverage: **{report['coverage']}**; scope: {report['repository_scope']}",
             f"GitHub PRs: {report['github_prs_observed']} observed / {report['github_prs_reported']} reported",
             f"GitHub issues: {report['github_issues_observed']} observed / {report['github_issues_reported']} reported",
             f"Linear active/backlog records: {report['linear_issues_observed_open']} in supplied snapshot", "",
             "This is a **read-only triage report**, not test, merge, deployment, sale or closure evidence.",
             "No auto-merge, issue auto-close, payments, outreach, or production mutations.", "",
             "## Highest priority", ""]
    for item in report["items"][:40]:
        lines.append(f"- **{item['priority']}** [{item['title'].replace('[', '(').replace(']', ')')}]({item['url']}) — {item['status']}")
    if len(report["items"]) > 40:
        lines.extend(["", f"{len(report['items']) - 40} further items remain in backlog.json."])
    lines.append("")
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    inp = parser.add_mutually_exclusive_group(required=True)
    inp.add_argument("--live", action="store_true", help="Read via authenticated gh CLI")
    inp.add_argument("--snapshot", type=Path, help="Offline JSON with github_prs and github_issues")
    parser.add_argument("--linear-json", type=Path, help="Optional Linear connector JSON export")
    parser.add_argument("--output", type=Path, default=Path(".backlog-evidence"))
    args = parser.parse_args(argv)
    try:
        if args.live:
            prs = fetch_github(f"user:{OWNER} is:pr is:open")
            issues = fetch_github(f"user:{OWNER} is:issue is:open")
        else:
            snapshot = json.loads(args.snapshot.read_text(encoding="utf-8"))
            prs, issues = snapshot["github_prs"], snapshot["github_issues"]
        linear = None
        if args.linear_json:
            raw = json.loads(args.linear_json.read_text(encoding="utf-8"))
            linear = raw["issues"] if isinstance(raw, dict) else raw
        report = build_snapshot(prs, issues, linear)
    except (OSError, RuntimeError, ValueError, TypeError, KeyError) as exc:
        print(f"BLOCKED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "backlog.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (args.output / "TRIAGE.md").write_text(make_markdown(report), encoding="utf-8")
    print(f"{report['coverage']}: {len(report['items'])} records; outputs in {args.output}")
    return 0 if report["coverage"] != "PARTIAL" else 2


if __name__ == "__main__":
    raise SystemExit(main())
