#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# AI Guardrails Bootstrap (Modular)
#
# This version fetches templates from a repository instead of embedding them.
# Provides better versioning, easier maintenance, and selective updates.
# ============================================================================

VERSION="1.0.0"
DEFAULT_TEMPLATE_REPO="file://$(pwd)/ai-guardrails-templates"
DEFAULT_BRANCH="main"

MODE="apply"
FORCE=0
VERBOSE=0
REPO_ROOT=""
TEMPLATE_REPO="${AI_GUARDRAILS_REPO:-$DEFAULT_TEMPLATE_REPO}"
TEMPLATE_BRANCH="${AI_GUARDRAILS_BRANCH:-$DEFAULT_BRANCH}"
OFFLINE=0
PROFILE=""
COMPONENTS=""

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --apply) MODE="apply"; shift;;
    --ensure) MODE="ensure"; shift;;
    --doctor) MODE="doctor"; shift;;
    --update) MODE="update"; shift;;
    --list-versions) MODE="list-versions"; shift;;
    --list-components) MODE="list-components"; shift;;
    --profile) PROFILE="$2"; shift 2;;
    --components) COMPONENTS="$2"; shift 2;;
    -C) REPO_ROOT="$2"; shift 2;;
    --force) FORCE=1; shift;;
    --verbose) VERBOSE=1; shift;;
    --offline) OFFLINE=1; shift;;
    --template-repo) TEMPLATE_REPO="$2"; shift 2;;
    --template-branch) TEMPLATE_BRANCH="$2"; shift 2;;
    -h|--help)
      cat <<'USAGE'
AI Guardrails Bootstrap (Modular)

Usage:
  bash ai_guardrails_bootstrap_modular.sh [MODE] [OPTIONS]

Modes:
  --apply         Install/update guardrail files from templates (default)
  --ensure        Create minimal local setup and install hooks
  --doctor        Diagnose issues
  --update        Update existing installation to latest templates
  --list-versions List available template versions
  --list-components List available installation components

Options:
  -C PATH               Target repository root (auto-detect if omitted)
  --force               Overwrite existing files
  --verbose             Extra logging
  --offline             Use embedded fallbacks (no network)
  --profile NAME        Use installation profile (minimal|standard|full)
  --components LIST     Install specific components (comma-separated)
  --template-repo URL   Custom template repository URL
  --template-branch BR  Template branch/tag (default: main)

Environment:
  AI_GUARDRAILS_REPO    Override default template repository
  AI_GUARDRAILS_BRANCH  Override default branch

Examples:
  # Install latest templates
  bash ai_guardrails_bootstrap_modular.sh

  # Update to specific version
  bash ai_guardrails_bootstrap_modular.sh --update --template-branch v1.2.0

  # Install offline using embedded templates
  bash ai_guardrails_bootstrap_modular.sh --offline

  # Use custom template repo
  bash ai_guardrails_bootstrap_modular.sh --template-repo https://internal.company.com/ai-templates
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

cd "$REPO_ROOT" || exit 1
echo "→ Target repo: $REPO_ROOT"

log() { [[ $VERBOSE -eq 1 ]] && echo "[debug] $*"; }

# ----------------------------------------------------------------------------
# Component definitions
get_components() {
  case "$1" in
    "core")
      echo ".ai/guardrails.yaml .ai/envelope.json"
      ;;
    "schemas") 
      echo "ai/schemas/copilot_envelope.schema.json"
      ;;
    "scripts")
      echo "ai/scripts/check_envelope.py ai/scripts/check_envelope_local.py ai/scripts/lang_lint.sh ai/scripts/lang_test.sh"
      ;;
    "github")
      echo ".github/workflows/ai_guardrails_on_commit.yml .github/pull_request_template.md .github/chatmodes/blueprint-mode-mod.chatmode.md"
      ;;
    "precommit")
      echo ".pre-commit-config.yaml"
      ;;
    "docs")
      echo "ai/capabilities.md docs/decisions/0000-ADR-template.md"
      ;;
    *)
      echo ""
      ;;
  esac
}

