#!/usr/bin/env python3
"""Generate a kernel stamp for one owned repo. Does not talk to GitHub."""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KERNEL = ROOT / "kernel"
INVENTORY = ROOT / "inventory" / "repos.json"
OUT = ROOT / "out"

PROTECTED_HINTS = (
    "garcar-emergency-payments",
    "garcar-payments",
    "Garrettc123.github.io",
    "systems-master-hub",
    "garcar-enterprise-production",
)


def load_inventory():
    if not INVENTORY.exists():
        return []
    return json.loads(INVENTORY.read_text())


def classify(name: str, inventory: list[dict]) -> dict:
    for row in inventory:
        if row["name"] == name:
            return row
    return {"name": name, "tier": "STUB", "private": False, "lang": None, "size": 0, "desc": ""}


def render_readme(row: dict) -> str:
    name = row["name"]
    tier = row.get("tier") or "STUB"
    desc = row.get("desc") or "Garcar Enterprise satellite."
    return f"""# {name}\n\n{desc}\n\n**Foundry tier:** `{tier}`\n"""


def stamp(name: str, dry_run: bool, force: bool) -> Path:
    inventory = load_inventory()
    row = classify(name, inventory)
    dest = OUT / name
    if name in PROTECTED_HINTS and not force:
        raise SystemExit(f"refusing to stamp protected repo {name} without --force")
    files = {
        "app.py": (KERNEL / "app.py").read_text(),
        "requirements.txt": (KERNEL / "requirements.txt").read_text(),
        "Dockerfile": (KERNEL / "Dockerfile").read_text().replace(
            "GARCAR_SYSTEM_ID=garcar-repo-foundry", f"GARCAR_SYSTEM_ID={name}"
        ),
        "README.md": render_readme(row),
    }
    if dry_run:
        print(f"DRY {name} tier={row.get('tier')} files={list(files)}")
        return dest
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    for rel, content in files.items():
        (dest / rel).write_text(content)
        print(f"wrote {dest / rel}")
    return dest


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--repo", required=True)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--force", action="store_true")
    p.add_argument("--all-stubs", action="store_true")
    args = p.parse_args()
    if args.all_stubs:
        inventory = load_inventory()
        count = 0
        for row in inventory:
            if row.get("tier") in {"STUB", "EMPTY"} and row["name"] not in PROTECTED_HINTS:
                stamp(row["name"], dry_run=args.dry_run, force=args.force)
                count += 1
        print(f"stamped {count} stub/empty repos")
        return
    stamp(args.repo, dry_run=args.dry_run, force=args.force)


if __name__ == "__main__":
    main()
