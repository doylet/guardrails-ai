#!/usr/bin/env python3
import json
import os
import re
import sys
from jsonschema import validate, ValidationError
import requests


# Fail with an error message
def fail(msg):
    print(f"::error::{msg}")
    sys.exit(1) # Exit with error


# Get the pull request body
def pr_body():

    evp = os.environ.get("GITHUB_EVENT_PATH")

    # Check if the event path exists
    if not evp or not os.path.exists(evp):
        fail("GITHUB_EVENT_PATH not found")

    event = json.load(open(evp))
    pr = event.get("pull_request") or {}
    body = pr.get("body")

    if body:
        return body

    token = os.environ["GITHUB_TOKEN"]
    owner, repo = os.environ["GITHUB_REPOSITORY"].split("/")
    number = pr.get("number")
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}"

    # Make a request to the GitHub API
    try:
        r = requests.get(url, headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"})
        r.raise_for_status() # Check if the request was successful
    except requests.RequestException as e:
        fail(f"Failed to fetch pull request: {e}")

    # Get the pull request body
    return r.json().get("body") or ""


# Extract the JSON envelope from the pull request body
def extract_env(text: str):

    m = re.search(r"```json\s*(\{.*?\})\s*```", text, flags=re.DOTALL|re.IGNORECASE)

    # Extract the JSON envelope
    return json.loads(m.group(1)) if m else None


# Validate the JSON envelope against the schema
def validate_schema(env):

    # Load the schema
    with open(".ai/schemas/copilot_envelope.schema.json", "r", encoding="utf-8") as f:
        schema = json.load(f)

    # Validate the envelope
    try:
        validate(env, schema)
    except ValidationError as e:
        fail(f"Envelope schema invalid: {e.message}") # Validation failed


# Get the list of changed files in the pull request
def changed_files():

    token = os.environ["GITHUB_TOKEN"]
    owner, repo = os.environ["GITHUB_REPOSITORY"].split("/")
    number = json.load(open(os.environ["GITHUB_EVENT_PATH"]))["pull_request"]["number"]
    files, page = [], 1

    # Get the list of changed files
    while True:

        url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}/files?per_page=100&page={page}"

        # Make a request to the GitHub API
        try:
            r = requests.get(
                url,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json"
                }
            )

            r.raise_for_status()
            batch = r.json()

        except requests.RequestException as e:
            fail(f"Failed to fetch changed files: {e}")

        # Check if the batch is empty
        if not batch:
            break


        files.extend([f["filename"] for f in batch])
        page += 1

    # Get the list of changed files
    return files


# Get the list of allowed files from the envelope
def allowed_from(env):

    allowed=set()

    # Get the list of allowed files from the envelope
    for d in env.get("discovery", []):
        p=d.get("path")
        allowed.update([p] if p else [])

    # Get the list of allowed files from the envelope
    for c in env.get("changes", []):
        p=c.get("path")
        allowed.update([p] if p else [])

    # Get the list of allowed files from the envelope
    for t in env.get("tests", []):
        for k in ("path","golden"):
            p=t.get(k)
            allowed.update([p] if p else [])

    # Get the list of allowed files from the envelope
    allowed |= {
        ".github/pull_request_template.md",".github/CODEOWNERS",
        ".github/workflows/ai_guardrails_on_commit.yaml",
        "README.md","CONTRIBUTING.md","ai/CONTRIBUTING_AI.md"
    }

    # Get the list of allowed files from the envelope
    return allowed


# Main function
def main():
    body = pr_body()
    env = extract_env(body)

    if not env:
        fail("No fenced ```json envelope found in PR description.")

    validate_schema(env)
    changed = changed_files()
    allowed = allowed_from(env)
    offenders = [f for f in changed if not any(f==a or f.startswith(a.rstrip("*")) for a in allowed)]

    # Report any offenders
    if offenders:
        print("::group::Scope violations")

        for f in offenders:
            print(f" - {f}")

        print("::endgroup::")

        fail("Changed files exceed envelope scope.")

    limit = env.get("limits",{}).get("files_touched")

    if isinstance(limit,int) and len(changed)>limit:
        fail(f"files_touched {len(changed)} exceeds declared limit {limit}")

    print(f"Envelope OK. {len(changed)} files within scope.")


# Entry point
if __name__=="__main__":
    main()
