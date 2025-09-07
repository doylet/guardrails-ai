#!/usr/bin/env python3
from asyncio import subprocess
import json
import os
import pathlib
import sys

# Get the root directory of the project
root = pathlib.Path(__file__).resolve().parents[2]
candidates = []
envp = os.getenv("ENVELOPE_PATH")

if envp:
    candidates.append( pathlib.Path(envp) )

candidates += [root/".ai"/"envelope.json", root/"ai"/"envelope.local.json", root/"ai"/"envelope.json"]

env_path = next( (p for p in candidates if p and p.exists()), None )


# Check if the envelope file was found
if not env_path:
    sys.exit( "Missing envelope. Create .ai/envelope.json or set ENVELOPE_PATH=..." )


env = json.loads(env_path.read_text())


# Get allowed paths from envelope
def allowed_paths(e):

    s = set()

    # Discovery paths
    for d in e.get("discovery", []):
        p = d.get("path")
        s.update([p] if p else [])

    # Changes paths
    for c in e.get("changes", []):
        p = c.get("path")
        s.update([p] if p else [])

    # Test paths
    for t in e.get("tests", []):

        for k in ("path","golden"):
            p = t.get(k)
            s.update([p] if p else [])

    # Discovery paths
    return s

allowed = allowed_paths(env)

# Get the merge base
try:
    # merge_base = subprocess.check_output(["git","merge-base","HEAD","origin/main"]).decode().strip()
    # replace origin/main assumption in check_envelope_local.py
    default_branch = subprocess.create_subprocess_exec( "$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | cut -d/ -f2)" )
    merge_base = subprocess.create_subprocess_exec('$(git merge-base HEAD "origin/${default_branch:-main}" 2>/dev/null || echo "HEAD~1")')

# Get the list of changed files
except subprocess.CalledProcessError:
    merge_base = "HEAD~1"

changed = subprocess.check_output(["git","diff","--name-only", f"{merge_base}...HEAD"]).decode().splitlines()

off = [f for f in changed if not any(f==a or f.startswith(a.rstrip("*")) for a in allowed)]

# Report files outside envelope scope
if off:

    print("Files outside envelope scope:")

    # Report each file
    for f in off:
        print(" -", f)

    # Report the offending files
    sys.exit(1)

limit = env.get("limits",{}).get("files_touched") #


# Check if the limit is exceeded
if isinstance(limit,int) and len(changed)>limit:
    sys.exit(f"Changed files {len(changed)} exceed declared limit {limit}.")


# If we reach this point, the local envelope scope is considered valid
print("Local envelope scope OK.")
