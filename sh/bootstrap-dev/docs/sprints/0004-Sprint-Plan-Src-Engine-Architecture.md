# 0004-Sprint-Plan-Src-Engine-Architecture

**Date:** 2025-09-06
**Status:** 🟡 PLANNED
**Priority:** High
**Related:** [ADR-004-src-engine-design.md], [ADR-001-modular-bootstrap-architecture.md], [ADR-003-example-template-idempotency-strategy.md]
**Branch:** feature/src-engine-architecture

---

## Executive Summary

This sprint implements the source engine architecture redesign as defined in ADR-004. The goal is to evolve the existing `src/packages/` structure into a clean, transaction-safe engine with clear separation between pure planning logic and side-effect operations, while preserving all existing functionality.

**Current Status: 0% Complete** - Ready for implementation kickoff

---

## Sprint Goal

Transform the current `src/packages/` structure into a pure engine with deterministic planning, transaction safety, and receipt-driven idempotency while maintaining backward compatibility.

**Duration:** 8 weeks (4 phases as defined in ADR-004)

---

## Sprint Tasks

### Phase 1: Foundation (Weeks 1-2)

#### Directory Structure Setup

- [ ] Create new directory structure within `src/packages/`:
  - [ ] `cli/` - CLI parsing and coordination
  - [ ] `domain/` - Pure types and domain rules
  - [ ] `adapters/` - Infrastructure adapters
- [ ] Preserve existing `core/`, `managers/`, `operations/`, `utils/` during transition
- [ ] Add proper `__init__.py` files with clear exports

#### Domain Models Implementation

- [ ] **`domain/model.py`** - Core data structures:
  - [ ] `InstallPlan` dataclass with components sequence
  - [ ] `ComponentPlan` with actions and metadata
  - [ ] `FileAction` with kind/src/dst/mode/reason
  - [ ] `ActionKind` literal type (COPY/MERGE/TEMPLATE/SKIP)
  - [ ] `Reason` literal type (new/hash-diff/unchanged/drift)
- [ ] **`domain/errors.py`** - Typed exceptions:
  - [ ] `ConflictError` for component/path conflicts
  - [ ] `DepError` for dependency resolution failures
  - [ ] `DriftError` for state drift detection
  - [ ] Base `BootstrapError` with error codes
- [ ] **`domain/constants.py`** - System defaults:
  - [ ] `GUARDRAILS_DIR = ".ai"`
  - [ ] Hook names and standard paths
  - [ ] Default file modes and permissions

#### Adapter Foundation

- [ ] **`adapters/fs.py`** - Atomic filesystem operations:
  - [ ] `atomic_write()` with staging/verify/promote
  - [ ] `safe_mkdir()` with sentinel file creation
  - [ ] `staging()` context manager for transactions
  - [ ] `cleanup()` with sentinel validation (never rm without marker)
- [ ] **`adapters/hashing.py`** - Content hashing:
  - [ ] `sha256_file()` for source/target verification
  - [ ] `sha256_content()` for in-memory content
  - [ ] Hash comparison utilities for drift detection
- [ ] **`adapters/logging.py`** - Structured logging:
  - [ ] Quiet/verbose mode controls
  - [ ] Structured JSON output for CI integration
  - [ ] Performance timing for operations

### Phase 2: Core Logic Separation (Weeks 3-4)

#### Pure Planning Logic

- [ ] **`core/resolver.py`** - Dependency resolution (extract from `plugin_system.py`):
  - [ ] Load and validate `installation-manifest.yaml`
  - [ ] Load and validate `plugins/*/plugin-manifest.yaml`
  - [ ] Resolve component dependencies and conflicts
  - [ ] Compute deterministic installation order `(priority, plugin.id)`
  - [ ] Output `ResolvedSpec` ready for planning
- [ ] **`core/planner.py`** - Pure planning logic (extract from `component_manager.py`):
  - [ ] Build `InstallPlan` from `ResolvedSpec`
  - [ ] Determine file actions: COPY/MERGE/TEMPLATE/SKIP
  - [ ] Compute reasons via source hash vs target + receipts
  - [ ] No filesystem writes (pure function)
  - [ ] Deterministic and unit-testable

#### Receipt System

- [ ] **`adapters/receipts.py`** - Idempotency tracking (evolve from `state_manager.py`):
  - [ ] Read/write `.ai/guardrails/installed/<component>.json`
  - [ ] Track source digests, manifest digests, file hashes
  - [ ] `is_current(component)` validation for planner
  - [ ] Receipt format with timestamp, sizes, modes