get_profile_components() {
  case "$1" in
    "minimal")
      echo "core schemas"
      ;;
    "standard")
      echo "core schemas scripts docs precommit"
      ;;
    "full")
      echo "core schemas scripts github docs precommit"
      ;;
    *)
      echo "core schemas scripts docs"  # default
      ;;
  esac
}

list_components() {
  echo "== Available Components =="
  echo "  core      - Core AI guardrails configuration (.ai/ files)"
  echo "  schemas   - JSON schemas for validation"
  echo "  scripts   - Automation scripts (Python/bash)"
  echo "  github    - GitHub workflows and templates"
  echo "  precommit - Pre-commit hooks configuration"
  echo "  docs      - Documentation templates"
  echo ""
  echo "== Available Profiles =="
  echo "  minimal   - core, schemas"
  echo "  standard  - core, schemas, scripts, docs, precommit (default)"
  echo "  full      - all components including GitHub integration"
}

# ----------------------------------------------------------------------------
# Template fetching
fetch_template() {
  local template_path="$1"
  local target_path="$2"

  if [[ $OFFLINE -eq 1 ]]; then
    fetch_embedded_template "$template_path" "$target_path"
    return
  fi

  # For file:// URLs, direct file access with proper path handling
  if [[ "$TEMPLATE_REPO" =~ ^file:// ]]; then
    # Remove templates/ prefix if it's already in the template_path
    if [[ "$template_path" =~ ^templates/ ]]; then
      local url="${TEMPLATE_REPO}/${template_path}"
    else
      local url="${TEMPLATE_REPO}/${template_path}"
    fi
  else
    local url="${TEMPLATE_REPO}/${TEMPLATE_BRANCH}/${template_path}"
  fi
  log "Fetching: $url"

  if command -v curl >/dev/null 2>&1; then
    if curl -fsSL "$url" -o "$target_path.tmp" 2>/dev/null; then
      mv "$target_path.tmp" "$target_path"
      echo "fetched: $target_path"
      return 0
    fi
  elif command -v wget >/dev/null 2>&1; then
    if wget -q "$url" -O "$target_path.tmp" 2>/dev/null; then
      mv "$target_path.tmp" "$target_path"
      echo "fetched: $target_path"
      return 0
    fi
  fi

  echo "::warning:: Failed to fetch $template_path, using embedded fallback"
  fetch_embedded_template "$template_path" "$target_path"
}

fetch_embedded_template() {
  local template_path="$1"
  local target_path="$2"

  # Minimal embedded fallbacks for key files
  case "$template_path" in
    ".ai/guardrails.yaml")
      cat > "$target_path" <<'EOF'
python:
  lint: "ruff check ."
  type: "mypy ."
  test: "pytest -q"
node:
  lint: "npx -y eslint . || npx -y @biomejs/biome check ."
  type: "npx -y tsc --noEmit"
  test: "npm test --silent || pnpm -s test || yarn -s test"
go:
  lint: "golangci-lint run || (go vet ./... && echo 'fallback go vet ok')"
  test: "go test ./..."
rust:
  lint: "cargo clippy --no-deps -q -D warnings || echo 'clippy not installed'"
  test: "cargo test --quiet"
generic:
  shell: "shellcheck **/*.sh || echo 'shellcheck not found'"
  markdown: "markdownlint . || echo 'markdownlint not found'"
EOF
      ;;
    ".ai/envelope.json")
      cat > "$target_path" <<'EOF'
{
  "discovery": [], "assumptions": [], "plan": [], "changes": [], "tests": [],
  "validation": { "commands": [], "results": [] },
  "limits": { "files_touched": 5, "workflow": "Main" },
  "risks": [], "rollback": [], "question": null, "status": "READY_FOR_REVIEW"
}
EOF
      ;;
    "ai/schemas/copilot_envelope.schema.json")
      cat > "$target_path" <<'EOF'
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Copilot Envelope",
  "type": "object",
  "properties": {
    "discovery": { "type": "array" },
    "assumptions": { "type": "array" },
    "plan": { "type": "array" },
    "changes": { "type": "array" },
    "tests": { "type": "array" },
    "validation": { "type": "object" },
    "limits": { "type": "object" },
    "risks": { "type": "array" },
    "rollback": { "type": "array" },
    "question": { "type": ["string", "null"] },
    "status": { "type": "string" }
  }
}
EOF
      ;;
    ".pre-commit-config.yaml"|"templates/.pre-commit-config.yaml")
      cat > "$target_path" <<'EOF'
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-merge-conflict
      - id: check-yaml
  - repo: local
    hooks:
      - id: ai-lint
        name: AI Guardrails Lint
        entry: ai/scripts/lang_lint.sh
        language: script
        pass_filenames: false
        always_run: true
