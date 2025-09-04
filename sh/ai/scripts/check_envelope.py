#!/usr/bin/env python3
import json, os, re, sys
from jsonschema import validate, ValidationError
import requests
def fail(msg): print(f"::error::{msg}"); sys.exit(1)
def pr_body():
    evp = os.environ.get("GITHUB_EVENT_PATH")
    if not evp or not os.path.exists(evp): fail("GITHUB_EVENT_PATH not found")
    event = json.load(open(evp))
    pr = event.get("pull_request") or {}
    body = pr.get("body")
    if body: return body
    token = os.environ["GITHUB_TOKEN"]
    owner, repo = os.environ["GITHUB_REPOSITORY"].split("/")
    number = pr.get("number")
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}"
    r = requests.get(url, headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"})
    r.raise_for_status()
    return r.json().get("body") or ""
def extract_env(text: str):
    m = re.search(r"```json\s*(\{.*?\})\s*```", text, flags=re.DOTALL|re.IGNORECASE)
    return json.loads(m.group(1)) if m else None
def validate_schema(env):
    with open("ai/schemas/copilot_envelope.schema.json", "r", encoding="utf-8") as f:
        schema = json.load(f)
    try: validate(env, schema)
    except ValidationError as e: fail(f"Envelope schema invalid: {e.message}")
def changed_files():
    token = os.environ["GITHUB_TOKEN"]
    owner, repo = os.environ["GITHUB_REPOSITORY"].split("/")
    number = json.load(open(os.environ["GITHUB_EVENT_PATH"]))["pull_request"]["number"]
    files, page = [], 1
    while True:
        url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}/files?per_page=100&page={page}"
        r = requests.get(url, headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"})
        r.raise_for_status()
        batch = r.json()
        if not batch: break
        files.extend([f["filename"] for f in batch]); page += 1
    return files
def allowed_from(env):
    allowed=set()
    for d in env.get("discovery", []):
        p=d.get("path");  allowed.update([p] if p else [])
    for c in env.get("changes", []):
        p=c.get("path");  allowed.update([p] if p else [])
    for t in env.get("tests", []):
        for k in ("path","golden"):
            p=t.get(k); allowed.update([p] if p else [])
    allowed |= {
        ".github/pull_request_template.md",".github/CODEOWNERS",
        ".github/workflows/ai_guardrails_on_commit.yml",
        "README.md","CONTRIBUTING.md","ai/CONTRIBUTING_AI.md"
    }
    return allowed
def main():
    body = pr_body()
    env = extract_env(body)
    if not env: fail("No fenced ```json envelope found in PR description.")
    validate_schema(env)
    changed = changed_files()
    allowed = allowed_from(env)
    offenders = [f for f in changed if not any(f==a or f.startswith(a.rstrip("*")) for a in allowed)]
    if offenders:
        print("::group::Scope violations")
        for f in offenders: print(f" - {f}")
        print("::endgroup::")
        fail("Changed files exceed envelope scope.")
    limit = env.get("limits",{}).get("files_touched")
    if isinstance(limit,int) and len(changed)>limit:
        fail(f"files_touched {len(changed)} exceeds declared limit {limit}")
    print(f"Envelope OK. {len(changed)} files within scope.")
if __name__=="__main__": main()