- [ ] **`adapters/schema.py`** - Validation layer:
  - [ ] JSONSchema validators for plugin manifests
  - [ ] Core manifest validation
  - [ ] Target structure schema enforcement
  - [ ] Receipt format validation

#### YAML Operations Consolidation

- [ ] **`adapters/yaml_ops.py`** - Single content transformation funnel (merge from `config_manager.py` + `yaml_operations.py`):
  - [ ] YAML merge operations for configuration files
  - [ ] Template processing with variable substitution
  - [ ] JSON operations for envelope files
  - [ ] All content edits go through this single interface

### Phase 3: Transaction Safety & Integration (Weeks 5-6)

#### Safe Installation Engine

- [ ] **`core/installer.py`** - Side-effect executor (extract from `component_manager.py`):
  - [ ] Execute `InstallPlan` with per-component transactions
  - [ ] Implement staging/backup/promote pattern
  - [ ] Write receipts with full metadata
  - [ ] Rollback capability on any failure
  - [ ] Component-level error isolation

#### Enhanced Doctor System

- [ ] **`core/doctor.py`** - State validation and repair (evolve existing):
  - [ ] Validate receipts vs actual disk state
  - [ ] Detect drift and missing files
  - [ ] Manifest health checks
  - [ ] Target structure schema validation
  - [ ] Optional `--repair` mode for restoration

#### CLI Integration

- [ ] **`cli/main.py`** - Main entry point:
  - [ ] Parse command line arguments (`plan`, `install`, `doctor`, `list`)
  - [ ] Coordinate resolver → planner → installer flow
  - [ ] Handle `--dry-run`, `--force`, `--profile` options
  - [ ] Error mapping and user-friendly messages
- [ ] **`cli/args.py`** - Argument parsing:
  - [ ] Command-specific argument handling
  - [ ] Profile and component selection
  - [ ] Verbosity and output format controls

#### Orchestration Layer

- [ ] **`core/orchestrator.py`** - Rename and evolve `bootstrap.py`:
  - [ ] Wire together resolver → planner → installer
  - [ ] Handle CLI coordination and logging
  - [ ] Manage transaction boundaries
  - [ ] Error handling and rollback coordination

### Phase 4: Validation & Polish (Weeks 7-8)

#### Comprehensive Testing

- [ ] **Unit Tests** for all new components:
  - [ ] Domain models with various scenarios
  - [ ] Pure functions (resolver, planner)
  - [ ] Adapter interfaces with mocks
  - [ ] Error handling and edge cases
- [ ] **Integration Tests** for full workflows:
  - [ ] End-to-end installation scenarios
  - [ ] Transaction safety validation
  - [ ] Rollback and recovery testing
  - [ ] Doctor repair functionality
- [ ] **Performance Testing**:
  - [ ] Ensure no regression vs current system
  - [ ] Validate < 2 second planning response time
  - [ ] Memory usage validation for large manifests

#### CLI Enhancement

- [ ] **New CLI Commands**:
  - [ ] `ai-guardrails plan --profile full` - Show installation plan
  - [ ] `ai-guardrails install --dry-run` - Preview without changes
  - [ ] `ai-guardrails doctor --repair` - Fix detected issues
  - [ ] `ai-guardrails list --components` - Show available components
- [ ] **Enhanced Error Messages**:
  - [ ] Clear conflict descriptions with resolution suggestions
  - [ ] Dependency error explanations
  - [ ] Drift detection reports with repair options

#### Documentation & Migration

- [ ] **Update Entry Point**:
  - [ ] Modify `bin/ai-guardrails-bootstrap` to use `packages.cli.main`
  - [ ] Ensure backward compatibility for existing installations
  - [ ] Update all internal script references
- [ ] **Migration Documentation**:
  - [ ] Document breaking changes (if any)
  - [ ] Provide migration guide for custom plugins
  - [ ] Update developer documentation for new architecture

#### Optional Cleanup

- [ ] **Rename `packages/` to `infra/`** (if desired for clarity):
  - [ ] Update all imports and references
  - [ ] Update entry point script
  - [ ] Update documentation and examples

---

## Dependencies

### Upstream
- **ADR-001**: Modular Bootstrap Architecture - Provides foundation
- **ADR-003**: Example Template Idempotency Strategy - Informs receipt design
- Current `src/packages/` system - Working foundation to evolve

### Downstream
- **Future ADR**: Plugin API Standards - Will use new engine interfaces
- **User Installations**: Must maintain compatibility
- **CI/CD Integration**: Enhanced with new `--plan` and `--dry-run` capabilities

---

## Risks & Mitigation

