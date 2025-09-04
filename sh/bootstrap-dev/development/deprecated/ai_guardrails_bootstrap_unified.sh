#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# AI Guardrails Bootstrap (Unified) - DEPRECATED
#
# ⚠️  DEPRECATION NOTICE ⚠️
# This unified script is deprecated and will be removed in a future version.
# Please migrate to the new modular bootstrap script for better maintainability:
#
#   ai_guardrails_bootstrap_modular.sh
#
# Benefits of the modular approach:
# - Faster updates with template repository
# - Better version management
# - Offline mode support
# - Easier customization for organizations
#
# Migration is simple - the modular script provides identical functionality.
# For migration help, see: docs/migration-guide.md
# ============================================================================

# ============================================================================
# AI Guardrails Bootstrap (Unified)
# Modes:
#   --apply   : write guardrail files (default; skips existing unless --force)
#   --ensure  : create minimal local bits (e.g., .ai/envelope.json) & install hooks
#   --doctor  : diagnose common setup problems (no writes)
# Options:
#   -C PATH   : repo root (auto-detect via git if omitted)
#   --force   : overwrite existing files when applying
#   --verbose : extra logging
# ----------------------------------------------------------------------------

MODE="apply"
FORCE=0
VERBOSE=0
REPO_ROOT=""
REPAIR=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --apply) MODE="apply"; shift;;
    --ensure) MODE="ensure"; shift;;
    --doctor) MODE="doctor"; shift;;
    --repair) REPAIR=1; shift;;
    -C) REPO_ROOT="$2"; shift 2;;
    --force) FORCE=1; shift;;
    --verbose) VERBOSE=1; shift;;
    -h|--help)
      cat <<'USAGE'
AI Guardrails Bootstrap (Unified)

Usage:
  bash ai_guardrails_bootstrap_unified.sh [--apply|--ensure|--doctor] [-C /path/to/repo] [--force] [--verbose]

Modes:
  --apply   Write guardrail files (schema, scripts, prompts, CI, hooks). Skips existing files unless --force.
  --ensure  Create missing local bits (.ai/envelope.json) and install pre-commit hooks.
  --doctor  Diagnose common issues (git worktree, line endings, tools, missing files). No writes.

Examples:
  # Apply to current repo
  bash ai_guardrails_bootstrap_unified.sh

  # Apply to a specific repo and overwrite existing files
  bash ai_guardrails_bootstrap_unified.sh -C ~/code/my-repo --force

  # Quick local setup + hooks
  bash ai_guardrails_bootstrap_unified.sh --ensure

  # Diagnose
  bash ai_guardrails_bootstrap_unified.sh --doctor -C ~/code/my-repo
USAGE
      exit 0;;
    *) echo "Unknown arg: $1"; exit 1;;
  esac
done

# Detect repo root
if [[ -z "${REPO_ROOT}" ]]; then
  if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    REPO_ROOT="$(git rev-parse --show-toplevel)"
  else
    echo "::warning:: Not in a git repository. Using current directory: $PWD"
    REPO_ROOT="$PWD"
  fi
fi

# Validate and change to repo root
if [[ ! -d "$REPO_ROOT" ]]; then
  echo "::error:: Repository root does not exist: $REPO_ROOT"
  exit 1
fi

cd "$REPO_ROOT" || {
  echo "::error:: Cannot change to repository root: $REPO_ROOT"
  exit 1
}
echo "→ Target repo: $REPO_ROOT"

log() { [[ $VERBOSE -eq 1 ]] && echo "[debug] $*"; }