EOF
      ;;
    *)
      echo "::error:: No embedded fallback for $template_path"
      return 1
      ;;
  esac
  echo "embedded: $target_path"
}

write_template() {
  local template_path="$1"
  local target_path="$2"
  local optional="${3:-false}"

  mkdir -p "$(dirname "$target_path")"

  if [[ -e "$target_path" && $FORCE -eq 0 ]]; then
    echo "skip (exists): $target_path"
    return 0
  fi

  if fetch_template "$template_path" "$target_path"; then
    return 0
  elif [[ "$optional" == "true" && $OFFLINE -eq 1 ]]; then
    echo "skip (optional): $target_path"
    return 0
  else
    return 1
  fi
}

# Get current installed version
get_installed_version() {
  if [[ -f .ai/guardrails.version ]]; then
    cat .ai/guardrails.version
  else
    echo "unknown"
  fi
}

# Get latest available version
get_latest_version() {
  if [[ $OFFLINE -eq 1 ]]; then
    echo "$VERSION"
    return
  fi

  local url="${TEMPLATE_REPO}/${TEMPLATE_BRANCH}/version.txt"
  if command -v curl >/dev/null 2>&1; then
    curl -fsSL "$url" 2>/dev/null || echo "$VERSION"
  elif command -v wget >/dev/null 2>&1; then
    wget -qO- "$url" 2>/dev/null || echo "$VERSION"
  else
    echo "$VERSION"
  fi
}

# ----------------------------------------------------------------------------
# Modes

doctor() {
  echo "== Doctor =="

  # Basic tools
  command -v bash >/dev/null || { echo "::error:: bash not found"; exit 1; }
  command -v git >/dev/null || { echo "::error:: git not found"; exit 1; }

  # Network tools
  if ! command -v curl >/dev/null && ! command -v wget >/dev/null; then
    echo "::warning:: Neither curl nor wget found. Use --offline mode."
  fi

  # Python
  if ! command -v python >/dev/null && ! command -v python3 >/dev/null; then
    echo "::warning:: Python not found; pre-commit install may be skipped."
  fi

  # Version info
  local installed=$(get_installed_version)
  local latest=$(get_latest_version)
  echo "Installed version: $installed"
  echo "Latest version: $latest"

  if [[ "$installed" != "$latest" && "$installed" != "unknown" ]]; then
    echo "🔄 Update available! Run with --update"
  fi

  # Check key files
  local key_files=(".ai/guardrails.yaml" ".ai/envelope.json" "ai/schemas/copilot_envelope.schema.json")
  local missing=0
  for f in "${key_files[@]}"; do
    if [[ ! -f "$f" ]]; then
      echo "::warning:: missing: $f"
      missing=1
    fi
  done

  if [[ $missing -eq 1 ]]; then
    echo "⚠️  Some files are missing. Run with --apply to install."
  else
    echo "✅ Key files present."
  fi

  echo "-- Doctor complete --"
}

