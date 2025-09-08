# 0006-Sprint-Plan-Schema-Path-Migration-Completion

**Date:** 2025-01-07
**Status:** ✅ COMPLETED
**Priority:** High
**Related:** [manifest-paths-consolidation.patch], [ADR-002-project-structure-reorganization.md]
**Branch:** feature/complete-schema-path-migration

---

## Executive Summary

This sprint completes the path migration from `ai/` to `.ai/` directories, specifically focusing on schema file locations and bootstrap script updates. The scripts migration (`ai/scripts` → `.ai/scripts`) has been completed, but schema references and bootstrap installation logic still point to the old paths.

**Current Status: 100% Complete** - All path migration completed, legacy ai/ directory safely removed

---

## Sprint Goal

Complete the migration from `ai/` to `.ai/` directory structure to fully consolidate AI-related files under dotfile conventions, enabling safe removal of the legacy `ai/` folder.

**Duration:** 3 days

---

## Sprint Tasks

### Phase 1: Schema Path Migration (Day 1) ✅ COMPLETED

#### Update Installation Manifest
- [x] **`src/installation-manifest.yaml`** - Line 18:
  - Change `"ai/schemas/*.json"` → `".ai/schemas/*.json"`

#### Update Target Structure Schema  
- [x] **`src/target-structure.schema.yaml`** - Lines 21, 110:
  - Change `"ai/schemas/copilot_envelope.schema.json"` → `".ai/schemas/copilot_envelope.schema.json"`
  - Update validation rules to reference `.ai/schemas/`

### Phase 2: Bootstrap Script Updates (Day 2) ✅ COMPLETED

#### Update Bootstrap Installation Logic
- [x] **`src/ai_guardrails_bootstrap_modular.sh`** - Multiple lines:
  - Line 170: `"ai/schemas/copilot_envelope.schema.json"` → `".ai/schemas/copilot_envelope.schema.json"`
  - Line 281: `"ai/schemas/copilot_envelope.schema.json"` → `".ai/schemas/copilot_envelope.schema.json"`
  - Line 328: Update template write paths from `ai/schemas/` → `.ai/schemas/`
  - Line 331-334: Update script installation paths from `ai/scripts/` → `.ai/scripts/`
  - Line 337: `chmod +x ai/scripts/*.py ai/scripts/*.sh` → `chmod +x .ai/scripts/*.py .ai/scripts/.sh`

### Phase 3: Template Structure Migration (Day 2) ✅ COMPLETED

#### Move Schema Files in Templates
- [x] **Create `.ai/schemas/` directory** in `src/ai-guardrails-templates/`
- [x] **Move schema files** from `ai/schemas/` → `.ai/schemas/`
- [x] **Create `.ai/scripts/` directory** in templates (if not exists)
- [x] **Move script files** from `ai/scripts/` → `.ai/scripts/`

### Phase 4: Validation & Cleanup (Day 3) ✅ COMPLETED

#### Testing & Verification
- [x] **Test bootstrap installation** with new paths
- [x] **Verify all manifests** reference correct paths
- [x] **Run existing tests** to ensure no regressions
- [x] **Check GitHub workflows** use correct script paths

#### Final Cleanup
- [x] **Remove legacy `ai/` directory** from templates
- [x] **Update any remaining documentation** referencing old paths
- [x] **Verify grep search** shows no remaining `ai/scripts` or `ai/schemas` references

---

## Success Criteria

1. ✅ All installation manifests reference `.ai/` paths
2. ✅ Bootstrap scripts install to `.ai/` directories
3. ✅ Template structure uses `.ai/` convention
4. ✅ All tests pass with new path structure
5. ✅ Legacy `ai/` directory can be safely removed
6. ✅ No remaining references to old `ai/scripts` or `ai/schemas` paths

---

## Risk Assessment

**Low Risk** - This is a straightforward path migration with clear, mechanical changes.

### Potential Issues:
- **Path case sensitivity** on different filesystems
- **Existing installations** may have old structure
- **CI/CD pipelines** may need cache invalidation

### Mitigation:
- Test on multiple platforms during validation
- Document migration steps for existing users
- Update all references atomically

---

## Dependencies

- None - all required changes are internal to this repository

---

## Deliverables

1. **Updated installation manifests** with `.ai/` path references
2. **Updated bootstrap scripts** installing to correct locations
3. **Migrated template structure** using `.ai/` convention
4. **Validated test suite** ensuring no regressions
5. **Clean repository** with legacy `ai/` directory removed

---

## Definition of Done

- [x] All manifest files reference `.ai/` paths consistently
- [x] Bootstrap installation creates files in `.ai/` directories
- [x] Template structure follows `.ai/` convention
- [x] All tests pass successfully
- [x] `grep -r "ai/schemas\|ai/scripts"` returns no matches (except patch files)
- [x] Legacy `ai/` directory removed from templates
- [x] Documentation updated if necessary

---

## Notes

This sprint resolves the incomplete migration identified during the application of `manifest-paths-consolidation.patch`. The scripts portion was successfully migrated, but schema references and installation logic still used the old paths, preventing safe removal of the legacy `ai/` directory.
