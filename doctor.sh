Great question. You’ve got a real mix across C/Node/Python/Ruby/Rust projects (e.g., `Zero-Latency`, `ai_deck_gen`, `roam-research-mcp`, Rails-style trees). A consistent scheme will save you from import/path weirdnessespecially when switching OSes or packaging.&#x20;

# A simple, durable policy

## Layer 1: Repos & top-level folders

* **kebab-case** only (all lowercase, dashes): `zero-latency`, `ai-deck-gen`, `docsearch`.
* No spaces or uppercase; ASCII only.
* Reason: works cleanly in URLs, npm, Cargo, Docker tags, CI paths.

## Layer 2: Language-specific inside each repo

### Python

* **Package & module dirs/files:** `snake_case` (`ai_deck_gen/`, `vector_store.py`)
* **Distribution/project name (`pyproject.toml [project].name`):** kebab-case (`ai-deck-gen`)
* **Classes:** `CapWords` (`VectorStore`)
* **Constants:** `UPPER_SNAKE`
* Why: imports break on hyphens; PyPI package names typically kebab/normalized.

### Node/TypeScript

* **package.json "name":** kebab-case (`roam-research-mcp`)
* **Folders/files:** kebab-case by default (`editor-collab/server`); **React components** may use `PascalCase.tsx`
* **Classes:** `PascalCase`
* **Constants:** `SCREAMING_SNAKE`

### Rust

* **Crate/package names (Cargo.toml):** kebab-case (`zero-latency-core`)
* **Module files/dirs:** `snake_case.rs` (`vector_search.rs`)
* **Types/traits/enums:** `PascalCase` (`VectorSearch`, `SearchError`)
* **Constants/features:** `SCREAMING_SNAKE` / feature flags `snake_case`
* Note: Rust maps crate `zero-latency` `zero_latency` in paths automatically.

### C

* **Dirs/files:** `snake_case` (`tcp_server/src`, `request_parser.c`, `request_parser.h`)
* **Macros:** `SCREAMING_SNAKE`
* **lib names:** `libname.so`/`libname.a`

### Ruby / Rails

* **Gem name:** kebab or snake are both common; prefer **kebab** externally (`print-system`) and **snake** in require paths (`require "print_system"`).
* **Rails app folder:** `snake_case`
* **Classes/Modules:** `CamelCase`

## Cross-cutting rules

* Pick **one** separator per layer (kebab for repos/packages; snake for importable module/file names).
* Avoid mixing `-` and `_` at the same layer.
* Never rely on case for meaning (macOS often case-insensitive; Linux isn’t).

# Rename mapping (practical examples)

* **Repo branding vs code imports**

* Repo: `zero-latency`
* Rust crate: `zero-latency-core` import path `zero_latency_core`
* Python project: `ai-deck-gen` (dist) import `ai_deck_gen`
* Your current examples:

* `Zero-Latency` **rename repo** to `zero-latency`; keep Rust crates kebab, modules snake.
* `ai_deck_gen` repo `ai-deck-gen`; Python package dir stays `ai_deck_gen`.

# Migration checklist (fast & safe)

1. **Decide the canonical forms**

* Repos: kebab
* Python packages/modules: snake
* Node packages / Rust crates: kebab (files snake for Rust modules)
2. **Search & fix hardcoded paths**

   ```bash
   rg -nS --hidden --glob '!.git' '(Zero[-_]Latency|ai[_-]deck[_-]gen|[A-Z].*[A-Z])'
   ```
3. **Rename with Git to keep history**

   ```bash
   git mv Zero-Latency zero-latency
   ```
4. **Update manifests**

* Python: `[project].name = "ai-deck-gen"` (imports unchanged)
* Node: `"name": "roam-research-mcp"`
* Rust: `package.name = "zero-latency-core"` (Cargo updates lock/metadata)
5. **CI & scripts**

* Fix `working-directory`, Docker contexts, launchd/systemd unit paths.
6. **Guardrails in CI** (fails on new violations)

   ```bash
   # disallow uppercase or spaces in paths (except .git)
   if find . -path ./.git -prune -o -regex '.*[[:upper:][:space:]].*' -print | grep -q .; then
     echo "Path names must be lowercase and dash_or_underscore only"; exit 1; fi
   ```

# One-page team standard (drop-in)

* **Repos/Packages:** kebab-case
* **Importable code (modules/files):** snake\_case
* **Types/classes:** PascalCase
* **Constants/macros:** SCREAMING\_SNAKE
* **React components:** PascalCase files allowed
* **No uppercase or spaces in paths**
* **Python:** dist name kebab, import name snake
* **Rust:** crate kebab, module files snake (Cargo maps automatically)

If you want, I can produce a quick “rename plan” for a specific repo (commands + manifest diffs) and a tiny pre-commit hook to enforce this going forward.