### 🚨 Migration Complexity

**Risk:** Refactoring existing working system might introduce bugs
**Mitigation:**
- Preserve existing code during transition phases
- Comprehensive test coverage before any deletions
- Gradual migration with backward compatibility
- Feature flags for new vs old code paths

### 🚨 Performance Regression

**Risk:** Additional abstraction layers might slow down operations
**Mitigation:**
- Performance benchmarks before/after each phase
- Optimize hot paths in receipt checking and file operations
- Profile memory usage for large plugin manifests
- Validate < 2 second planning requirement

### 🚨 Transaction Safety Bugs

**Risk:** Staging/backup/promote logic might have edge cases
**Mitigation:**
- Extensive testing of atomic operations
- Test disk space exhaustion scenarios
- Validate rollback under various failure conditions
- Test concurrent access patterns

### 🚨 User Experience Disruption

**Risk:** CLI changes might confuse existing users
**Mitigation:**
- Maintain backward compatibility for existing commands
- Provide clear migration documentation
- Add helpful error messages for deprecated patterns
- Gradual rollout with user feedback integration

---

## Success Metrics

### Technical Metrics
- **Zero data loss** during component installation
- **100% transaction rollback** success rate on failures
- **Deterministic plans** across identical environments
- **Receipt accuracy** with hash validation
- **< 2 second** planning response time
- **Test coverage** ≥ 90% for new code

### User Experience Metrics
- **Clear `--plan` output** showing intended changes
- **Successful `--dry-run`** preview capability
- **Reliable `doctor --repair`** functionality
- **Helpful error messages** with resolution guidance
- **Backward compatibility** for existing installations

### Operational Metrics
- **Reduced support tickets** related to installation failures
- **Faster debugging** with structured logs and receipts
- **Easier plugin development** with clear interfaces
- **Maintainable codebase** with separation of concerns

---

## Definition of Done

### Phase 1 Complete
- [ ] All new directories and domain models implemented
- [ ] Basic adapters (fs, hashing, logging) functional
- [ ] Unit tests for domain models pass
- [ ] No regression in existing functionality

### Phase 2 Complete
- [ ] Pure planning logic separated from side effects
- [ ] Receipt system tracks all component metadata
- [ ] YAML operations consolidated to single interface
- [ ] Integration tests validate planning accuracy

### Phase 3 Complete
- [ ] Transaction safety implemented with staging/backup/promote
- [ ] CLI integration provides new commands (`plan`, `install`, `doctor`)
- [ ] Doctor system validates and repairs state
- [ ] End-to-end tests pass for all workflows

### Phase 4 Complete
- [ ] Comprehensive test suite with ≥ 90% coverage
- [ ] Performance meets < 2 second planning requirement
- [ ] Documentation updated for new architecture
- [ ] Migration guide available for users and developers
- [ ] All success metrics validated

---

## Configuration Schema

```python
# domain/model.py - Core data structures
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Sequence

ActionKind = Literal["COPY", "MERGE", "TEMPLATE", "SKIP"]
Reason = Literal["new", "hash-diff", "unchanged", "drift"]

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
    total_files: int
    estimated_size: int
```

---

## CLI Usage Examples

```bash
# Preview installation plan
ai-guardrails plan --profile full

# Dry run without changes
ai-guardrails install --profile full --dry-run

# Install with verbose logging
ai-guardrails install --profile standard --verbose

# Validate current installation
ai-guardrails doctor

# Repair detected issues
ai-guardrails doctor --repair

# List available components
ai-guardrails list --components
```

---

## Architecture Validation

### Pure/Effectful Separation
- **Pure**: `resolver.py`, `planner.py` - No side effects, deterministic
- **Effectful**: `installer.py`, `doctor.py` - Only components that modify filesystem
- **Single Funnel**: All content transformations through `yaml_ops.py`

### Transaction Safety
- **Per Component**: Each component uses staging/backup/promote
- **Rollback Capable**: All operations can be undone on failure
- **Receipt Driven**: Idempotency through `.ai/guardrails/installed/*.json`
- **Sentinel Protected**: Never delete without marker files

### Deterministic Behavior
- **Stable Plans**: Same inputs produce identical `InstallPlan`
- **Hash Verification**: Source and target content validation
- **Conflict Detection**: Clear error reporting for incompatible components
- **Dependency Resolution**: Consistent ordering via `(priority, plugin.id)`

---

**Status:** 🟡 Ready for Implementation
**Next Review:** Post-Phase 1 completion (Week 2)
**Owner:** Bootstrap System Team
**Epic:** Source Engine Architecture Modernization
