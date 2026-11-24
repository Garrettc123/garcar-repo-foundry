#!/usr/bin/env python3
"""Evidence-first fleet completion matrix. No GitHub writes, releases or secrets."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime
import json
from pathlib import Path
import re

REPO = re.compile(r"^Garrettc123/[A-Za-z0-9_.-]+$")
EVIDENCE_KINDS = ("source_review", "test_run", "security_review", "runtime_receipt", "customer_flow")


def build_matrix(snapshot: dict, checked: dict | None = None) -> dict:
    """Treat all submitted evidence as unverified until independently checked."""
    rows = snapshot.get("repositories")
    if not isinstance(rows, list):
        raise ValueError("repositories array is required")
    if snapshot.get("repository_count") != len(rows):
        raise ValueError("inventory count mismatch; refuse incomplete evidence")
    observed = snapshot.get("observed_at_utc") or snapshot.get("observed_date")
    if not isinstance(observed, str):
        raise ValueError("inventory observation timestamp required")
    datetime.fromisoformat(observed.replace("Z", "+00:00"))
    checked = checked or {}
    if not isinstance(checked, dict):
        raise ValueError("checked evidence must be a JSON object")
    result: list[dict] = []
    seen: set[str] = set()
    for entry in rows:
        if not isinstance(entry, dict):
            raise ValueError("invalid repository entry")
        name = entry.get("repository")
        if not isinstance(name, str) or REPO.fullmatch(name) is None:
            raise ValueError("invalid repository name")
        if name in seen:
            raise ValueError(f"duplicate repository: {name}")
        seen.add(name)
        evidence = checked.get(name, {})
        if not isinstance(evidence, dict):
            raise ValueError(f"invalid evidence for {name}")
        links = {k: evidence[k] for k in EVIDENCE_KINDS
                 if isinstance(evidence.get(k), str) and evidence[k].startswith("https://github.com/")}
        # Links are pointers, not verified proof; never infer a live deployment.
        if entry.get("archived") is True:
            state = "ARCHIVED_NOT_CERTIFIED"
        elif not links:
            state = "UNINSPECTED"
        elif "test_run" not in links:
            state = "SOURCE_REVIEW_ONLY"
        elif "runtime_receipt" not in links:
            state = "CI_EVIDENCE_ONLY"
        else:
            state = "OPERATOR_REVIEW_REQUIRED"
        result.append({
            "repository": name, "candidate_lane": entry.get("candidate_lane", "unassessed"),
            "default_branch": entry.get("default_branch"), "status": state,
            "review_links": links, "production_ready": False,
            "note": evidence.get("note", "") if isinstance(evidence.get("note", ""), str) else "",
        })
    unexpected = sorted(set(checked) - seen)
    if unexpected:
        raise ValueError("evidence for repos not in snapshot: " + ",".join(unexpected[:5]))
    result.sort(key=lambda item: item["repository"].casefold())
    return {
        "snapshot_observed": observed,
        "snapshot_observed_precision": "date" if len(observed) == 10 else "datetime",
        "scope": "dated inventory; URL presence is NOT CI, runtime or sale verification",
        "repository_count": len(result),
        "status_counts": dict(Counter(row["status"] for row in result)),
        "production_ready_count_confirmed": 0,
        "repositories": result,
    }


def write_report(report: dict, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--evidence", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    snapshot = json.loads(args.snapshot.read_text(encoding="utf-8"))
    evidence = json.loads(args.evidence.read_text(encoding="utf-8")) if args.evidence else None
    write_report(build_matrix(snapshot, evidence), args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
