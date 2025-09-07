# 0007-Sprint-Plan-Plugin-Schema-Decoupling

**Date:** 2025-09-07
**Status:** � IN PROGRESS
**Priority:** High  
**Related:** [ADR-006-decouple-plugin-manifests-from-target-structure.md], [ADR-005-git-hook-execution-ordering-strategy.md]
**Branch:** feature/plugin-schema-decoupling

---

## Executive Summary

This sprint implements ADR-006: Decouple Plugin Manifests from Target Structure Schema. The goal is to eliminate tight coupling between plugin manifests and the global target structure schema by introducing plugin-specific structure schemas and a schema composition system. This will enable true plugin independence and eliminate the coordination nightmare for plugin developers.

**Current Status: 0% Complete** - Sprint started on feature/plugin-schema-decoupling branch, Phase 1 implementation beginning.

---

## Sprint Goal

Transform plugin architecture from tightly-coupled global schema dependency to autonomous plugin structure composition with clear separation of concerns.

**Duration:** 8 weeks (4 phases as defined in ADR-006 migration plan)

---

## Architecture Transformation

### Current State (Problematic)
```yaml
# Plugin Manifest contains target structure knowledge
configuration:
  target_structure_extensions:
    ".ai/guardrails/":
      files:
        "acl.yml":
          required: false
          description: "ACL policy configuration"
```

### Target State (Decoupled)
```yaml
# Plugin Structure Schema (independent)
# src/plugins/guardrails-acl-kit/plugin-structure.schema.yaml
provides_structure:
  ".ai/guardrails/":
    files:
      "acl.yml":
        required: false
        description: "Access control list policy configuration"
        schema_ref: "acl.schema.json"

# Plugin Manifest (installation-focused)
# plugin-manifest.yaml
components:
  acl-policy:
    description: "ACL policy configuration"
    source_patterns:
      - ".ai/guardrails/acl.yml"
```

---

## Phase 1: Foundation & Schema Extraction (Weeks 1-2)

### Core Schema Composition System

#### **Task 1.1: Schema Composer Implementation**
- [x] **File:** `src/packages/core/schema_composer.py`
  - [ ] `SchemaComposer` class with composition engine
  - [ ] `compose_target_schema()` method for merging schemas
  - [ ] `load_plugin_schema()` method for plugin schema loading
  - [ ] `merge_schemas()` method with conflict detection
  - [ ] `validate_composition()` method for final validation
  - [ ] Support for schema versioning and compatibility checks

**Acceptance Criteria:**
- [ ] Can compose target schema from base + multiple plugin schemas
- [ ] Detects and reports file path conflicts between plugins
- [ ] Validates dependency requirements across plugin schemas
- [ ] Supports dry-run mode for composition preview
- [ ] Handles plugin schema version compatibility

#### **Task 1.2: Plugin Structure Schema Format**
- [x] **File:** `src/schemas/plugin-structure.schema.json`
  - [ ] JSON Schema definition for plugin structure schemas
  - [ ] `provides_structure` section with file definitions
  - [ ] `requires_structure` section for dependencies
  - [ ] `conflicts_with` section for exclusion rules
  - [ ] Schema versioning and metadata fields
  - [ ] Integration with existing target structure format

**Acceptance Criteria:**
- [ ] Validates plugin structure schema files correctly
- [ ] Enforces required fields and data types
- [ ] Supports all current plugin structure patterns
- [ ] Enables IDE autocompletion for plugin developers
- [ ] Backward compatible with existing file patterns

#### **Task 1.3: Extract Existing Plugin Structures**
- [x] **Target Plugins:** All 6 existing plugins
  - [ ] **repo-safety-kit**: Extract target_structure_extensions to plugin-structure.schema.yaml
  - [ ] **commit-msg-kit**: Extract structure definitions
  - [ ] **demos-on-rails-kit**: Extract structure definitions  
  - [ ] **copilot-acl-kit**: Extract structure definitions
  - [ ] **doc-guardrails-kit**: Extract structure definitions
  - [ ] **root-hygiene-kit**: Extract structure definitions