# ----------------------------------------------------------------------------
# DOCTOR
doctor() {
  echo "== Doctor =="

  # bash, python presence
  command -v bash >/dev/null || { echo "::error:: bash not found on PATH"; exit 1; }
  if ! command -v python >/dev/null && ! command -v python3 >/dev/null; then
    echo "::warning:: Python not found; pre-commit install may be skipped."
  fi

  # git sanity
  if ! git status -s >/dev/null 2>&1; then
    echo "::error:: Not a git worktree or git not available"
    exit 1
  fi

  # Line endings on this script
  if file "$0" | grep -qi "CRLF"; then
    echo "::warning:: Script has CRLF line endings. Run: sed -i 's/\r$//' $0"
  fi

  # Expected dirs/files
  local DIRS=( ".ai" "ai/scripts" "ai/schemas" ".github/workflows" ".github/instructions" ".github/chatmodes" ".github/prompts" "ai/decisions" "docs/decisions" )
  local FILES=(
    ".ai/envelope.json"
    "ai/schemas/copilot_envelope.schema.json"
    "ai/scripts/check_envelope.py"
    "ai/scripts/check_envelope_local.py"
    "ai/scripts/lang_lint.sh"
    "ai/scripts/lang_test.sh"
    ".pre-commit-config.yaml"
    ".github/workflows/ai_guardrails_on_commit.yml"
    ".github/chatmodes/blueprint-mode-mod.chatmode.md"
    ".github/prompts/strict_mode.prompts.md"
    ".github/instructions/memory-usage.md"
    "ai/capabilities.md"
    "ai/ai_rules.yaml"
    "docs/decisions/ADR-template.md"
  )
  local missing=0
  for d in "${DIRS[@]}"; do [[ -d "$d" ]] || { echo "::warning:: missing dir: $d"; missing=1; }; done
  for f in "${FILES[@]}"; do [[ -f "$f" ]] || { echo "::warning:: missing file: $f"; missing=1; }; done

  if [[ $missing -eq 1 ]]; then
    echo "⚠️  Some guardrail files are missing. Re-run with --apply or --ensure."
  else
    echo "✅ Guardrail files present."
  fi

  # Pre-commit hook presence
  if [[ -d .git/hooks ]]; then
    [[ -f .git/hooks/pre-commit ]] && echo "✓ pre-commit hook present" || echo "• pre-commit hook not installed"
    [[ -f .git/hooks/pre-push   ]] && echo "✓ pre-push hook present"   || echo "• pre-push hook not installed"
  fi

  # Upstream branch
  if git rev-parse --verify origin/main >/dev/null 2>&1; then
    echo "Upstream found: origin/main"
  else
    echo "• No origin/main; local pre-push scope will compare to HEAD~1"
  fi

  echo "-- Doctor complete --"
}

# ----------------------------------------------------------------------------
# ENSURE
ensure_local() {
  echo "== Ensure local bits =="
  mkdir -p .ai
  if [[ ! -f .ai/envelope.json ]]; then
    cat > .ai/envelope.json <<'EOFJSON'
{
  "discovery": [], "assumptions": [], "plan": [], "changes": [], "tests": [],
  "validation": { "commands": [], "results": [] },
  "limits": { "files_touched": 5, "workflow": "Main" },
  "risks": [], "rollback": [], "question": null, "status": "READY_FOR_REVIEW"
}
EOFJSON

    echo "Created .ai/envelope.json"
  else
    echo "✓ .ai/envelope.json exists"
  fi

    # Install hooks if config exists
  if [[ -f .pre-commit-config.yaml ]]; then
    if command -v python >/dev/null || command -v python3 >/dev/null; then
      PYBIN="$(command -v python || command -v python3)"
      "$PYBIN" - <<'PY' || true
import sys, subprocess
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "pre-commit"], check=False)
PY
      pre-commit install || true
      pre-commit install -t pre-push || true
      echo "Installed pre-commit hooks"
      # after installing hooks
      git config core.hooksPath >/dev/null 2>&1 && echo "ℹ︎ core.hooksPath is set; pre-commit will place hooks there."
    else
      echo "::warning:: Python not found; skipped pre-commit install"
    fi
  else
    echo "• No .pre-commit-config.yaml yet (run --apply first)"
  fi
  echo "-- Ensure complete --"
}

# -----------------------------------------------------------------------------
write_file() {
  # write_file <path> <label_unused> <content>
  local path="$1"; shift
  local _label_unused="$1"; shift
  local content="$1"

  # Validate inputs
  if [[ -z "$path" ]]; then
    echo "::error:: write_file: path cannot be empty"
    return 1
  fi

  local dir
  dir="$(dirname "$path")"
  if [[ ! -d "$dir" ]]; then
    if ! mkdir -p "$dir"; then
      echo "::error:: Failed to create directory: $dir"
      return 1
    fi
  fi

  if [[ -e "$path" && ${FORCE:-0} -eq 0 ]]; then
    echo "skip (exists): $path"
  else
    # Write content exactly as provided (preserves newlines)
    if printf '%s' "$content" > "$path"; then
      echo "wrote: $path"
    else
      echo "::error:: Failed to write file: $path"
      return 1
    fi
  fi
}

