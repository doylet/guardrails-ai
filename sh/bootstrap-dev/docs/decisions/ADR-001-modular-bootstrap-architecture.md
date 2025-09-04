# ADR-001: Modular Bootstrap Architecture for AI Guardrails

- Date: 2025-09-03
- Status: Proposed

## Context

The current `ai_guardrails_bootstrap_unified.sh` presents significant maintenance and distribution challenges:

### Current Problems

1. **Monolithic Design**: All template files are embedded as heredocs within a 1000+ line bash script, making maintenance difficult
2. **No Version Management**: Users cannot track what version they have installed or update selectively
3. **Distribution Complexity**: Every template update requires redistributing the entire script
4. **Testing Difficulties**: Cannot test individual template components in isolation
5. **Poor Developer Experience**: Editing templates requires modifying bash heredocs instead of actual files
6. **No Rollback Capability**: No way to revert to previous template versions
7. **Limited Customization**: Organizations cannot easily maintain custom template variants

### Constraints

- Must maintain backward compatibility during transition
- Network connectivity may not always be available (offline support needed)
- Different organizations may need custom template repositories
- Users expect simple, single-command installation experience

## Decision

We will transition from the monolithic embedded approach to a **modular template repository architecture** with the following components:

### 1. Template Repository Structure

Create a separate repository containing:

```
ai-guardrails-templates/
├── version.txt                           # Semantic version (e.g., "1.2.0")
├── CHANGELOG.md                          # Version history and breaking changes
├── templates/                            # All template files as actual files
│   ├── .ai/
│   │   ├── guardrails.yaml
│   │   └── envelope.json
│   ├── ai/
│   │   ├── schemas/copilot_envelope.schema.json
│   │   ├── scripts/
│   │   └── capabilities.md
│   ├── .github/
│   │   ├── workflows/
│   │   ├── chatmodes/
│   │   └── prompts/
│   └── docs/decisions/ADR-template.md
└── scripts/
    ├── bootstrap.sh                      # Lean bootstrap script
    └── migrate-from-unified.sh           # Migration helper
```

### 2. Modular Bootstrap Script

Replace the monolithic script with `ai_guardrails_bootstrap_modular.sh` that:

- **Fetches templates** from repository instead of embedding them
- **Supports versioning** with semantic version tags
- **Provides offline fallbacks** with minimal embedded templates for core files
- **Enables custom repositories** for organizations
- **Tracks installed versions** and provides update capabilities

### 3. Key Features

- **Version Management**: `--update`, `--list-versions`, pin to specific versions
- **Selective Updates**: Update only specific components when needed
- **Custom Repositories**: `--template-repo` for organization-specific templates
- **Offline Support**: `--offline` mode with embedded fallbacks
- **Migration Tools**: Helper scripts to transition from unified approach

### Why This Over Alternatives

**Alternative 1: Keep Current Approach**

- ❌ Maintenance burden continues to grow
- ❌ No version management
- ❌ Poor developer experience

**Alternative 2: Package Manager (npm/pip)**

- ❌ Adds dependency on language ecosystem
- ❌ More complex for simple shell script distribution
- ❌ May not be available in all environments

**Alternative 3: Git Submodules**

- ❌ Requires Git knowledge from users
- ❌ More complex workflow
- ❌ Doesn't solve version management cleanly

**Chosen: Template Repository + Modular Bootstrap**

- ✅ Maintains simple user experience
- ✅ Enables proper version management
- ✅ Allows independent template development
- ✅ Supports organizational customization
- ✅ Provides clean migration path

## Consequences

### Positive Outcomes

1. **Maintainer Benefits**:
   - Edit templates as actual files with proper syntax highlighting
   - Version control individual template changes
   - Test templates independently
   - Deploy updates incrementally

2. **User Benefits**:
   - Clear version tracking with semantic versioning
   - Update existing installations: `bootstrap --update`
   - Pin to specific versions for stability
   - Custom template repositories for organizations

3. **Distribution Benefits**:
   - Smaller bootstrap script (easier to audit)
   - Gradual rollout of breaking changes via version tags
   - Better compatibility and dependency tracking

### Risks and Mitigations

**Risk: Network Dependency**

- *Mitigation*: Offline mode with embedded fallbacks for core files
- *Mitigation*: Error handling with graceful degradation

**Risk: Repository Availability**

- *Mitigation*: Multiple repository mirrors (GitHub, GitLab, self-hosted)
- *Mitigation*: Cached templates in user's local system

**Risk: Migration Complexity**

- *Mitigation*: Provide automated migration script
- *Mitigation*: Maintain unified script during transition period
- *Mitigation*: Clear migration documentation and examples

**Risk: Breaking Changes**

- *Mitigation*: Semantic versioning with clear breaking change indicators
- *Mitigation*: Changelog with migration guides
- *Mitigation*: Deprecation warnings before removing features

### Migration Plan

**Phase 1: Foundation (Week 1-2)**

- Create template repository structure
- Develop modular bootstrap script
- Add offline fallbacks for critical templates

**Phase 2: Testing (Week 3)**

- Internal testing with existing projects
- Validate migration from unified approach
- Refine error handling and user experience

**Phase 3: Soft Launch (Week 4)**

- Release modular script alongside unified version
- Add deprecation notice to unified script
- Provide migration documentation

**Phase 4: Full Migration (Month 2)**

- Encourage users to migrate via documentation
- Provide migration helper tools
- Collect feedback and iterate

**Phase 5: Sunset (Month 3+)**

- Mark unified script as deprecated
- Eventually remove unified script after sufficient adoption

### Success Metrics

1. **Maintenance Efficiency**:
   - Time to update templates: < 5 minutes (vs current ~30 minutes)
   - Template testing coverage: > 90%
   - Deployment frequency: Weekly vs monthly

2. **User Experience**:
   - Installation success rate: > 95%
   - Update adoption rate: > 60% within 30 days of release
   - Support issues: < 50% of current volume

3. **Adoption**:
   - Migration from unified script: > 80% within 3 months
   - Custom repository usage: > 5 organizations
   - Version pinning usage: > 30% of installations

### Rollback Plan

If critical issues arise:

1. **Immediate**: Revert to unified script as primary recommendation
2. **Short-term**: Fix issues in modular approach while maintaining unified script
3. **Long-term**: Re-evaluate architecture if fundamental problems discovered

The unified script will be maintained during the transition period to ensure users always have a working fallback option.