**Acceptance Criteria:**
- [ ] Each plugin has independent plugin-structure.schema.yaml
- [ ] All existing file patterns preserved in new format
- [ ] Plugin structure schemas validate against JSON schema
- [ ] No loss of functionality or structure information
- [ ] Clear separation between structure and installation logic

### Validation & Testing Infrastructure

#### **Task 1.4: Plugin Structure Validation**
- [x] **File:** `scripts/validate_plugin_structures.py`
  - [ ] Independent validation of plugin structure schemas
  - [ ] Conflict detection between multiple plugins
  - [ ] Dependency requirement validation
  - [ ] Integration with existing plugin validation pipeline
  - [ ] CLI tool for plugin developers

**Acceptance Criteria:**
- [ ] Validates individual plugin structure schemas
- [ ] Detects conflicts when multiple plugins are enabled
- [ ] Reports clear error messages for schema violations
- [ ] Integrates with CI/CD pipeline for automated validation
- [ ] Provides actionable feedback for plugin developers

---

## Phase 2: Schema Composition Implementation (Weeks 3-4)

### Composition Engine Core

#### **Task 2.1: Schema Composition Logic**
- [x] **Enhancement:** `src/packages/core/schema_composer.py`
  - [ ] Implement deep merge algorithm for schema composition
  - [ ] Handle file path collision detection and resolution
  - [ ] Support for conditional structure composition
  - [ ] Plugin dependency graph resolution
  - [ ] Composition caching for performance optimization

**Acceptance Criteria:**
- [ ] Correctly merges base target schema with plugin schemas
- [ ] Handles complex dependency chains between plugins
- [ ] Optimizes composition performance for large plugin sets
- [ ] Provides detailed composition reports and logs
- [ ] Supports incremental composition updates

#### **Task 2.2: Conflict Detection System**
- [x] **File:** `src/packages/core/conflict_detector.py`
  - [ ] `detect_file_conflicts()` method for overlapping paths
  - [ ] `detect_dependency_conflicts()` method for circular deps
  - [ ] `detect_version_conflicts()` method for compatibility
  - [ ] Conflict resolution strategy suggestions
  - [ ] Integration with composition validation

**Acceptance Criteria:**
- [ ] Identifies all types of plugin conflicts accurately
- [ ] Provides clear conflict descriptions and locations
- [ ] Suggests resolution strategies for common conflicts
- [ ] Supports override mechanisms for advanced users
- [ ] Integrates with plugin installation workflow

#### **Task 2.3: Composed Schema Generation**
- [x] **Integration:** Update existing target structure validation
  - [ ] Modify `scripts/validate_plugin_manifests.py` to use composed schema
  - [ ] Update target structure validation to work with composed results
  - [ ] Ensure backward compatibility with existing validation
  - [ ] Add composition mode to validation pipeline
  - [ ] Create composed schema inspection tools

**Acceptance Criteria:**
- [ ] All existing validation continues to work correctly
- [ ] New composed schema validation catches more errors
- [ ] Plugin developers can preview composed schema locally
- [ ] CI pipeline validates composed schema automatically
- [ ] Clear migration path from old to new validation

### Plugin Loading & Management

#### **Task 2.4: Plugin Schema Discovery**
- [x] **File:** `src/packages/core/plugin_discovery.py`
  - [ ] `discover_plugin_schemas()` method for automatic discovery
  - [ ] Support for multiple plugin directories
  - [ ] Plugin schema caching and invalidation
  - [ ] Error handling for malformed schemas
  - [ ] Integration with plugin enablement system

**Acceptance Criteria:**
- [ ] Automatically discovers all plugin structure schemas
- [ ] Handles missing or malformed schema files gracefully
- [ ] Supports plugin directory configuration
- [ ] Caches discovery results for performance
- [ ] Provides clear error reporting for discovery failures

---

## Phase 3: Plugin Manifest Simplification (Weeks 5-6)

### Simplified Plugin Manifests

