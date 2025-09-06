Great q. Since you’re shipping a single CLI (installed to `~/.local/bin/...`) that **installs into the PWD** and you’re consolidating the installed layout under `./.ai/…`, the `src/` tree should be the **engine** only: pure Python that plans, validates, and applies installs; plus the built-in assets (templates) and first-party plugins it knows how to copy.

Here’s an idiomatic, low-friction `src/` design that fits what you have now (keeps your “infra” vibe), but tightens roles and boundaries.

# Top-level shape (engine + payloads)

```
bootstrap-dev/
  src/
    infra/                       # the engine (pure python, no project writes here)
      cli/
        __init__.py
        main.py                  # entry: plan/install/uninstall/list/doctor
        args.py
      core/
        planner.py               # builds an InstallPlan (pure)
        installer.py             # executes an InstallPlan (side effects)
        resolver.py              # loads manifests, resolves deps, detects conflicts
        orchestrator.py          # ties resolver→planner→installer; handles --dry-run/--plan
        doctor.py                # drift, schema, deps/conflicts checks; --repair
      adapters/                  # IO/infra details behind small interfaces
        fs.py                    # atomic writes, staging/backup/promote, safe cleanup
        yaml_ops.py              # merge/template ops; single funnel for content edits
        git.py                   # (optional) commit-range diff helpers for CI usage
        schema.py                # JSONSchema validators (manifest, state, target structure)
        hashing.py               # sha256 for source/target/manifest digests
        receipts.py              # read/write .ai/guardrails/installed/*.json (in target)
        logging.py               # structured logs; quiet/verbose control
      domain/
        model.py                 # dataclasses: Plugin, Component, FileAction, InstallPlan…
        errors.py                # typed exceptions (ConflictError, DepError, DriftError…)
        constants.py             # defaults (GUARDRAILS_DIR=".ai", hook names, etc.)
    ai-guardrails-templates/     # built-in payloads (copied into target on install)
      .githooks/                 # shims/dispatcher (referencing ./.ai/scripts/…)
      .github/workflows/
      .ai/guardrails/            # default policy files
      .ai/scripts/policy/        # core check scripts delivered to targets
    plugins/                     # first-party plugins (payloads + manifests)
      <plugin-id>-kit/
        plugin-manifest.yaml     # your current plugin manifest
        files/…                  # everything this plugin drops into a target
    installation-manifest.yaml   # your core manifest (components/profiles)
    bin/
      ai-guardrails-bootstrap    # tiny shim → `python -m infra.cli.main …`
```

> **Boundary:** `infra/*` never touches your dev repo; it only reads manifests/assets under `src/` and writes to the **target** (PWD or `--target`) using the adapters. Assets under `ai-guardrails-templates/` + `plugins/*/files/` are the **payloads** copied into targets.

---

# Responsibilities (quick mental model)

## domain/ (pure types & rules)

* `InstallPlan`, `Component`, `FileAction(kind, src, dst, mode, reason)`, `Receipt`.
* No IO. Deterministic, unit-testable.

## core/ (application logic)

* `resolver.py`:

* Load & JSON-schema validate: `installation-manifest.yaml` + `plugins/*/plugin-manifest.yaml`.
* Resolve deps/capabilities; compute a deterministic order `(priority, plugin.id)`.
* Detect **component/path conflicts** raise `ConflictError`.
* Output a **ResolvedSpec** (ready for planning).
* `planner.py`:

* Build **InstallPlan**: per file decide `COPY | MERGE | TEMPLATE | SKIP`, compute reasons (`new | hash-diff | unchanged | drift`) by comparing source hashes vs existing target + **receipts**.
* No writes.
* `installer.py`:

* Execute the plan **per component** with **staging verify promote** and **backup/rollback**.
* Write **receipts** (`.ai/guardrails/installed/<component>.json`) including source & manifest digests, file hashes, size, mode.
* `doctor.py`:

* Validate state, receipts vs disk (drift), manifest health, target structure schema.
* Optional `--repair` to restore missing/changed files from sources (idempotent).
* `orchestrator.py`:

* CLI orchestration: `--plan`, `--dry-run`, `--force`, common logging, error mapping.

