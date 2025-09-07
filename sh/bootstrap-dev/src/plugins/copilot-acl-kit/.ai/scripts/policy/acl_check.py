#!/usr/bin/env python3
from __future__ import annotations
import os, sys, subprocess, fnmatch, re

ACL_PATH = ".ai/guardrails/acl.yml"

def eprint(*a): print(*a, file=sys.stderr)

def load_yaml(path: str):
    try:
        import yaml  # type: ignore
    except Exception:
        eprint("(!) PyYAML not installed; skipping ACL check locally. (CI installs it.)")
        return None
    if not os.path.exists(path):
        eprint(f"(!) {path} not found; skipping ACL check.")
        return None
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def resolve_aliases(ident: str, aliases: dict):
    if ident in aliases:
        out = []
        for x in aliases[ident]:
            out.extend(resolve_aliases(x, aliases))
        return out
    return [ident]

def flatten_identities(idents, aliases):
    out = []
    for i in idents or []:
        out.extend(resolve_aliases(i, aliases))
    seen = set()
    flat = []
    for x in out:
        if x not in seen:
            seen.add(x); flat.append(x)
    return flat

def get_changed(range_expr: str|None, staged: bool=False):
    if staged:
        cmd = ["git", "diff", "--cached", "--name-status", "-z", "--find-renames"]
    else:
        cmd = ["git", "diff", "--name-status", "-z", "--find-renames", range_expr]
    z = subprocess.check_output(cmd)
    parts = z.split(b"\x00")
    changes = []
    i = 0
    while i < len(parts) and parts[i]:
        status = parts[i].decode("utf-8", "replace")
        i += 1
        if status.startswith("R"):
            old = parts[i].decode("utf-8", "replace"); i += 1
            new = parts[i].decode("utf-8", "replace"); i += 1
            changes.append(("rename", old, new))
        else:
            path = parts[i].decode("utf-8", "replace"); i += 1
            act = {"A":"create","M":"modify","D":"delete"}.get(status[0], "modify")
            changes.append((act, path, path))
    return changes

def match_rule(path: str, rules: list[dict]):
    for r in rules:
        for pat in r.get("paths", []):
            if fnmatch.fnmatch(path, pat):
                return r
    return None

def actor_identity():
    actor = os.environ.get("GITHUB_ACTOR")
    if actor:
        return "@"+actor
    # fallback to local user name (best-effort)
    try:
        name = subprocess.check_output(["git","config","user.name"], text=True).strip() or "local"
    except Exception:
        name = "local"
    return name

def main(argv):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--range", help="A..B commit range (CI)")
    ap.add_argument("--staged", action="store_true", help="check staged changes (local)")
    ap.add_argument("--enforce", action="store_true", help="exit nonzero on violation")
    args = ap.parse_args(argv[1:])

    cfg = load_yaml(ACL_PATH)
    if cfg is None:
        return 0

    defaults = cfg.get("defaults", {})
    rules = cfg.get("rules", [])
    aliases = cfg.get("aliases", {})

    if args.staged and args.range:
        eprint("Use either --staged or --range, not both.")
        return 2

    changes = get_changed(args.range, staged=args.staged)
    if not changes:
        return 0

    actor = actor_identity()

    violations = []
    for act, old, new in changes:
        path = new if act != "delete" else old
        r = match_rule(path, rules) or {"name":"(no rule)", **defaults}
        allowed = flatten_identities(r.get("allow", ["*"]), aliases)
        actions = set((r.get("actions") or defaults.get("actions") or ["create","modify","delete","rename"]))
        mode = r.get("mode", defaults.get("mode","enforce"))

        if act not in actions:
            violations.append((path, act, r, f"action '{act}' is not allowed"))
            continue

        if "*" not in allowed and actor not in allowed:
            violations.append((path, act, r, f"{actor} not in allow list {allowed}"))

    if not violations:
        return 0

    eprint("ACL violations:")
    for path, act, rule, why in violations:
        eprint(f" - {path} ({act}) → rule: {rule.get('name','unnamed')} :: {why}")
        req = rule.get("require_reviews_from") or []
        if req:
            eprint(f"   requires review from: {', '.join(req)}")

    if args.enforce or (defaults.get("mode") == "enforce"):
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
