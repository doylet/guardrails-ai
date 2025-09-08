# ADR-004: Source Engine Architecture and Design

**Date:** 2025-09-06
**Status:** Proposed
**Deci### **Migration Effort**: Moderate refactoring of current `src/packages/` structure (not complete rewrite)ers:** Development Team, Bootstrap System Architects
**Technical Story:** Restructure src/ directory as pure engine with clean separation of concerns

---

## Context

The current `src/packages/` structure already provides a good foundation as the engine, but needs refinement to establish clearer boundaries between pure planning logic and side-effect operations. As we ship a single CLI that installs into the PWD and consolidate the installed layout under `./.ai/`, we need to evolve the existing structure into a **pure engine** with better separation of concerns.

### Current Structure Analysis
```
src/packages/               # Current engine (equivalent to proposed infra/)
├── core/bootstrap.py       # Main orchestrator ✅
├── managers/               # Component management ✅
│   ├── component_manager.py
│   ├── config_manager.py
│   ├── plugin_system.py
│   └── state_manager.py
├── operations/             # YAML operations ✅
│   ├── doctor.py
│   └── yaml_operations.py
└── utils/                  # Utilities ✅
```

### Current Issues
- Mixed responsibilities between planning and execution in component_manager.py
- No clear separation between pure and effectful operations
- Lack of transactional safety for component installation
- Missing receipt-driven idempotency tracking
- No formal domain models or typed exceptions

---

## Decision

We refactor the existing `src/packages/` structure to implement clean separation of concerns while preserving the working system. The current `packages/` becomes our engine with better-defined roles and boundaries.

### **Evolved Structure (Engine + Payloads)**

```
bootstrap-dev/
  src/
    packages/                    # Evolved engine (renamed to infra/ in future)
      cli/                       # NEW: CLI parsing and coordination
        __init__.py
        main.py                  # entry: plan/install/uninstall/list/doctor
        args.py
      core/                      # REFINED: Pure application logic
        bootstrap.py             # → orchestrator.py (rename)
        planner.py               # NEW: builds InstallPlan (pure)
        installer.py             # NEW: executes InstallPlan (side effects)
        resolver.py              # NEW: manifest loading/deps/conflicts
      managers/                  # → adapters/ (rename & refactor)
        component_manager.py     # SPLIT: → planner.py + installer.py
        config_manager.py        # → adapters/yaml_ops.py
        plugin_system.py         # → core/resolver.py
        state_manager.py         # → adapters/receipts.py
      operations/                # → adapters/ (merge)
        doctor.py                # → core/doctor.py
        yaml_operations.py       # → adapters/yaml_ops.py
      domain/                    # NEW: Pure types and rules
        model.py                 # dataclasses: Plugin, Component, FileAction, InstallPlan
        errors.py                # typed exceptions (ConflictError, DepError, DriftError)
        constants.py             # defaults (GUARDRAILS_DIR=".ai", hook names, etc.)
      adapters/                  # NEW: IO/infra details behind small interfaces
        fs.py                    # atomic writes, staging/backup/promote, safe cleanup
        yaml_ops.py              # merge/template ops; single funnel for content edits
        git.py                   # (optional) commit-range diff helpers for CI usage
        schema.py                # JSONSchema validators (manifest, state, target structure)
        hashing.py               # sha256 for source/target/manifest digests
        receipts.py              # read/write .ai/guardrails/installed/*.json (in target)
        logging.py               # structured logs; quiet/verbose control
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
```

---

## Consequences

### **Positive**

1. **Clear Separation**: Pure planning logic separated from side effects
2. **Transaction Safety**: Component-level staging/backup/rollback prevents corruption
3. **Deterministic**: Plans are stable, logged, and testable
4. **Idempotent**: Receipt tracking prevents unnecessary operations
5. **Safe Cleanup**: Sentinel files prevent accidental deletions

### **Negative/Risks**

1. **Migration Effort**: Significant refactoring of current `src/packages/` structure
2. **Complexity**: More abstraction layers may increase learning curve
3. **Performance**: Additional validation and receipt tracking overhead

### **Component Responsibilities**

#### **domain/ (Pure Types & Rules)**

* `InstallPlan`, `Component`, `FileAction(kind, src, dst, mode, reason)`, `Receipt`.
* No IO. Deterministic, unit-testable.

#### **core/ (Application Logic)**

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

#### **adapters/ (Infrastructure Details)**

* `fs.py`: atomic\_write, safe\_mkdir, `with staging(component): …`, `promote()`, `rollback()`, **sentinel** file enforcement (only delete dirs you created this run).
* `yaml_ops.py`: single merge/transform funnel for YAML/JSON. (No ad-hoc edits elsewhere.)
* `schema.py`: validators for **plugin manifest**, **core manifest**, **target structure**, and **state/receipts**.
* `receipts.py`: read/write receipts; “is\_current(component)” lives here (planner calls it).
* `git.py`: (optional) diff helper used in CI flows to compute PR changes.
* `hashing.py`: sha256 helpers.

