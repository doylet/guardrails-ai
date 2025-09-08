# 0004-Sprint-Plan-Src-Engine-Architecture

**Date:** 2025-09-06
**Status:** ✅ COMPLETE
**Priority:** High
**Related:** [ADR-004-src-engine-design.md], [ADR-001-modular-bootstrap-architecture.md], [ADR-003-example-template-idempotency-strategy.md]
**Branch:** feature/src-engine-architecture

---

## Executive Summary

This sprint implements the source engine architecture redesign as defined in ADR-004. The goal is to evolve the existing `src/packages/` structure into a clean, transaction-safe engine with clear separation between pure planning logic and side-effect operations, while preserving all existing functionality.

**Current Status: 95% Complete** - Phase 1 Foundation ✅ COMPLETE, Phase 2 Core Logic ✅ COMPLETE, Phase 3 Transaction Safety ✅ COMPLETE, Phase 4 Testing & Validation ✅ COMPLETE

## Phase 1 Achievements

- **🏗️ Foundation Architecture:** Complete domain models, adapters, and CLI framework
- **📊 Code Organization:** 5 new packages with clear separation of concerns
- **🛡️ Type Safety:** Comprehensive typed exceptions and domain models
- **⚡ Infrastructure:** Atomic filesystem operations, hashing, and structured logging
- **🎯 CLI Interface:** Full argument parsing for all planned commands
- **📚 Documentation:** Inline docs and clear module boundaries

## Phase 2 Achievements

- **🧠 Pure Planning Logic:** Resolver for dependency resolution and manifest loading
- **📝 Deterministic Planning:** Planner with stable file action generation from inputs
- **📋 Receipt System:** Enhanced tracking for idempotency and transaction safety
- **🔄 YAML Operations:** Consolidated adapter for content transformations
- **🎯 Separation of Concerns:** Clear boundaries between pure and effectful operations
- **✨ Clean Integration:** Updated package exports and module structure

## Phase 3 Achievements

- **🛡️ Safe Installation Engine:** Per-component transactions with staging/backup/promote pattern
- **🔧 Enhanced Doctor System:** Comprehensive health checks with drift detection and repair
- **🎯 CLI Integration:** Full pipeline coordination with proper error handling
- **🎼 Orchestration Layer:** Transaction boundary management and component coordination
- **🏗️ Architecture Enhancements:** Receipt tracking, status reporting, and environment validation
- **✅ Transaction Safety:** Atomic operations with automatic rollback on failure

---

## Sprint Goal

Transform the current `src/packages/` structure into a pure engine with deterministic planning, transaction safety, and receipt-driven idempotency while maintaining backward compatibility.

**Duration:** 8 weeks (4 phases as defined in ADR-004)

---

## Sprint Tasks

### Phase 1: Foundation (Weeks 1-2)

#### Directory Structure Setup

- [x] Create new directory structure within `src/packages/`:
  - [x] `cli/` - CLI parsing and coordination
  - [x] `domain/` - Pure types and domain rules
  - [x] `adapters/` - Infrastructure adapters
- [x] Preserve existing `core/`, `managers/`, `operations/`, `utils/` during transition
- [x] Add proper `__init__.py` files with clear exports

#### Domain Models Implementation

- [x] **`domain/model.py`** - Core data structures:
  - [x] `InstallPlan` dataclass with components sequence
  - [x] `ComponentPlan` with actions and metadata
  - [x] `FileAction` with kind/src/dst/mode/reason
  - [x] `ActionKind` literal type (COPY/MERGE/TEMPLATE/SKIP)
  - [x] `Reason` literal type (new/hash-diff/unchanged/drift)
- [x] **`domain/errors.py`** - Typed exceptions:
  - [x] `ConflictError` for component/path conflicts
  - [x] `DepError` for dependency resolution failures
  - [x] `DriftError` for state drift detection
  - [x] Base `BootstrapError` with error codes
- [x] **`domain/constants.py`** - System defaults:
  - [x] `GUARDRAILS_DIR = ".ai"`
  - [x] Hook names and standard paths
  - [x] Default file modes and permissions

#### Adapter Foundation

- [x] **`adapters/fs.py`** - Atomic filesystem operations:
  - [x] `atomic_write()` with staging/verify/promote
  - [x] `safe_mkdir()` with sentinel file creation
  - [x] `staging()` context manager for transactions
  - [x] `cleanup()` with sentinel validation (never rm without marker)
- [x] **`adapters/hashing.py`** - Content hashing:
  - [x] `sha256_file()` for source/target verification
  - [x] `sha256_content()` for in-memory content
  - [x] Hash comparison utilities for drift detection
- [x] **`adapters/logging.py`** - Structured logging:
  - [x] Quiet/verbose mode controls
  - [x] Structured JSON output for CI integration
  - [x] Performance timing for operations

#### CLI Framework

- [x] **`cli/args.py`** - Argument parsing:
  - [x] Command-specific argument handling (plan/install/doctor/list/uninstall)
  - [x] Profile and component selection
  - [x] Verbosity and output format controls
- [x] **`cli/main.py`** - Main entry point:
  - [x] Error handling and user-friendly messages
  - [x] Logging configuration
  - [x] Basic orchestration framework

### Phase 2: Core Logic Separation (Weeks 3-4) ✅ COMPLETE

#### Pure Planning Logic

- [x] **`core/resolver.py`** - Dependency resolution (extract from `plugin_system.py`):
  - [x] Load and validate `installation-manifest.yaml`
  - [x] Load and validate `plugins/*/plugin-manifest.yaml`
  - [x] Resolve component dependencies and conflicts
  - [x] Compute deterministic installation order `(priority, plugin.id)`
  - [x] Output `ResolvedSpec` ready for planning
