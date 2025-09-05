#!/usr/bin/env bash
set -euo pipefail
shopt -s nullglob

read_cfg() {
  awk -v lang="$1" -v key="$2" '
    $0 ~ "^" lang ":" { f=1 }
    f && $0 ~ key ":" {
      val = substr($0, index($0, ":") + 2)
      gsub(/^"+|"+$/, "", val)
      print val
      exit
    }
  ' .ai/guardrails.yaml 2>/dev/null || true
}

# Function to check if a language is disabled
is_language_disabled() {
    local language="$1"
    local config_file=".ai/guardrails.yaml"

    if [[ ! -f "$config_file" ]]; then
        return 1  # Not disabled if no config file
    fi

    # Simple grep approach - check if the language appears in disabled_languages section
    if grep -A 20 "disabled_languages:" "$config_file" | grep -q "^\s*-\s*$language\s*"; then
        return 0  # Language is disabled
    else
        return 1  # Language is not disabled
    fi
}

# Reads a value from .ai/guardrails.yaml for a given language and key
py_lint=$(read_cfg python lint)
node_lint=$(read_cfg node lint)
go_lint=$(read_cfg go lint)
rust_lint=$(read_cfg rust lint)

if [[ -f pyproject.toml || -f requirements.txt || -n "$(find . -name '*.py' -print -quit)" ]]; then
  if is_language_disabled python; then
    echo "Python linting disabled in guardrails.yaml"
  elif [[ -n "${py_lint:-}" ]]; then
    bash -lc "$py_lint"
  elif command -v ruff >/dev/null; then
    ruff check .
  else
    echo "ruff not found; skipping python lint"
  fi
fi

if [[ -f package.json ]]; then
  if is_language_disabled node; then
    echo "Node.js linting disabled in guardrails.yaml"
  elif [[ -n "${node_lint:-}" ]]; then
    bash -lc "$node_lint"
  else
    npx -y eslint . || npx -y @biomejs/biome check . || echo "eslint/biome unavailable"
  fi
fi

if [[ -f go.mod ]]; then
  if is_language_disabled go; then
    echo "Go linting disabled in guardrails.yaml"
  elif [[ -n "${go_lint:-}" ]]; then
    bash -lc "$go_lint"
  elif command -v golangci-lint >/dev/null; then
    golangci-lint run
  else
    go vet ./... || true
  fi
fi

if [[ -f Cargo.toml ]]; then
  if is_language_disabled rust; then
    echo "Rust linting disabled in guardrails.yaml"
  elif [[ -n "${rust_lint:-}" ]]; then
    bash -lc "$rust_lint"
  elif command -v cargo >/dev/null; then
    cargo clippy --workspace -q -- -D warnings || echo "clippy not installed"
  fi
fi

if command -v shellcheck >/dev/null 2>&1; then find . -name '*.sh' -exec shellcheck {} + || true; fi
if command -v hadolint   >/dev/null 2>&1; then find . -type f -name 'Dockerfile*' -exec hadolint {} + || true; fi
if command -v markdownlint >/dev/null 2>&1; then markdownlint . || true; fi