---

## Implementation Plan

### **CLI Behavior Examples**

* `ai-guardrails plan --profile full`
`orchestrator` `resolver` `planner` print the plan (no IO, deterministic).
* `ai-guardrails install --profile full [--dry-run|--force]`
Resolver Planner Installer (per component): staging + backup + promote + receipts.
Writes under target’s `./.ai/…` and other declared targets (e.g., `.githooks`, `.github/workflows`).
* `ai-guardrails doctor [--repair]`
`doctor` checks receipts, schema, conflicts, deps; optional targeted repairs.

---

### **Data Models**

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

### **Architecture Rules**

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

### **Payload Organization**

* **Templates**: the **default payload** your engine can install (dispatcher hook, default workflows, default `.ai/guardrails/*` policy, core **policy scripts** that will live under the target’s `./.ai/scripts/policy/…`).
* **Plugins**: each `<id>-kit/` keeps `plugin-manifest.yaml` + `files/…` tree; the engine copies from here into the target. (Same format you’re using todayjust ensure they now target `./.ai/scripts/...` etc.)

---

### **Entry Point Design**

* `bin/ai-guardrails-bootstrap`:

  ```bash
  #!/usr/bin/env bash
  exec python -m packages.cli.main "$@"  # Updated from infra.cli.main
  ```
* `packages/cli/main.py`:

* parses args calls `orchestrator.run(args)`.

---

---

## Migration Strategy

### **Current → Future Mapping**
```
# Existing (Working System)          # Evolved (Clean Architecture)
src/packages/core/bootstrap.py    →  src/packages/core/orchestrator.py
src/packages/managers/             →  Split across core/ + adapters/
  component_manager.py             →    core/planner.py + core/installer.py
  plugin_system.py                 →    core/resolver.py
  config_manager.py                →    adapters/yaml_ops.py
  state_manager.py                 →    adapters/receipts.py
src/packages/operations/           →  Move to adapters/ + core/
  yaml_operations.py               →    adapters/yaml_ops.py (merge)
  doctor.py                        →    core/doctor.py
```

### **Phase 1: Foundation (Week 1-2)**
- [ ] Create new directories: `domain/`, `adapters/`, `cli/`
- [ ] Define domain models in `domain/model.py` (`InstallPlan`, `FileAction`, etc.)
- [ ] Move existing code with minimal changes to new locations
- [ ] Preserve all existing functionality during transition

### **Phase 2: Core Logic Separation (Week 3-4)**
- [ ] Split `component_manager.py` into pure `planner.py` + effectful `installer.py`
- [ ] Extract resolution logic from `plugin_system.py` into `resolver.py`
- [ ] Build transaction safety in `installer.py` with staging/backup/promote
- [ ] Add receipt tracking in `adapters/receipts.py`

### **Phase 3: Integration (Week 5-6)**
- [ ] Rename `bootstrap.py` to `orchestrator.py` and wire new components
- [ ] Update CLI (`bin/ai-guardrails-bootstrap`) to use new architecture
- [ ] Ensure backward compatibility for existing installations
- [ ] Add new CLI commands: `plan`, `--dry-run`

### **Phase 4: Validation & Cleanup (Week 7-8)**
- [ ] Comprehensive testing of transaction safety
- [ ] Performance validation (ensure no regression)
- [ ] Optional: Rename `packages/` to `infra/` for clarity
- [ ] Documentation updates

---

## Success Metrics

**Technical:**
- Zero data loss during component installation
- 100% transaction rollback success rate
- Deterministic plans across identical environments
- Receipt accuracy (hash validation)

**User Experience:**
- Clear `--plan` output showing intended changes
- Successful `--dry-run` preview capability
- Reliable `doctor --repair` functionality
- < 2 second response time for planning

---

## Related Decisions

- **ADR-001:** Modular Bootstrap Architecture - Foundation this builds upon
- **ADR-003:** Example Template Idempotency Strategy - Will be implemented within this engine
- **Future ADR:** Plugin API Standards - Will define interfaces for plugin manifests

---

## Why This Design Works

* **Deterministic**: plan is stable, logged, and testable.
* **Safe**: staging/backup/receipts + sentinel cleanup.
* **Simple mental model**: payloads are just files under `src/ai-guardrails-templates` and `src/plugins/.../files`; engine is pure Python under `src/infra`.
* **Aligned with `.ai/` consolidation**: all script references in payloads point at `./.ai/scripts/policy/...` so targets stay clean and hidden.

---

**Status:** 🟡 Awaiting Implementation
**Next Review:** Post-Phase 1 completion
**Owner:** Bootstrap System Team
