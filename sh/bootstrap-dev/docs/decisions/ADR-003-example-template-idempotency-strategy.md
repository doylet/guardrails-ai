# ADR-003: Example and Template Idempotency Strategy

**Date:** 2025-09-06
**Status:** Proposed
**Deciders:** Development Team, Bootstrap System Architects
**Technical Story:** Establish canonical idempotent handling of example files and templates

---

## Context

The AI Guardrails Bootstrap system handles two distinct types of template files:

1. **Example files** (`.example` suffix): Configuration files that should be merged into active configurations
2. **Template files** (`.template` suffix): Document scaffolds that should be copied as reference

Current implementation in `component_manager.py` has basic logic for handling these files, but lacks comprehensive idempotency guarantees and enforcement mechanisms. Analysis of the existing system reveals:

### Current State
- ✅ Basic `.example.yaml` → `.yaml` transformation working
- ✅ YAML merging preserves some user customizations
- ✅ File identity checks prevent unnecessary operations
- 🟡 Inconsistent naming patterns across components
- ❌ No validation of naming conventions
- ❌ Limited idempotency testing
- ❌ No backup/rollback mechanisms

### Problems Identified
```python
# Current gaps in component_manager.py:
def _should_merge_file(self, src_path: Path, target_path: Path) -> bool:
    # Works but lacks comprehensive validation
    if src_path.name.endswith('.example.yaml') or src_path.name.endswith('.yaml.example'):
        return True
    # Missing: naming convention enforcement, edge case handling
```

### Business Impact
- User configurations occasionally overwritten during updates
- Inconsistent behavior across different file types
- No reliable rollback when merges fail
- Plugin developers uncertain about naming conventions

---

## Decision

We adopt a **comprehensive idempotency strategy** with strict enforcement mechanisms:

### 1. Canonical Naming Convention (Enforced)

| Pattern | Status | Usage |
|---------|--------|-------|
| `{filename}.{extension}.example` | ✅ **Required** | Configuration examples |
| `{filename}.{extension}.template` | ✅ **Required** | Document scaffolds |
| `example.{filename}.{extension}` | ❌ **Prohibited** | Creates confusion |
| `{filename}-example.{extension}` | ❌ **Prohibited** | Non-standard |

### 2. Idempotent Transformation Rules

```python
# New enforcement logic:
def get_transformation_rule(src_path: Path) -> TransformationRule:
    """Determine how to handle each file type"""

    if src_path.name.endswith('.example.yaml'):
        return TransformationRule(
            target_name=src_path.name.replace('.example.yaml', '.yaml'),
            operation='merge',
            preserve_user_changes=True
        )

    elif src_path.name.endswith('.template.md'):
        return TransformationRule(
            target_name=src_path.name,  # Keep .template suffix
            operation='copy',
            preserve_user_changes=False
        )

    else:
        return TransformationRule(
            target_name=src_path.name,
            operation='copy_if_not_exists',
            preserve_user_changes=True
        )
```

### 3. YAML Merging Strategy

**Preservation Guarantees:**
- User-added exclude patterns in pre-commit hooks → **Always preserved**
- Custom configuration sections → **Always preserved**
- User-added repos/hooks → **Always preserved**
- Comments in YAML → **Best effort preservation**

**Merge Behavior:**
```yaml
# Example: .pre-commit-config.yaml merging
# User file (existing):
repos:
  - repo: local
    hooks:
      - id: custom-check
        exclude: 'user-pattern.*'  # ← PRESERVED

# Template file (.example):
repos:
  - repo: local
    hooks:
      - id: custom-check
        exclude: ''  # ← IGNORED (user wins)
      - id: new-check
        entry: ./new-script.sh

# Result (merged):
repos:
  - repo: local
    hooks:
      - id: custom-check
        exclude: 'user-pattern.*'  # ← USER PRESERVED
      - id: new-check              # ← TEMPLATE ADDED
        entry: ./new-script.sh
```

### 4. Enforcement Mechanisms

**Pre-Installation Validation:**
```python
def validate_component_files(component: str, files: List[Path]) -> ValidationResult:
    """Validate all files conform to naming conventions"""
    errors = []
    for file_path in files:
        if not follows_naming_convention(file_path):
            errors.append(f"Invalid naming: {file_path}")

    if errors:
        raise ValidationError(f"Component {component} has naming violations: {errors}")
```

**Operation Logging:**
```
Installing component: precommit (3 files)
  merging: .pre-commit-config.yaml.example → .pre-commit-config.yaml
  skipping: .gitignore (identical)
  copying: docs/ADR-template.md.template → docs/ADR-template.md.template
```

**Idempotency Verification:**
```python
def verify_idempotency(component: str) -> bool:
    """Verify repeated operations produce identical results"""
    # Take snapshot, run operation twice, compare results
    return run_twice_and_compare(component)
```

### 5. Error Recovery

**Backup Strategy:**
- Create `.{filename}.backup-{timestamp}` before any merge operation
- Keep last 3 backups automatically
- Provide `--rollback` command to undo last operation