## adapters/ (infrastructure details)

* `fs.py`: atomic\_write, safe\_mkdir, `with staging(component): …`, `promote()`, `rollback()`, **sentinel** file enforcement (only delete dirs you created this run).
* `yaml_ops.py`: single merge/transform funnel for YAML/JSON. (No ad-hoc edits elsewhere.)
* `schema.py`: validators for **plugin manifest**, **core manifest**, **target structure**, and **state/receipts**.
* `receipts.py`: read/write receipts; “is\_current(component)” lives here (planner calls it).
* `git.py`: (optional) diff helper used in CI flows to compute PR changes.
* `hashing.py`: sha256 helpers.

---

# How this maps to your CLI behaviour

* `ai-guardrails plan --profile full`
`orchestrator` `resolver` `planner` print the plan (no IO, deterministic).
* `ai-guardrails install --profile full [--dry-run|--force]`
Resolver Planner Installer (per component): staging + backup + promote + receipts.
Writes under target’s `./.ai/…` and other declared targets (e.g., `.githooks`, `.github/workflows`).
* `ai-guardrails doctor [--repair]`
`doctor` checks receipts, schema, conflicts, deps; optional targeted repairs.

---

# Data shapes (sketch)

```python
# domain/model.py
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Sequence

ActionKind = Literal["COPY", "MERGE", "TEMPLATE", "SKIP"]
Reason     = Literal["new", "hash-diff", "unchanged", "drift"]

@dataclass(frozen=True)
class FileAction:
    kind: ActionKind
    src: Path
    dst: Path
    mode: int | None
    reason: Reason

@dataclass(frozen=True)
class ComponentPlan:
    name: str
    actions: Sequence[FileAction]
    manifest_digest: str
    plugin_id: str | None

@dataclass(frozen=True)
class InstallPlan:
    components: Sequence[ComponentPlan]
```

Installer consumes `InstallPlan`; planner produces it; receipts mirror it.

---

# Rules that keep `src/` tidy and reliable

1. **PureEffectful split:**
Planner/Resolver are pure; Installer/Doctor are the only writers.

2. **One funnel for edits:**
Any file content transformation (**YAML/JSON merges**, templating) goes through `yaml_ops.py`. Everywhere else is byte copy.

3. **Transactions per component:**
Every component uses: `stage verify promote` with a **backup** and **rollback** on error.

4. **Receipts drive idempotency:**
Planner asks `receipts.is_current(component)`; no-op unless `--force` or drift.

5. **Never `rm -rf` without a sentinel:**
All temporary dirs (`.staging/<component>`, `.backup/<component>`) get a marker file so `fs.cleanup` refuses to delete anything else.

6. **Schema is enforcement, not documentation:**
Apply **target structure** schema before any write and after each component; fail fast + rollback if invalid.

---

# What to put in `ai-guardrails-templates/` and `plugins/`

* **Templates**: the **default payload** your engine can install (dispatcher hook, default workflows, default `.ai/guardrails/*` policy, core **policy scripts** that will live under the target’s `./.ai/scripts/policy/…`).
* **Plugins**: each `<id>-kit/` keeps `plugin-manifest.yaml` + `files/…` tree; the engine copies from here into the target. (Same format you’re using todayjust ensure they now target `./.ai/scripts/...` etc.)

---

# Minimal entrypoint wiring

* `bin/ai-guardrails-bootstrap`:

  ```bash
  #!/usr/bin/env bash
  exec python -m infra.cli.main "$@"
  ```
* `infra/cli/main.py`:

* parses args calls `orchestrator.run(args)`.

---

# Why this design works for your PWD installer

* **Deterministic**: plan is stable, logged, and testable.
* **Safe**: staging/backup/receipts + sentinel cleanup.
* **Simple mental model**: payloads are just files under `src/ai-guardrails-templates` and `src/plugins/.../files`; engine is pure Python under `src/infra`.
* **Aligned with `.ai/` consolidation**: all script references in payloads point at `./.ai/scripts/policy/...` so targets stay clean and hidden.

If you want, I can sketch the exact module/function stubs (empty bodies + docstrings) for `infra/core/*` so you can drop them into your tree and let Copilot fill in implementation safely.