# ----------------------------------------------------------------------------
apply_bootstrap() {
  echo "== Apply guardrails =="

  mkdir -p .ai ai/scripts ai/schemas ai/prompts ai/decisions .github/workflows .github/instructions .github/chatmodes .github

  # .gitignore
  if [[ ! -f .gitignore ]] || ! grep -q '^\.ai/envelope\.json$' .gitignore; then
    echo ".ai/envelope.json" >> .gitignore || true
  fi

  # Config
  write_file ".ai/guardrails.yaml" "EOFYML" \
'python:
  lint: "ruff check ."
  type: "mypy ."
  test: "pytest -q"
node:
  lint: "npx -y eslint . || npx -y @biomejs/biome check ."
  type: "npx -y tsc --noEmit"
  test: "npm test --silent || pnpm -s test || yarn -s test"
go:
  lint: "golangci-lint run || (go vet ./... && echo '\''fallback go vet ok'\'')"
  test: "go test ./..."
rust:
  lint: "cargo clippy --no-deps -q -D warnings || echo '\''clippy not installed'\''"
  test: "cargo test --quiet"
java:
  test: "mvn -q -DskipTests=false test || ./gradlew test"
dotnet:
  test: "dotnet test --nologo --verbosity quiet"
generic:
  shell: "shopt -s globstar nullglob; (command -v shellcheck >/dev/null && shellcheck **/*.sh) || echo '\''shellcheck not found'\''"
  docker: "shopt -s globstar nullglob; (command -v hadolint >/dev/null && hadolint **/Dockerfile* || echo '\''hadolint not found'\'')"
  markdown: "(command -v markdownlint >/dev/null && markdownlint . || echo '\''markdownlint not found'\'')"'
  # Local envelope (created if missing)
  if [[ ! -f .ai/envelope.json || $FORCE -eq 1 ]]; then
    cat > .ai/envelope.json <<'EOFJSON1'
{
  "discovery": [], "assumptions": [], "plan": [], "changes": [], "tests": [],
  "validation": { "commands": [], "results": [] },
  "limits": { "files_touched": 5, "workflow": "Main" },
  "risks": [], "rollback": [], "question": null, "status": "READY_FOR_REVIEW"
}
EOFJSON1
    echo "wrote: .ai/envelope.json"
  else
    echo "skip (exists): .ai/envelope.json"
  fi

  # Envelope JSON Schema
  write_file "ai/schemas/copilot_envelope.schema.json" "EOFJSON2" \
'{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Copilot JSON Envelope",
  "type": "object",
  "required": ["discovery","plan","changes","tests","validation","limits","risks","rollback","status"],
  "properties": {
    "discovery": {"type":"array","minItems":1,"items":{"type":"object","required":["path","why"],"properties":{"path":{"type":"string"},"evidence":{"type":"string"},"why":{"type":"string"}},"additionalProperties":false}},
    "assumptions":{"type":"array","items":{"type":"string"}},
    "plan":{"type":"array","minItems":1,"items":{"type":"string"}},
    "changes":{"type":"array","items":{"type":"object","required":["path","patch"],"properties":{"path":{"type":"string"},"patch":{"type":"string"}},"additionalProperties":false}},
    "tests":{"type":"array","items":{"type":"object","properties":{"path":{"type":"string"},"patch":{"type":"string"},"golden":{"type":"string"},"check":{"type":"string","enum":["structural","byte","custom"]}},"additionalProperties":false}},
    "validation":{"type":"object","required":["commands"],"properties":{"commands":{"type":"array","items":{"type":"string"}},"results":{"type":"array","items":{"type":"string"}}},"additionalProperties":true},
    "limits":{"type":"object","required":["files_touched","workflow"],"properties":{"files_touched":{"type":"integer","minimum":1},"workflow":{"type":"string","enum":["Loop","Debug","Express","Main"]}},"additionalProperties":false},
    "risks":{"type":"array","items":{"type":"string"}},
    "rollback":{"type":"array","items":{"type":"string"}},
    "question":{"type":["string","null"]},
    "status":{"type":"string","enum":["READY_FOR_REVIEW","BLOCKED","DRAFT"]},
    "could_not_find":{"type":"array","items":{"type":"string"}}
  },
  "additionalProperties": false
}'

  # CI envelope/scope checker
  write_file "ai/scripts/check_envelope.py" "EOFPY1" \
'#!/usr/bin/env python3
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
'
  chmod +x ai/scripts/check_envelope.py

  # Local pre-push checker
  write_file "ai/scripts/check_envelope_local.py" "EOFPY2" \
'#!/usr/bin/env python3
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
'
  chmod +x ai/scripts/check_envelope_local.py

  # Language-aware launchers
  write_file "ai/scripts/lang_lint.sh" "EOFSH1" \