**Failure Handling:**
```python
def safe_merge_file(src: Path, target: Path) -> MergeResult:
    """Merge with automatic backup and rollback on failure"""
    backup_path = create_backup(target)
    try:
        return merge_yaml_files(src, target)
    except Exception as e:
        restore_from_backup(backup_path, target)
        raise MergeError(f"Merge failed, restored backup: {e}")
```

---

## Consequences

### Positive

1. **Reliability:** 100% idempotency guarantee for all operations
2. **User Trust:** Configurations never lost during updates
3. **Developer Experience:** Clear naming conventions reduce confusion
4. **Maintainability:** Comprehensive test coverage prevents regressions
5. **Debugging:** Detailed logging makes troubleshooting straightforward

### Negative/Risks

1. **Implementation Effort:** Requires updates to component_manager.py and comprehensive tests
2. **Performance Impact:** Binary file comparison and backup creation add ~100ms per operation
3. **Disk Usage:** Backup files consume additional space (~3x for YAML files)
4. **Breaking Changes:** Some existing plugins may need naming convention updates

### Migration Requirements

**Immediate (Week 1):**
- Update component_manager.py with validation logic
- Add comprehensive test suite for idempotency
- Document naming conventions

**Short-term (Week 2-3):**
- Audit all existing plugins for naming compliance
- Add backup/rollback mechanisms
- Implement dry-run mode

**Long-term (Month 2):**
- Add concurrent operation detection
- Performance optimization for large files
- Real-world usage monitoring

### Success Metrics

**Technical:**
- Zero file corruption incidents in production
- 100% pass rate on idempotency test suite
- Installation time remains < 5 seconds per component

**User Experience:**
- Zero user configuration loss incidents
- < 1% installation failures due to file conflicts
- Positive feedback on naming convention clarity

### Monitoring

```python
# Key metrics to track:
metrics = {
    'operations_per_day': 'gauge',
    'merge_failures': 'counter',
    'backup_restorations': 'counter',
    'naming_violations': 'counter',
    'idempotency_test_failures': 'counter'
}
```

**Alert Thresholds:**
- Any merge failure → Immediate investigation
- >5% naming violations → Review plugin quality
- Backup restoration used → Validate merge logic

---

## Implementation Plan

### Phase 1: Core Enforcement (Week 1)
- [ ] Update `ComponentManager._should_merge_file()` with validation
- [ ] Add `validate_naming_conventions()` function
- [ ] Create comprehensive test suite in `test_example_template_idempotency.py`
- [ ] Document strategy in architecture docs

### Phase 2: Safety Mechanisms (Week 2)
- [ ] Implement backup creation before merges
- [ ] Add rollback command to CLI
- [ ] Create dry-run mode for preview
- [ ] Add operation logging with detail levels

### Phase 3: Production Hardening (Week 3)
- [ ] Add concurrent operation detection
- [ ] Implement performance monitoring
- [ ] Create plugin naming validation tool
- [ ] Add automated idempotency regression tests

### Acceptance Criteria

**Must Have:**
- ✅ All existing functionality preserved
- ✅ Zero user configuration loss in testing
- ✅ 100% idempotency test pass rate
- ✅ Clear error messages for naming violations

**Should Have:**
- ✅ Backup/rollback functionality working
- ✅ Dry-run mode implemented
- ✅ Performance impact < 100ms per operation
- ✅ Documentation updated with examples

**Could Have:**
- ✅ Concurrent operation detection
- ✅ Advanced YAML comment preservation
- ✅ Plugin naming validation tool
- ✅ Real-time monitoring dashboard

---

## Related Decisions

- **ADR-001:** Modular Bootstrap Architecture - Established plugin system that this strategy builds upon
- **ADR-002:** Project Structure Reorganization - Impacts where template files are stored
- **Future ADR:** Plugin Quality Standards - Will reference these naming conventions

---

## Appendix

### Example Transformations

```bash
# Valid example files:
.pre-commit-config.yaml.example  → .pre-commit-config.yaml    [merge]
.env.example                     → .env                       [copy]
guardrails.docs.example.yaml     → guardrails.yaml            [merge]

# Valid template files:
ADR-template.md.template         → ADR-template.md.template   [copy as-is]
0000-COE-template.md.template    → 0000-COE-template.md.template [copy as-is]

# Invalid patterns (will be rejected):
example.config.yaml              → ERROR: Invalid naming
config-example.yaml              → ERROR: Invalid naming
template-ADR.md                  → ERROR: Invalid naming
```

### Test Coverage Matrix

| Scenario | Example Files | Template Files | Regular Files |
|----------|---------------|----------------|---------------|
| First install | Merge → target | Copy as-is | Copy if not exists |
| Identical content | Skip (no-op) | Skip (no-op) | Skip (no-op) |
| User customized | Preserve + merge new | N/A | Preserve existing |
| Malformed YAML | Backup + error | N/A | Copy + warn |
| Permission denied | Graceful failure | Graceful failure | Graceful failure |

---

**Status:** 🟡 Awaiting Implementation
**Next Review:** Post-implementation validation
**Owner:** Bootstrap System Team