- [x] **`core/planner.py`** - Pure planning logic (extract from `component_manager.py`):
  - [x] Build `InstallPlan` from `ResolvedSpec`
  - [x] Determine file actions: COPY/MERGE/TEMPLATE/SKIP
  - [x] Compute reasons via source hash vs target + receipts
  - [x] No filesystem writes (pure function)
  - [x] Deterministic and unit-testable

#### Receipt System

- [x] **`adapters/receipts.py`** - Idempotency tracking (evolve from `state_manager.py`):
  - [x] Read/write `.ai/guardrails/installed/<component>.json`
  - [x] Track source digests, manifest digests, file hashes
  - [x] `is_current(component)` validation for planner
  - [x] Receipt format with timestamp, sizes, modes
- [x] **`adapters/yaml_ops.py`** - YAML operations consolidation:
  - [x] Content merging with configurable strategies
  - [x] Template processing with variable substitution
  - [x] Content validation and type detection
  - [x] Unified interface for content transformations
  - [x] Receipt format validation

#### YAML Operations Consolidation

- [x] **`adapters/yaml_ops.py`** - Single content transformation funnel (merge from `config_manager.py` + `yaml_operations.py`):
  - [x] YAML merge operations for configuration files
  - [x] Template processing with variable substitution
  - [x] JSON operations for envelope files
  - [x] All content edits go through this single interface

### Phase 3: Transaction Safety & Integration (Weeks 5-6) ✅ COMPLETE

#### Safe Installation Engine

- [x] **`core/installer.py`** - Side-effect executor (extract from `component_manager.py`):
  - [x] Execute `InstallPlan` with per-component transactions
  - [x] Implement staging/backup/promote pattern
  - [x] Write receipts with full metadata
  - [x] Rollback capability on any failure
  - [x] Component-level error isolation

#### Enhanced Doctor System

- [x] **`core/doctor.py`** - State validation and repair (evolve existing):
  - [x] Validate receipts vs actual disk state
  - [x] Detect drift and missing files
  - [x] Manifest health checks
  - [x] Target structure schema validation
  - [x] Optional `--repair` mode for restoration

#### CLI Integration

- [x] **`cli/main.py`** - Main entry point:
  - [x] Parse command line arguments (`plan`, `install`, `doctor`, `list`)
  - [x] Coordinate resolver → planner → installer flow
  - [x] Handle `--dry-run`, `--force`, `--profile` options
  - [x] Error mapping and user-friendly messages
- [x] **`cli/args.py`** - Argument parsing:
  - [x] Command-specific argument handling
  - [x] Profile and component selection
  - [x] Verbosity and output format controls

#### Orchestration Layer

- [x] **`core/orchestrator.py`** - Rename and evolve `bootstrap.py`:
  - [x] Wire together resolver → planner → installer
  - [x] Handle CLI coordination and logging
  - [x] Manage transaction boundaries
  - [x] Error handling and rollback coordination

### Phase 4: Validation & Polish (Weeks 7-8)

#### Comprehensive Testing

- [x] **Unit Tests** for all new components:
  - [x] Domain models with various scenarios
  - [x] Pure functions (resolver, planner)
  - [x] Adapter interfaces with mocks
  - [x] Error handling and edge cases
- [x] **Integration Tests** for full workflows:
  - [x] End-to-end installation scenarios
  - [x] Transaction safety validation
  - [x] Rollback and recovery testing
  - [x] Doctor repair functionality
- [x] **Performance Testing**:
  - [x] Ensure no regression vs current system
  - [x] Validate < 2 second planning response time
  - [x] Memory usage validation for large manifests

#### CLI Enhancement

- [x] **New CLI Commands**:
  - [x] `ai-guardrails plan --profile full` - Show installation plan
  - [x] `ai-guardrails install --dry-run` - Preview without changes
  - [x] `ai-guardrails doctor --repair` - Fix detected issues
  - [x] `ai-guardrails list --components` - Show available components
- [x] **Enhanced Error Messages**:
  - [x] Clear conflict descriptions with resolution suggestions
  - [x] Dependency error explanations
  - [x] Drift detection reports with repair options

#### Documentation & Migration ✅ COMPLETE

- [x] **Update Entry Point**:
  - [x] Modify `bin/ai-guardrails-bootstrap` to use `packages.cli.main`
  - [x] Ensure backward compatibility for existing installations
  - [x] Update all internal script references
- [x] **Migration Documentation**:
  - [x] Document breaking changes (if any)
  - [x] Provide migration guide for custom plugins (`docs/guides/sprint-004-migration-guide.md`)
  - [x] Update developer documentation for new architecture (`docs/guides/developer-documentation.md`)

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

### Phase 1 Complete ✅
- [x] All new directories and domain models implemented
- [x] Basic adapters (fs, hashing, logging) functional
- [x] CLI framework with comprehensive argument parsing
- [x] No regression in existing functionality

### Phase 2 Complete ✅
- [x] Pure planning logic separated from side effects
- [x] Receipt system tracks all component metadata
- [x] YAML operations consolidated to single interface
- [x] Integration tests validate planning accuracy

### Phase 3 Complete ✅
- [x] Transaction safety implemented with staging/backup/promote
- [x] CLI integration provides new commands (`plan`, `install`, `doctor`)
- [x] Doctor system validates and repairs state
- [x] End-to-end tests pass for all workflows

### Phase 4 Complete ✅
- [x] Comprehensive test suite with ≥ 90% coverage
- [x] Performance meets < 2 second planning requirement
- [x] Documentation updated for new architecture (`docs/guides/developer-documentation.md`)
- [x] Migration guide available for users and developers (`docs/guides/sprint-004-migration-guide.md`)
- [x] All success metrics validated

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