#### **Task 3.1: Remove Target Structure Extensions**
- [x] **Target:** All plugin manifest files
  - [ ] Remove `target_structure_extensions` sections from all plugin manifests
  - [ ] Ensure all file patterns migrated to plugin structure schemas
  - [ ] Update plugin manifest validation to exclude removed sections
  - [ ] Maintain all other plugin manifest functionality
  - [ ] Create migration validation to ensure no data loss

**Acceptance Criteria:**
- [ ] No plugin manifests contain target_structure_extensions
- [ ] All file patterns preserved in plugin structure schemas
- [ ] Plugin manifest validation updated and passing
- [ ] Backward compatibility maintained for installation logic
- [ ] Clear separation achieved between structure and installation

#### **Task 3.2: Enhanced Plugin Manifest Focus**
- [x] **Enhancement:** Plugin manifest functionality
  - [ ] Focus manifests on installation logic only
  - [ ] Enhance `post_install` section capabilities
  - [ ] Improve component-based installation patterns
  - [ ] Add plugin configuration management
  - [ ] Strengthen profile-based installation

**Acceptance Criteria:**
- [ ] Plugin manifests clearly focused on "how to install"
- [ ] Enhanced installation capabilities and flexibility
- [ ] Improved component and profile management
- [ ] Better configuration handling in manifests
- [ ] Cleaner separation of concerns achieved

#### **Task 3.3: Plugin Manifest Validation Update**
- [x] **File:** `scripts/validate_plugin_manifests.py`
  - [ ] Update validation to exclude target_structure_extensions
  - [ ] Add validation for new simplified manifest format
  - [ ] Ensure integration with plugin structure schema validation
  - [ ] Maintain backward compatibility during transition
  - [ ] Add migration assistance and error reporting

**Acceptance Criteria:**
- [ ] Validates simplified plugin manifests correctly
- [ ] Rejects manifests with legacy target_structure_extensions
- [ ] Provides clear migration guidance for invalid manifests
- [ ] Integrates seamlessly with structure schema validation
- [ ] Maintains existing validation quality and coverage

### Testing & Validation

#### **Task 3.4: End-to-End Composition Testing**
- [x] **File:** `tests/test_plugin_composition.py`
  - [ ] Test complete composition workflow
  - [ ] Test plugin enablement/disablement scenarios
  - [ ] Test conflict detection and resolution
  - [ ] Test performance with large plugin sets
  - [ ] Test backward compatibility with existing plugins

**Acceptance Criteria:**
- [ ] Comprehensive test coverage for composition system
- [ ] All plugin combination scenarios tested
- [ ] Performance benchmarks established and met
- [ ] Backward compatibility thoroughly validated
- [ ] Edge cases and error conditions properly handled

---

## Phase 4: Documentation & Tooling (Weeks 7-8)

### Developer Documentation

#### **Task 4.1: Plugin Development Guide Update**
- [x] **File:** `docs/guides/plugin-development-guide.md`
  - [ ] Complete rewrite for new decoupled architecture
  - [ ] Plugin structure schema documentation with examples
  - [ ] Best practices for plugin independence
  - [ ] Migration guide from old to new format
  - [ ] Troubleshooting guide for common issues

**Acceptance Criteria:**
- [ ] Comprehensive guide covering new plugin architecture
- [ ] Clear examples for all plugin structure schema patterns
- [ ] Step-by-step migration instructions for existing plugins
- [ ] Best practices clearly documented and explained
- [ ] Troubleshooting section addresses common problems

#### **Task 4.2: Schema Composition CLI Tools**
- [x] **File:** `scripts/plugin_schema_tools.py`
  - [ ] `compose-schema` command for preview and testing
  - [ ] `validate-plugin` command for individual plugin validation
  - [ ] `detect-conflicts` command for conflict analysis
  - [ ] `migrate-plugin` command for legacy plugin migration
  - [ ] Integration with existing CLI infrastructure

**Acceptance Criteria:**
- [ ] Complete CLI tool suite for plugin schema management
- [ ] Intuitive commands with comprehensive help documentation
- [ ] Integration with existing bootstrap CLI infrastructure
- [ ] Support for batch operations and automation
- [ ] Clear output formatting and error reporting