'#!/usr/bin/env bash
set -euo pipefail
shopt -s nullglob
read_cfg() { awk "/^$1:/{f=1} f&&/$2:/{print substr(\$0,index(\$0,\":\")+2); exit}" .ai/guardrails.yaml 2>/dev/null | sed '\''s/^[[:space:]]*"//;s/"[[:space:]]*$//'\'' || true; }
py_lint=$(read_cfg python lint); node_lint=$(read_cfg node lint); go_lint=$(read_cfg go lint); rust_lint=$(read_cfg rust lint)
has() { command -v "$1" >/dev/null 2>&1; }
if [[ -f pyproject.toml || -f requirements.txt || -n "$(echo **/*.py 2>/dev/null)" ]]; then
  if [[ -n "${py_lint:-}" ]]; then
    # Use direnv exec to ensure proper environment
    if command -v direnv >/dev/null 2>&1; then
      direnv exec . bash -c "$py_lint"
    else
      bash -lc "$py_lint"
    fi
  elif [[ -f .venv/bin/ruff ]]; then
    echo "Using .venv/bin/ruff"
    ./.venv/bin/ruff check .
  elif command -v ruff >/dev/null; then
    echo "Using system ruff"
    ruff check .
  else
    echo "ruff not found; skipping python lint"
  fi
fi
if [[ -f package.json ]]; then
  if [[ -n "${node_lint:-}" ]]; then bash -lc "$node_lint"; else npx -y eslint . || npx -y @biomejs/biome check . || echo "eslint/biome unavailable"; fi
fi
if [[ -f go.mod ]]; then
  if [[ -n "${go_lint:-}" ]]; then bash -lc "$go_lint"; elif command -v golangci-lint >/dev/null; then golangci-lint run; else go vet ./... || true; fi
fi
if [[ -f Cargo.toml ]]; then
  if [[ -n "${rust_lint:-}" ]]; then bash -lc "$rust_lint"; elif command -v cargo >/dev/null; then cargo clippy --no-deps -q -D warnings || echo "clippy not installed"; fi
fi
if command -v shellcheck >/dev/null 2>&1; then shellcheck **/*.sh || true; fi
if command -v hadolint   >/dev/null 2>&1; then hadolint **/Dockerfile* || true; fi
if command -v markdownlint >/dev/null 2>&1; then markdownlint . || true; fi
'
  chmod +x ai/scripts/lang_lint.sh

  write_file "ai/scripts/lang_test.sh" "EOFSH2" \
'#!/usr/bin/env bash
set -euo pipefail
read_cfg() { awk "/^$1:/{f=1} f&&/$2:/{print substr(\$0,index(\$0,\":\")+2); exit}" .ai/guardrails.yaml 2>/dev/null || true; }
if [[ -f pyproject.toml || -f requirements.txt || -n "$(echo **/*.py 2>/dev/null)" ]]; then
  cmd=$(read_cfg python test); if [[ -n "$cmd" ]]; then bash -lc "$cmd"; elif command -v pytest >/dev/null; then pytest -q; fi
fi
if [[ -f package.json ]]; then
  cmd=$(read_cfg node test); if [[ -n "$cmd" ]]; then bash -lc "$cmd"; else npm test --silent || pnpm -s test || yarn -s test || true; fi
fi
if [[ -f go.mod ]]; then
  cmd=$(read_cfg go test); if [[ -n "$cmd" ]]; then bash -lc "$cmd"; else go test ./...; fi
fi
if [[ -f Cargo.toml ]]; then
  cmd=$(read_cfg rust test); if [[ -n "$cmd" ]]; then bash -lc "$cmd"; else cargo test --quiet; fi
fi
if [[ -f pom.xml || -f build.gradle || -f build.gradle.kts ]]; then
  cmd=$(read_cfg java test); if [[ -n "$cmd" ]]; then bash -lc "$cmd"; else mvn -q -DskipTests=false test || ./gradlew test; fi
fi
if compgen -G "**/*.sln" > /dev/null || compgen -G "**/*.csproj" > /dev/null; then
  cmd=$(read_cfg dotnet test); if [[ -n "$cmd" ]]; then bash -lc "$cmd"; else dotnet test --no-build --nologo --verbosity quiet; fi
fi
'
  chmod +x ai/scripts/lang_test.sh

  # pre-commit config
  write_file ".pre-commit-config.yaml" "EOFYAML1" \
'repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: end-of-file-fixer
      - id: trailing-whitespace
      - id: mixed-line-ending
      - id: check-merge-conflict
      - id: detect-private-key
  - repo: local
    hooks:
      - id: lang-lint
        name: language lint (auto-detect)
        entry: ai/scripts/lang_lint.sh
        language: system
        pass_filenames: false
      - id: lang-test-quick
        name: language test (quick)
        entry: ai/scripts/lang_test.sh
        language: system
        pass_filenames: false
        stages: [pre-push]
      - id: ai-envelope-local
        name: AI envelope (local scope check)
        entry: python ai/scripts/check_envelope_local.py
        language: system
        pass_filenames: false
        stages: [pre-push]
      - id: ai-envelope-updated
        name: AI envelope must be updated (newer than last commit)
        entry: bash -c "if [[ -f .ai/envelope.json ]]; then if [[ .ai/envelope.json -ot .git/logs/HEAD ]]; then echo \"::error::.ai/envelope.json is older than last commit. Update it to reflect your changes.\"; exit 1; fi; fi"
        language: system
        pass_filenames: false
        stages: [pre-commit]'

  # GitHub Actions workflow
  write_file ".github/workflows/ai_guardrails_on_commit.yml" "EOFYAML2" \
'name: AI Guardrails (Full)
on:
  pull_request:
    types: [opened, edited, synchronize, reopened]
  push:
    branches: ["**"]
permissions:
  contents: read
  pull-requests: read
concurrency:
  group: ai-guardrails-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: false
jobs:
  envelope:
    if: ${{ github.event_name == '\''pull_request'\'' }}
    runs-on: ubuntu-latest
    env: { GITHUB_TOKEN: ${{ github.token }} }
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: python -m pip install --upgrade pip jsonschema requests
      - name: Validate envelope & scope
        run: python ai/scripts/check_envelope.py
  python:
    if: ${{ hashFiles('\''**/pyproject.toml'\'', '\''**/requirements.txt'\'') != '''' || hashFiles('\''**/*.py'\'') != '''' }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - name: Install deps
        run: |
          python -m pip install --upgrade pip
          [ -f requirements-dev.txt ] && pip install -r requirements-dev.txt || true
          [ -f requirements.txt ] && pip install -r requirements.txt || true
          pip install -q pytest ruff mypy
      - run: ruff check .
      - run: mypy .
      - run: pytest -q
  node:
    if: ${{ hashFiles('\''**/package.json'\'') != '''' }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '\''20'\'', cache: '\''npm'\'' }
      - name: Install
        run: |
          if [ -f package-lock.json ]; then npm ci; elif [ -f pnpm-lock.yaml ]; then corepack enable && pnpm i --frozen-lockfile; elif [ -f yarn.lock ]; then yarn --frozen-lockfile; else npm i; fi
      - name: Lint
        run: npx -y eslint . || npx -y @biomejs/biome check .
      - name: Type Check
        run: npx -y tsc --noEmit || echo "tsc not configured"
      - name: Test
        run: npm test --silent || pnpm -s test || yarn -s test || true
  go:
    if: ${{ hashFiles('\''**/go.mod'\'') != '''' }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with: { go-version: '\''1.22'\'' }
      - run: go mod download
      - run: go vet ./...
      - run: go test ./...
  rust:
    if: ${{ hashFiles('\''**/Cargo.toml'\'') != '''' }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
      - run: cargo fmt -- --check || true
      - run: cargo check
      - run: cargo test --quiet
  java:
    if: ${{ hashFiles('\''**/pom.xml'\'', '\''**/build.gradle'\'', '\''**/build.gradle.kts'\'') != '''' }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with:
          distribution: temurin
          java-version: '\''21'\''
      - run: |
          if [ -f pom.xml ]; then mvn -q -DskipTests=false test;
          elif [ -f gradlew ]; then chmod +x gradlew && ./gradlew test;
          else echo "No Maven/Gradle wrapper found"; fi
  dotnet:
    if: ${{ hashFiles('\''**/*.sln'\'', '\''**/*.csproj'\'') != '''' }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-dotnet@v4
        with: { dotnet-version: '\''8.0.x'\'' }
      - run: dotnet restore
      - run: dotnet build --no-restore --nologo
      - run: dotnet test --no-build --nologo --verbosity quiet
  generic_checks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Shellcheck (if present)
        run: |
          sudo apt-get update -y && sudo apt-get install -y shellcheck || true
          shopt -s globstar nullglob
          shellcheck **/*.sh || true
      - name: Hadolint (if present)
        run: |
          curl -sL -o /usr/local/bin/hadolint https://github.com/hadolint/hadolint/releases/latest/download/hadolint-Linux-x86_64 || true
          chmod +x /usr/local/bin/hadolint || true
          shopt -s globstar nullglob
          hadolint **/Dockerfile* || true
      - name: Markdownlint (if present)
        run: |
          npm -g i markdownlint-cli || true
          markdownlint . || true'

  # PR template
  write_file ".github/pull_request_template.md" "EOFMD1" \
'MODE: <Loop|Debug|Express|Main> | scope=<N> | confidence=<0–100> | rationale=<one line>

```json
{
  "discovery": [],
  "assumptions": [],
  "plan": [],
  "changes": [],
  "tests": [],
  "validation": { "commands": [], "results": [] },
  "limits": { "files_touched": 5, "workflow": "Main" },
  "risks": [],
  "rollback": [],
  "question": null,
  "status": "READY_FOR_REVIEW"
}
```
'

  # Prompts & instructions
  write_file ".github/chatmodes/blueprint-mode-mod.chatmode.md" "EOFMD2" \
'
---
description: "Follows strict workflows (Debug, Express, Main, Loop) to analyze requirements, plan before coding and verify against edge cases. Self-corrects and favors simple, maintainable solutions."
---

# Blueprint Mode v32 GitHub Copilot Chat

## Goal

You are a blunt and pragmatic senior dev. You give clear plans, write tight code with a smirk.

Ship **safe, minimal, verifiable** changes. **Reuse > rebuild.** No silent scope creep or regressions.

## Where this applies

- **Chat view:** planning, discovery, multi-file patches.
- **Inline Chat (⌘I):** single-file surgical edits only.

## Outputs (exactly two, in order)

1. **MODE line** (single sentence):
`MODE: <Loop|Debug|Express|Main> | scope=<N files> | confidence=<0100> | rationale=<one line>`
2. **One of:**
- **Chat view:** JSON envelope (below) + `diff` blocks
- **Inline Chat:** a single `diff` block for the current file

> If the envelope would exceed limits, send an **index** first (files + intent), then stream `PATCH [i/N]` messages.

## Non-negotiables

- **Discovery before design:** list concrete paths you’ll call/change (modules, tests, schemas).
- **Reuse existing capability** (e.g., PPTX pipeline). Extending is allowed; cloning is not.
- **Scope fences:** `Express ≤ 2 files`, otherwise `≤ 5` without explicit approval.
- **Test-first for behavior changes:** add/adjust characterization or golden tests (e.g., `.pptx` structural checks).
- **Verification required:** show the commands you _would_ run (`pytest`, `ruff`, `mypy`) and expected short outcomes.
- **Fail closed on ambiguity:** if confidence `< 60`, ask **one** question and stop.

## Example JSON envelope (Chat view)

<example-json-envelope>
```json
{
  "discovery": [
    {
      "path": "src/ai_deck_gen/pipeline/pptx/render.py",
      "evidence": "def render_pptx(...)",
      "why": "entrypoint"
    },
    {
      "path": "tests/pipelines/test_pptx_pipeline.py",
      "evidence": "test_renders_minimal_deck",
      "why": "characterization"
    },
    {
      "path": "schemas/pptx_plan.schema.json",
      "evidence": "required fields: title, slides[]",
      "why": "contract"
    }
  ],
  "assumptions": ["theme X should not change placeholder indices"],
  "plan": ["Smallest viable steps…"],
  "changes": [
    { "path": "src/.../render.py", "patch": "diff --git a/... b/...\n@@ ..." }
  ],
  "tests": [
    {
      "path": "tests/.../test_pptx_pipeline.py",
      "patch": "diff --git a/... b/...\n@@ ..."
    },
    { "golden": "tests/golden/sample_deck.pptx", "check": "structural" }
  ],
  "validation": {
    "commands": ["pytest -q", "ruff .", "mypy ."],
    "results": ["all green | 12 passed, 0 failed | lint/type clean"]
  },
  "limits": { "files_touched": 2, "workflow": "Express" },
  "risks": ["legacy theme placeholders may shift"],
  "rollback": ["git revert <sha>"],
  "question": null,
  "status": "READY_FOR_REVIEW"
}
```
</example-json-envelope>

## Diff rules

- Use unified `diff` blocks; keep each hunk minimal.
- **Inline Chat:** modify only the _current_ file.
- Never introduce new top-level packages or pipelines unless `"could_not_find"` is present.

## Ambiguity policy

- `confidence < 60` populate `question` (one, concise) and **stop**.
- `6090` proceed, list `assumptions`.
- `> 90` proceed.

## Workflow picker (Copilot-friendly)

- **Loop:** repeatable ops (refactors, codemods)
- **Debug:** reproduction + targeted fix
- **Express:** tiny change (≤ 2 files)
- **Main:** anything larger or multi-step

## Tiny examples

**MODE line (Chat view):**
`MODE: Express | scope=2 files | confidence=78 | rationale=extend existing pptx renderer to support theme X`

**Inline Chat ask (inside `render.py`):**
“Add guard so empty slide content is skipped; keep public API. Return early and log at debug.”

**Expected Inline output:** one `diff` block touching only `render.py`.

## Artifacts

These are for internal use only; keep concise, absolute minimum.

```yaml
artifacts:
  - name: memory
    path: .github/instructions/memory.instruction.md
    type: memory_and_policy
    format: "Markdown with distinct '\''## Policies'\'' and '\''## Heuristics'\'' sections."
    purpose: "Single source for guiding agent behavior. Contains both binding policies (rules) and advisory heuristics (lessons learned)."
    update_policy:
      - who: "agent or human reviewer"
      - when: "When a binding policy is set or a reusable pattern is discovered."
      - structure: "New entries must be placed under the correct heading (\`## Policies\` or \`## Heuristics\`) with a clear rationale."

  - name: envelope_local
    path: .ai/envelope.json
    type: plan_scope
    format: "JSON matching ai/schemas/copilot_envelope.schema.json"
    purpose: "Local, per-branch plan/scope; drives pre-push scope checks."
    update_policy:
      - who: "agent"
      - when: "Before first edit; whenever touching additional files; before Verify."
      - structure: "Fill discovery/plan/changes/tests/validation/limits with explicit file paths or folder prefixes."

  - name: envelope_schema
    path: ai/schemas/copilot_envelope.schema.json
    type: schema
    format: "JSON Schema (Draft-07)"
    purpose: "Validation for envelope_local and PR envelope.

  ```yaml
artifacts:
  - name: memory
    path: .github/instructions/memory.instruction.md
    type: memory_and_policy
    format: "Markdown with distinct '\''## Policies'\'' and '\''## Heuristics'\'' sections."
    purpose: "Single source for guiding agent behavior. Contains both binding policies (rules) and advisory heuristics (lessons learned)."
    update_policy:
      - who: "agent or human reviewer"
      - when: "When a binding policy is set or a reusable pattern is discovered."
      - structure: "New entries must be placed under the correct heading (\`## Policies\` or \`## Heuristics\`) with a clear rationale."

  - name: envelope_local
    path: .ai/envelope.json
    type: plan_scope
    format: "JSON matching ai/schemas/copilot_envelope.schema.json"
    update_policy:
      - who: "agent"
      - when: "Before first edit; whenever adding/removing touched files; before Verify."
      - structure: "Fill discovery/plan/changes/tests/validation/limits with explicit file paths or folder prefixes."

  - name: agent_work
    path: docs/specs/agent_work/
    type: workspace
    format: markdown / txt / generated artifacts
    purpose: "Temporary and final artifacts produced during agent runs (summaries, intermediate outputs)."
    filename_convention: "summary_YYYY-MM-DD_HH-MM-SS.md"
    update_policy:
      - who: "agent"
      - when: "during execution"
```
'
  write_file ".github/prompts/strict_mode.prompts.md" "EOFMD3" \
'---
role: "agent"
---

# STRICT MODE

You are working **inside an existing codebase**. Your job is to **reuse** capabilities, not to recreate them. Before proposing changes:

1) **DISCOVER**: locate relevant code, tests, CLIs, and docs. Use ripgrep-like searches.
2) **CITE**: list absolute file paths you relied on + line ranges (approx ok).
3) **PLAN**: propose the smallest change that satisfies the requirement.
4) **DIFF-ONLY**: present changes as minimal, reviewable diffs. No broad rewrites.
5) **TEST-FIRST**: add/adjust characterization or golden tests before code changes.
6) **NO DUPLICATES**: do not create parallel pipelines for existing capabilities.
7) **STOP-ASK**: if discovery finds a capability, **stop and integrate** with it.

Your output **must** be JSON:

<example-output>
```json
{
  "discovery": [{"path": ".../render_pptx.py","evidence": "fn render(...)", "why": "entry point"}],
  "plan": ["..."],
  "changes": [{"path":"...", "patch":"diff --git ..."}],
  "tests": [{"path":"tests/...","patch":"diff --git ..."}],
  "risks": ["..."],
  "rollback": ["git revert ..."]
}
```
</example-output>

If you cant find an existing capability, explicitly say so and show your search queries.'

  write_file "ai/ai_rules.yaml" "EOFYAML3" \
'boundaries:
  - name: "No duplicate pipelines"
    rule: "If capability exists in ai/capabilities.md, modify/extend only."
  - name: "Scope fences"
    rule: "Changes limited to files cited under discovery; max 5 files unless approved."
  - name: "Contracts first"
    rule: "If a schema or golden exists, update tests before code."
outputs:
  require_json_schema: true
  schema_ref: ai/schemas/copilot_envelope.schema.json
quality_gates:
  - "python -m pytest -q || true"
  - "ruff check . || true"
  - "mypy . || true"'

  write_file ".github/instructions/memory-usage.md" "EOFMD5" \
'---
applyTo: "*"
role: agent
---

# POLICY

## Golden Rules (Non-Negotiable)

1. **Single LLM pathway:**
All LLM calls go through ai_deck_gen/adapters/LMStudioProvider. No alternatives. No stubs.
2. **Fail fast over guessing:** If anything is unclear (API, schema, invariants), STOP and ask. Do not invent.
3. **Prefer maintainability:** Small changes, clear structure. Follow SOLID/DRY, naming and folder conventions.
4. **Always reuse first:** Before proposing code, discover and cite existing modules, tests, schemas, and CLIs you will call.
5. **Working code with tests:** Every new behavior is covered by tests. All tests must pass.
6. **Clean repo + clean history:** Respect project structure; practice proper branching and commit hygiene; never develop on main.

## Hard DO NOTs

- Do not introduce new adapters/engines/clients if one exists.
- Do not add stubs, mocks, “fake” providers, or speculative scaffolding.
- Do not ship features without a design note (even brief) and tests.
- Do not use emojis.
- Do not bypass planning: no broad refactors hidden in a “fix”.
- Do not push to main. Keep main releasable at all times.

## Strict DRY/Reuse Mode

### Discovery-before-design

- Run a focused search and list the exact functions/classes (by module path) you intend to call, and why.

### ACK handshake

- If reuse is found, begin reply with ACK REUSE and include a call graph (who calls what).
- If an import fails, STOP. Do not scaffold an alternative.

### No duplicate capability

- If a capability exists, you may extend or fix it but not clone it.
'
  write_file "ai/capabilities.md" "EOFMD5" \
'---
description: [Capture an overview of project capabilities to keep copilot on guardrails.]
---

# Capabilities Registry

## Title
- Purpose:
- Entry points:
- CLI:
- Contracts:
- Tests:
- Notes: Do **not** re-implement; extend via layouts or themes only.
(Add more capability stubs and keep this current.)'

  write_file "docs/decisions/ADR-template.md" "EOFMD6" \
'# ADR N: Title
- Date: YYYY-MM-DD
- Status: Proposed | Accepted | Superseded by ADR M
## Context
What problem are we solving? Constraints?
## Decision
What is decided? Why this over alternatives?
## Consequences
Risks, migrations, sunsets, and how we’ll measure success.'

  write_file "ai/scripts/discover_capability.sh" "EOFSH3" \
'#!/usr/bin/env bash
set -euo pipefail
q="${1:-pptx}"
root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
echo "== Grepping for ${q} =="
if command -v rg >/dev/null 2>&1; then
  rg -n --hidden --glob "!**/node_modules/**" --glob "!**/.venv/**" "${q}" "${root}" | head -n 200
else
  grep -RIn --exclude-dir=node_modules --exclude-dir=.venv "${q}" "${root}" | head -n 200
fi
echo "== Known capabilities =="
if [ -f "${root}/ai/capabilities.md" ]; then
  grep -n "^## " "${root}/ai/capabilities.md" | sed "s/^/  /" || true
fi'
  chmod +x ai/scripts/discover_capability.sh

  # Install hooks
  if command -v python >/dev/null || command -v python3 >/dev/null; then
    PYBIN="$(command -v python || command -v python3)"
    "$PYBIN" - <<'PY' || true
import sys, subprocess
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "pre-commit"], check=False)
PY
    pre-commit install || true
    pre-commit install -t pre-push || true
  else
    echo "::warning:: Python not found; skipped pre-commit install"
  fi

  echo "-- Apply complete --"
}

# Show deprecation warning
echo "⚠️  DEPRECATION WARNING ⚠️"
echo "This unified script is deprecated. Please migrate to:"
echo "  ai_guardrails_bootstrap_modular.sh"
echo ""
echo "The modular script provides identical functionality with better maintainability."
echo "See docs/migration-guide.md for migration instructions."
echo ""
echo "Continuing with unified script..."
echo ""

# DISPATCH---------------------------------------------------------------------
case "$MODE" in
  doctor) doctor; [[ $REPAIR -eq 1 ]] && ensure_local ;;
  ensure) ensure_local ;;
  apply)  apply_bootstrap ;;
esac

echo "✅ Done. Next steps:
• Keep .ai/envelope.json updated while you work (and paste it into PRs)
• Push: pre-push runs quick tests + envelope scope check
• PR: CI enforces envelope + language-conditional jobs
• Consider enabling branch protection to require the CI jobs"
