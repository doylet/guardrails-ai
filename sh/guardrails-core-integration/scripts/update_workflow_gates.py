#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import sys, shutil
from datetime import datetime

try:
    from ruamel.yaml import YAML  # type: ignore
    YAML_LIB = "ruamel"
except Exception:
    import yaml  # type: ignore
    YAML_LIB = "pyyaml"

MAIN = Path(".github/workflows/ai-guardrails-full.yml")
GATES = ["gate_commit_messages", "gate_root_hygiene"]

def load_yaml(p: Path):
    if YAML_LIB == "ruamel":
        y = YAML()
        y.preserve_quotes = True
        y.indent(mapping=2, sequence=4, offset=2)
        with p.open("r", encoding="utf-8") as f:
            return y, y.load(f) or {}
    else:
        with p.open("r", encoding="utf-8") as f:
            return None, yaml.safe_load(f) or {}

def dump_yaml(p: Path, loader, data):
    if YAML_LIB == "ruamel":
        loader.dump(data, p.open("w", encoding="utf-8"))
    else:
        p.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")

def ensure_gates(data: dict) -> None:
    jobs = data.setdefault("jobs", {})
    jobs.setdefault("gate_commit_messages", {"uses": "./.github/workflows/commit-message.yml", "secrets": "inherit"})
    jobs.setdefault("gate_root_hygiene", {"uses": "./.github/workflows/root-hygiene.yml", "secrets": "inherit"})

def merge_needs(old, extra):
    if old is None:
        return list(extra)
    if isinstance(old, str):
        old = [old]
    seen = {}
    for x in list(old) + list(extra):
        seen[x] = True
    return list(seen.keys())

def add_needs(data: dict) -> int:
    jobs = data.setdefault("jobs", {})
    changed = 0
    for name, job in jobs.items():
        if name in GATES or not isinstance(job, dict):
            continue
        new = merge_needs(job.get("needs"), GATES)
        if new != job.get("needs"):
            job["needs"] = new
            changed += 1
    return changed

def main():
    if not MAIN.exists():
        print(f"ERROR: {MAIN} not found.", file=sys.stderr)
        return 2
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = MAIN.with_suffix(MAIN.suffix + f".bak.{ts}")
    shutil.copy2(MAIN, backup)
    print(f"Backup: {backup}")

    loader, data = load_yaml(MAIN)
    ensure_gates(data)
    changed = add_needs(data)
    dump_yaml(MAIN, loader, data)
    print(f"Updated {MAIN} (needs merged on {changed} job(s)).")
    return 0

if __name__ == "__main__":
    sys.exit(main())