#### **Task 4.3: Migration Utilities**
- [x] **File:** `scripts/migrate_to_decoupled_schemas.py`
  - [ ] Automated migration from target_structure_extensions
  - [ ] Validation of migration completeness and correctness
  - [ ] Backup and rollback capabilities for safety
  - [ ] Batch migration support for multiple plugins
  - [ ] Integration with plugin validation pipeline

**Acceptance Criteria:**
- [ ] Automated migration tool for all existing plugins
- [ ] Complete migration validation and verification
- [ ] Safe migration with backup and rollback options
- [ ] Batch processing capability for efficiency
- [ ] Integration with development workflow

### Architecture Documentation

#### **Task 4.4: Architecture Decision Documentation**
- [x] **Files:** Architecture documentation updates
  - [ ] Update `docs/architecture/SYSTEM_ARCHITECTURE.md` with new plugin system
  - [ ] Create detailed plugin composition architecture documentation
  - [ ] Update plugin system analysis with new architecture
  - [ ] Document schema composition patterns and best practices
  - [ ] Create troubleshooting and debugging guides

**Acceptance Criteria:**
- [ ] Complete architectural documentation for new system
- [ ] Clear diagrams and examples of plugin composition
- [ ] Updated system architecture reflecting new plugin model
- [ ] Comprehensive troubleshooting and debugging information
- [ ] Best practices documentation for plugin developers

### System Upgrade & Maintenance

#### **Task 4.5: Upgrade System Implementation**
- [x] **Files:** System upgrade and maintenance capabilities
  - [ ] `src/packages/core/upgrade_manager.py` - Version management and upgrade logic
  - [ ] `src/packages/operations/upgrade.py` - Upgrade command implementation
  - [ ] Enhanced doctor command with cleanup capabilities
  - [ ] CLI integration for upgrade commands
  - [ ] Safe migration utilities for version transitions

**Upgrade Command Features:**
```bash
ai-guardrails upgrade                    # Upgrade to latest version
ai-guardrails upgrade --check           # Check for available upgrades  
ai-guardrails upgrade --dry-run         # Preview upgrade changes
ai-guardrails upgrade --force           # Force upgrade even if up-to-date
ai-guardrails upgrade --backup          # Create backup before upgrade
```

**Enhanced Doctor with Tidyup:**
```bash
ai-guardrails doctor --cleanup          # Remove orphaned files
ai-guardrails doctor --migrate          # Migrate old installations
ai-guardrails doctor --reset            # Reset to clean state
ai-guardrails doctor --repair-all       # Comprehensive repair mode
```

**Acceptance Criteria:**
- [ ] Complete upgrade system with version detection and management
- [ ] Safe upgrade process with automatic backup and rollback capabilities
- [ ] Enhanced doctor command with cleanup and migration features
- [ ] Integration with schema composition system for upgrade validation
- [ ] Comprehensive testing of upgrade scenarios and edge cases
- [ ] Clear upgrade path documentation and troubleshooting guides

---

## Success Metrics

### Plugin Independence Metrics
- [ ] **100% Decoupling**: No plugin manifests contain target_structure_extensions
- [ ] **Independent Validation**: Each plugin validates without global schema knowledge
- [ ] **Conflict Detection**: System identifies and reports all plugin conflicts
- [ ] **Composition Performance**: Schema composition completes in <1 second for 20 plugins

### Developer Experience Metrics  
- [ ] **Reduced Complexity**: Plugin developers only need to understand plugin structure schema format
- [ ] **Clear Separation**: Installation logic clearly separated from structure definition
- [ ] **Migration Success**: 100% of existing plugins migrated without data loss
- [ ] **Documentation Quality**: Complete plugin development guide with examples

### System Quality Metrics
- [ ] **Backward Compatibility**: All existing functionality preserved during migration
- [ ] **Validation Coverage**: Composed schema validation catches same or more errors
- [ ] **Performance**: No regression in plugin validation or installation performance
- [ ] **Maintainability**: Clear architecture with single responsibility principles

