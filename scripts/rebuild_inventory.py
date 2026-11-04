#!/usr/bin/env python3
"""Rebuild the fleet inventory from live GitHub data (requires authenticated gh CLI).

Usage:
    python3 scripts/rebuild_inventory.py

Outputs:
    inventory/repos.json       full fleet rows (source of truth for stamp.py)
    inventory/repos.csv        flat csv view
    inventory/FLEET.md         human-readable fleet snapshot
    inventory/CLASSIFICATION.md refreshed counts
"""
from __future__ import annotations

import csv
import json
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INV = ROOT / "inventory"

CONTROL_PAT = (  # matched against NAME only — orchestration layer stays tight
    "hub", "control-plane", "sync-core", "foundry", "orchestrator",
    "rhns-core", "-architecture", "production", "sovereign", "command-center",
    "enterprise-os-core", "garcar-base",
)
CASH_PAT = (  # matched against name + description — touches money paths
    "stripe", "checkout", "storefront", "fulfill", "payment", "lead",
    "invoice", "monetiz",
)
CODE_MIN_KB = 150      # real source beyond a stub
EMPTY_MAX_KB = 10      # no language, almost no bytes


def gh_repos() -> list[dict]:
    out = subprocess.run(
        ["gh", "repo", "list", "Garrettc123", "--limit", "500",
         "--json", "name,description,isPrivate,primaryLanguage,diskUsage,updatedAt,isEmpty"],
        capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def classify(r: dict) -> str:
    name = (r["name"] or "").lower()
    desc = (r.get("description") or "").lower()
    lang = (r.get("primaryLanguage") or {}).get("name")
    kb = r.get("diskUsage") or 0

    if any(p in f"{name} {desc}" for p in CASH_PAT):
        return "CASH"
    if any(p in name for p in CONTROL_PAT):
        return "CONTROL"
    if lang and kb >= CODE_MIN_KB:
        return "CODE"
    if lang or kb > EMPTY_MAX_KB:
        return "STUB"
    return "EMPTY"


def main() -> None:
    INV.mkdir(exist_ok=True)
    repos = gh_repos()
    rows = []
    for r in sorted(repos, key=lambda x: x["name"].lower()):
        rows.append({
            "name": r["name"],
            "tier": classify(r),
            "private": bool(r.get("isPrivate")),
            "lang": (r.get("primaryLanguage") or {}).get("name"),
            "size": r.get("diskUsage") or 0,
            "desc": r.get("description") or "",
            "updated": (r.get("updatedAt") or "")[:10],
        })

    counts: dict[str, int] = {}
    for row in rows:
        counts[row["tier"]] = counts.get(row["tier"], 0) + 1

    today = time.strftime("%Y-%m-%d")
    (INV / "repos.json").write_text(json.dumps(rows, indent=1))
    with open(INV / "repos.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["name", "tier", "visibility", "lang", "size"])
        for row in rows:
            w.writerow([row["name"], row["tier"], "private" if row["private"] else "public",
                        row["lang"] or "-", row["size"]])

    fleet = [f"# Fleet snapshot ({today})", "",
             f"Source: live GitHub API (`gh repo list Garrettc123`), {len(rows)} unique repos.", "",
             "| Tier | Count | Meaning |", "|---|---|---|",
             f"| CASH | {counts.get('CASH', 0)} | Touches Stripe, leads, fulfillment, storefront |",
             f"| CONTROL | {counts.get('CONTROL', 0)} | Hub, base contract, RHNS, production stack |",
             f"| CODE | {counts.get('CODE', 0)} | Has real source beyond a stub |",
             f"| STUB | {counts.get('STUB', 0)} | Thin repo, usually README + placeholder |",
             f"| EMPTY | {counts.get('EMPTY', 0)} | No language, almost no bytes |",
             f"| **Total** | **{len(rows)}** | Owned by `Garrettc123` |", "",
             "Source of truth: `inventory/repos.json` (used by `scripts/stamp.py`).", ""]
    (INV / "FLEET.md").write_text("\n".join(fleet))

    cls = [f"# Classification rules", "",
           f"Applied {today} against `gh repo list Garrettc123` ({len(rows)} unique names).", "",
           "Rules (in precedence order):",
           "1. **CONTROL** — name/description matches orchestration patterns (hub, control plane, sync core, foundry, orchestrator, RHNS core, architecture, production, sovereign, command center).",
           "2. **CASH** — name/description touches Stripe, checkout, storefront, fulfillment, payment, lead, revenue, monetization, invoice, subscription, CRM, deal, audit.",
           "3. **CODE** — has a primary language and >= 150 KB on disk.",
           "4. **STUB** — has a language or more than 10 KB, but below the CODE bar.",
           "5. **EMPTY** — no language and <= 10 KB.", "",
           f"CASH {counts.get('CASH', 0)} · CONTROL {counts.get('CONTROL', 0)} · CODE {counts.get('CODE', 0)} · STUB {counts.get('STUB', 0)} · EMPTY {counts.get('EMPTY', 0)}.", ""]
    (INV / "CLASSIFICATION.md").write_text("\n".join(cls))

    print(f"inventory rebuilt: {len(rows)} repos")
    print(f"CASH {counts.get('CASH', 0)} · CONTROL {counts.get('CONTROL', 0)} · CODE {counts.get('CODE', 0)} · STUB {counts.get('STUB', 0)} · EMPTY {counts.get('EMPTY', 0)}")


if __name__ == "__main__":
    main()
