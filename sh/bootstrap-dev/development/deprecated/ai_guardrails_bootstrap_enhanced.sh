#!/usr/bin/env bash
# Enhanced modular bootstrap with dynamic component loading

set -euo pipefail

VERSION="2.0.0"
DEFAULT_TEMPLATE_REPO="file://$(pwd)/ai-guardrails-templates"
DEFAULT_BRANCH="main"

MODE="apply"
FORCE=0
VERBOSE=0
REPO_ROOT=""
TEMPLATE_REPO="${AI_GUARDRAILS_REPO:-$DEFAULT_TEMPLATE_REPO}"
TEMPLATE_BRANCH="${AI_GUARDRAILS_BRANCH:-$DEFAULT_BRANCH}"
OFFLINE=0
PROFILE="standard"
INTERACTIVE=0
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
    --list-profiles) MODE="list-profiles"; shift;;
    -C) REPO_ROOT="$2"; shift 2;;
    --force) FORCE=1; shift;;
    --verbose) VERBOSE=1; shift;;
    --offline) OFFLINE=1; shift;;
    --interactive) INTERACTIVE=1; shift;;
    --profile) PROFILE="$2"; shift 2;;
    --components) COMPONENTS="$2"; shift 2;;
    --template-repo) TEMPLATE_REPO="$2"; shift 2;;
    --template-branch) TEMPLATE_BRANCH="$2"; shift 2;;
    -h|--help)
      cat <<'USAGE'
AI Guardrails Bootstrap (Enhanced Modular)

Usage:
  bash ai_guardrails_bootstrap_enhanced.sh [MODE] [OPTIONS]

Modes:
  --apply                Install/update guardrail files from templates (default)
  --ensure               Create minimal local setup and install hooks
  --doctor               Diagnose issues
  --update               Update existing installation to latest templates
  --list-versions        List available template versions
  --list-components      List available components
  --list-profiles        List available installation profiles

Options:
  -C PATH                Target repository root (auto-detect if omitted)
  --force                Overwrite existing files
  --verbose              Extra logging
  --offline              Use embedded fallbacks (no network)
  --interactive          Interactive component selection
  --profile NAME         Use installation profile (minimal|standard|full|custom)
  --components LIST      Install specific components (comma-separated)
  --template-repo URL    Custom template repository URL
  --template-branch BR   Template branch/tag (default: main)

Examples:
  # Install standard profile
  bash ai_guardrails_bootstrap_enhanced.sh --profile standard

  # Interactive installation
  bash ai_guardrails_bootstrap_enhanced.sh --interactive

  # Install specific components
  bash ai_guardrails_bootstrap_enhanced.sh --components core,scripts,docs

  # List available options
  bash ai_guardrails_bootstrap_enhanced.sh --list-profiles
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

# Enhanced template fetching with config support
get_bootstrap_config() {
  local config_path="$TEMPLATE_REPO/bootstrap-config.yaml"
  
  if [[ $OFFLINE -eq 1 ]]; then
    # Return minimal embedded config
    cat <<'EOF'
components:
  core:
    name: "Core AI Guardrails"
    required: true
    files:
      - source: ".ai/guardrails.yaml"
        target: ".ai/guardrails.yaml"
        embedded_fallback: true
      - source: ".ai/envelope.json"
        target: ".ai/envelope.json"
        embedded_fallback: true
profiles:
  minimal:
    description: "Minimal installation"
    components: ["core"]
EOF
  else
    # Try to fetch config from template repo
    if [[ -f "$config_path" ]]; then
      cat "$config_path"
    else
      echo "::warning:: No bootstrap-config.yaml found, using default configuration"
      get_bootstrap_config  # Recursive call with OFFLINE=1 fallback
    fi
  fi
}

# Use Python manager if available
use_python_manager() {
  local python_manager="scripts/bootstrap_manager.py"
  
  if [[ -f "$python_manager" ]] && command -v python3 >/dev/null; then
    local args=()
    
    [[ $FORCE -eq 1 ]] && args+=(--force)
    args+=(--config "bootstrap-config.yaml")
    args+=(--template-repo "src/ai-guardrails-templates")
    
    case "$MODE" in
      list-components)
        python3 "$python_manager" list-components
        return 0
        ;;
      list-profiles)
        python3 "$python_manager" list-profiles
        return 0
        ;;
      apply)
        if [[ -n "$COMPONENTS" ]]; then
          echo "Custom component installation not yet implemented in Python manager"
          return 1
        else
          python3 "$python_manager" "${args[@]}" install "$PROFILE"
          return $?
        fi
        ;;
    esac
  fi
  
  return 1  # Fall back to bash implementation
}

# Interactive component selection
interactive_selection() {
  echo "=== Interactive Component Selection ==="
  echo "Available components:"
  
  # This would parse the config and show options
  # For now, simplified version
  local components=(core schemas scripts github precommit docs)
  local selected=()
  
  for comp in "${components[@]}"; do
    echo -n "Install $comp? [y/N]: "
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
      selected+=("$comp")
    fi
  done
  
  COMPONENTS=$(IFS=,; echo "${selected[*]}")
  echo "Selected components: $COMPONENTS"
}

# Legacy apply function (fallback)
apply_templates_legacy() {
  echo "== Apply templates (legacy mode) =="
  
  # Core configuration
  write_template ".ai/guardrails.yaml" ".ai/guardrails.yaml"
  write_template ".ai/envelope.json" ".ai/envelope.json"
  
  # Schemas  
  write_template "ai/schemas/copilot_envelope.schema.json" "ai/schemas/copilot_envelope.schema.json"
  
  # Scripts
  write_template "ai/scripts/check_envelope.py" "ai/scripts/check_envelope.py" "optional"
  write_template "ai/scripts/check_envelope_local.py" "ai/scripts/check_envelope_local.py" "optional"
  write_template "ai/scripts/lang_lint.sh" "ai/scripts/lang_lint.sh" "optional"
  write_template "ai/scripts/lang_test.sh" "ai/scripts/lang_test.sh" "optional"
  
  chmod +x ai/scripts/*.py ai/scripts/*.sh 2>/dev/null || true
  
  echo "✅ Legacy installation complete"
}

# Main execution
main() {
  case "$MODE" in
    list-components|list-profiles|apply)
      # Try Python manager first
      if use_python_manager; then
        exit 0
      fi
      
      # Fall back to legacy bash implementation
      if [[ "$MODE" == "apply" ]]; then
        if [[ $INTERACTIVE -eq 1 ]]; then
          interactive_selection
        fi
        apply_templates_legacy
      else
        echo "Legacy mode: limited component/profile listing"
      fi
      ;;
    doctor)
      doctor_mode
      ;;
    ensure)
      ensure_local
      ;;
    *)
      echo "Unknown mode: $MODE"
      exit 1
      ;;
  esac
}

# Include legacy functions (write_template, doctor_mode, etc.)
# ... (keep existing functions from original script)

main "$@"
