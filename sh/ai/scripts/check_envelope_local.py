#!/usr/bin/env python3
import json, subprocess, sys, pathlib, os
root = pathlib.Path(__file__).resolve().parents[2]
candidates = []
envp = os.getenv("ENVELOPE_PATH")
if envp: candidates.append(pathlib.Path(envp))
candidates += [root/".ai"/"envelope.json", root/"ai"/"envelope.local.json", root/"ai"/"envelope.json"]
env_path = next((p for p in candidates if p and p.exists()), None)
if not env_path:
    sys.exit("Missing envelope. Create .ai/envelope.json or set ENVELOPE_PATH=...")
env = json.loads(env_path.read_text())
def allowed_paths(e):
    s=set()
    for d in e.get("discovery", []):
        p=d.get("path");  s.update([p] if p else [])
    for c in e.get("changes", []):
        p=c.get("path");  s.update([p] if p else [])
    for t in e.get("tests", []):
        for k in ("path","golden"):
            p=t.get(k); s.update([p] if p else [])
    return s
allowed = allowed_paths(env)
try:
    # Try to find default branch, fallback to main, then HEAD~1
    try:
        default_branch = subprocess.check_output(["git", "symbolic-ref", "--short", "refs/remotes/origin/HEAD"], stderr=subprocess.DEVNULL).decode().strip().split("/")[-1]
    except subprocess.CalledProcessError:
        default_branch = "main"
    try:
        merge_base = subprocess.check_output(["git", "merge-base", "HEAD", f"origin/{default_branch}"], stderr=subprocess.DEVNULL).decode().strip()
    except subprocess.CalledProcessError:
        merge_base = "HEAD~1"
except subprocess.CalledProcessError:
    merge_base = "HEAD~1"
changed = subprocess.check_output(["git","diff","--name-only", f"{merge_base}...HEAD"]).decode().splitlines()
off = [f for f in changed if not any(f==a or f.startswith(a.rstrip("*")) for a in allowed)]
if off:
    print("Files outside envelope scope:")
    for f in off: print(" -", f)
    sys.exit(1)
limit = env.get("limits",{}).get("files_touched")
if isinstance(limit,int) and len(changed)>limit:
    sys.exit(f"Changed files {len(changed)} exceed declared limit {limit}.")
print("Local envelope scope OK.")
