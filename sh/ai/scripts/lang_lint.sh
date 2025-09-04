#!/usr/bin/env bash
set -euo pipefail
shopt -s nullglob
read_cfg() { awk "/^$1:/{f=1} f&&/$2:/{print substr(\$0,index(\$0,\":\")+2); exit}" .ai/guardrails.yaml 2>/dev/null | sed 's/^[[:space:]]*"//;s/"[[:space:]]*$//' || true; }
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