ensure_local() {
  echo "== Ensure local setup =="

  mkdir -p .ai

  # Ensure envelope exists
  if [[ ! -f .ai/envelope.json ]]; then
    write_template ".ai/envelope.json" ".ai/envelope.json"
  fi

  # Install pre-commit if config exists
  if [[ -f .pre-commit-config.yaml ]] && command -v python >/dev/null; then
    python -m pip install -q pre-commit 2>/dev/null || true
    pre-commit install || true
    pre-commit install -t pre-push || true
    echo "Installed pre-commit hooks"
  fi

  echo "-- Ensure complete --"
}

apply_templates() {
  echo "== Apply templates =="

  # Determine what components to install
  local components_to_install
  if [[ -n "$COMPONENTS" ]]; then
    # Specific components requested
    components_to_install="$COMPONENTS"
    echo "Installing components: $components_to_install"
  elif [[ -n "$PROFILE" ]]; then
    # Profile requested
    components_to_install=$(get_profile_components "$PROFILE")
    echo "Installing profile '$PROFILE': $components_to_install"
  else
    # Default to standard profile
    components_to_install=$(get_profile_components "standard")
    echo "Installing default profile: $components_to_install"
  fi

  # Convert comma-separated to space-separated
  components_to_install=$(echo "$components_to_install" | tr ',' ' ')

  # Install each component
  for component in $components_to_install; do
    install_component "$component"
  done

  # Update .gitignore
  if [[ ! -f .gitignore ]] || ! grep -q '^\.ai/envelope\.json$' .gitignore; then
    echo ".ai/envelope.json" >> .gitignore
    echo "Updated .gitignore"
  fi

  # Record installed version
  get_latest_version > .ai/guardrails.version

  # Install hooks
  ensure_local

  echo "-- Apply complete --"
}

install_component() {
  local component="$1"
  local files=$(get_components "$component")
  
  if [[ -z "$files" ]]; then
    echo "::warning:: Unknown component: $component"
    return 1
  fi

  echo "Installing component: $component"
  
  for file_path in $files; do
    # Handle special cases for template structure
    local template_path="$file_path"
    if [[ "$file_path" =~ ^\.github/ ]] || [[ "$file_path" =~ ^docs/ ]] || [[ "$file_path" == ".pre-commit-config.yaml" ]]; then
      template_path="templates/$file_path"
    fi
    
    local optional="false"
    # Scripts are optional in offline mode
    if [[ "$component" == "scripts" ]] || [[ "$component" == "github" ]]; then
      optional="true"
    fi
    
    write_template "$template_path" "$file_path" "$optional"
  done

  # Post-install actions
  case "$component" in
    "scripts")
      chmod +x ai/scripts/*.py ai/scripts/*.sh 2>/dev/null || true
      ;;
  esac
}

update_installation() {
  echo "== Update installation =="

  local current=$(get_installed_version)
  local latest=$(get_latest_version)

  echo "Current: $current"
  echo "Latest: $latest"

  if [[ "$current" == "$latest" && $FORCE -eq 0 ]]; then
    echo "Already up to date. Use --force to reinstall."
    return 0
  fi

  FORCE=1  # Force overwrite during updates
  apply_templates

  echo "Updated from $current to $latest"
}

list_versions() {
  echo "== Available versions =="

  if [[ $OFFLINE -eq 1 ]]; then
    echo "Embedded version: $VERSION"
    return
  fi

  # This would ideally list tags/releases from the template repo
  # For now, just show current info
  echo "Current template branch: $TEMPLATE_BRANCH"
  echo "Latest version: $(get_latest_version)"
  echo "Installed version: $(get_installed_version)"
}

# ----------------------------------------------------------------------------
# Dispatch

case "$MODE" in
  doctor) doctor ;;
  ensure) ensure_local ;;
  apply) apply_templates ;;
  update) update_installation ;;
  list-versions) list_versions ;;
  list-components) list_components ;;
esac

echo "✅ Done."