### System Management Metrics
- [ ] **Upgrade Safety**: 100% safe upgrades with automatic backup and rollback
- [ ] **Version Detection**: Accurate detection of current vs available versions
- [ ] **Cleanup Effectiveness**: Doctor command removes all orphaned files and repairs issues
- [ ] **Migration Success**: Seamless migration between system versions without data loss

---

## Risk Mitigation

### Technical Risks

**Risk: Complex Migration Path**
- **Mitigation**: Phased migration with extensive testing at each step
- **Validation**: Comprehensive test suite and rollback procedures

**Risk: Performance Degradation**
- **Mitigation**: Schema composition caching and optimization
- **Validation**: Performance benchmarking and monitoring

**Risk: Breaking Changes**
- **Mitigation**: Backward compatibility preservation and migration utilities
- **Validation**: Extensive compatibility testing and gradual rollout

### Process Risks

**Risk: Developer Adoption**
- **Mitigation**: Comprehensive documentation and migration tools
- **Validation**: Developer feedback and ease-of-use metrics

**Risk: Validation Gaps**
- **Mitigation**: Enhanced test coverage and validation scenarios
- **Validation**: Comparison testing with existing validation system

---

## Dependencies & Prerequisites

### Technical Dependencies
- [x] **ADR-005 Implementation**: Semantic hook ordering system (COMPLETE)
- [ ] **Plugin System**: Current plugin architecture must be stable
- [ ] **Target Schema**: Existing target structure schema stability
- [ ] **Validation Pipeline**: Current plugin validation system

### Process Dependencies
- [ ] **Stakeholder Approval**: ADR-006 approval and implementation authorization
- [ ] **Development Environment**: Testing infrastructure for schema composition
- [ ] **Documentation Platform**: Updated plugin development documentation
- [ ] **CI/CD Pipeline**: Integration with automated validation systems

---

## Deliverables

### Phase 1 Deliverables
- [ ] `src/packages/core/schema_composer.py` - Core composition system
- [ ] `src/schemas/plugin-structure.schema.json` - Plugin structure schema definition
- [ ] 6 Plugin structure schema files for existing plugins
- [ ] `scripts/validate_plugin_structures.py` - Structure validation tool

### Phase 2 Deliverables  
- [ ] Enhanced schema composition with conflict detection
- [ ] Updated target structure validation using composed schemas
- [ ] Plugin discovery and loading system
- [ ] Composition performance optimization

### Phase 3 Deliverables
- [ ] Simplified plugin manifests (target_structure_extensions removed)
- [ ] Updated plugin manifest validation
- [ ] End-to-end composition testing suite
- [ ] Migration validation and verification

### Phase 4 Deliverables
- [ ] Complete plugin development guide for new architecture
- [ ] CLI tools for schema composition and management
- [ ] Migration utilities for existing plugins
- [ ] Updated architecture documentation
- [ ] Upgrade system with version management and safe migration
- [ ] Enhanced doctor command with cleanup and repair capabilities

---

## Definition of Done

### Technical DoD
- [ ] All plugin manifests simplified and validated
- [ ] Schema composition system fully functional with conflict detection
- [ ] 100% backward compatibility maintained
- [ ] Comprehensive test coverage for new architecture
- [ ] Performance meets or exceeds current system

### Documentation DoD  
- [ ] Plugin development guide updated for new architecture
- [ ] Architecture documentation reflects new plugin system
- [ ] Migration guide provides clear step-by-step instructions
- [ ] API documentation complete for all new components
- [ ] Troubleshooting guide addresses common issues

### Quality DoD
- [ ] All existing plugins migrated and validated successfully
- [ ] New architecture passes all existing validation tests
- [ ] Plugin independence verified through isolated testing
- [ ] Developer tools and CLI utilities fully functional
- [ ] System ready for plugin developer adoption

### System Management DoD
- [ ] Upgrade system fully functional with version management
- [ ] Safe upgrade process with backup and rollback capabilities
- [ ] Enhanced doctor command with comprehensive cleanup features
- [ ] Migration utilities handle all legacy system transitions
- [ ] Comprehensive testing of upgrade and maintenance workflows

---

**Next Sprint:** TBD - Plugin ecosystem expansion or system optimization based on decoupled architecture adoption
