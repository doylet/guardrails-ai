# ADR-002: Project Structure Clarification and Phased Reorganization

**Date:** 2025-09-03
**Status:** Proposed
**Deciders:** Development Team
**Technical Story:** Project organization confusion between development workspace and template distribution

---

## Context

Following the successful completion of Sprint 0001 (Modular Bootstrap Architecture), users have expressed confusion about the project organization. The current structure mixes development workspace files with template distribution artifacts in a single directory, creating ambiguity about:

- What files are for developers vs end users
- Which components are source vs distribution artifacts
- How to contribute to vs consume the project
- The relationship between development and template repositories

### Current Structure Issues

```
/scripts/sh/                           # Mixed purpose directory
├── ai_guardrails_bootstrap_modular.sh # Development artifact
├── ai_guardrails_bootstrap_unified.sh # Legacy artifact
├── ai-guardrails-templates/           # Distribution embedded in dev workspace
├── docs/                              # Development documentation
├── tests/                             # Development tests
├── ai/                                # Development configuration
└── README.md                          # Unclear audience (dev vs user)
```

**Problems:**

- Template repository (`ai-guardrails-templates/`) embedded within development workspace
- No clear separation between "building the system" vs "using the system"
- Documentation serves dual purpose without clear audience distinction
- New contributors and end users face the same confusing entry point

---

## Decision

We will implement a **phased approach** to clarify project structure while preserving the working system from Sprint 0001:

### Phase 1: Immediate Clarity (Week 1)

- Add comprehensive structure documentation
- Clarify README with distinct developer and user sections
- Document current dual-purpose architecture
- Create clear navigation paths for different audiences

### Phase 2: Reorganize Within Repository (Sprint 0002)

- Restructure files into logical groupings
- Maintain single repository but with clear separation
- Establish build processes for template distribution
- Create distinct entry points for development vs usage

### Phase 3: Split Repositories (Future Sprint)

- Extract template repository to standalone distribution
- Maintain development repository for bootstrap tooling
- Implement cross-repository synchronization
- Establish production-ready distribution model

---

## Considered Alternatives

### Alternative 1: Immediate Repository Split

**Pros:** Clean separation, professional structure, clear boundaries
**Cons:** Disrupts working system, complex migration, potential sync issues, delays current momentum

**Rejected because:** Would break Sprint 0001 deliverables and require extensive rework of documentation, testing, and processes.

### Alternative 2: Accept Current Structure Permanently

**Pros:** No changes needed, preserves all current work, simple maintenance
**Cons:** Continued confusion, poor user experience, unprofessional presentation, scaling difficulties

**Rejected because:** User confusion is a real problem that will worsen as the project grows and gains adoption.

### Alternative 3: Big Bang Reorganization

**Pros:** Immediate clarity, professional structure
**Cons:** High risk of breaking changes, extensive rework required, long implementation time

**Rejected because:** Too risky given the working state of Sprint 0001 deliverables.

---

## Rationale

The phased approach balances immediate clarity needs with preservation of working systems:

1. **Risk Mitigation:** Gradual changes reduce chance of breaking working components
2. **Value Preservation:** Sprint 0001 achievements remain intact and usable
3. **User Experience:** Immediate documentation improvements address confusion
4. **Evolution Path:** Clear roadmap to professional structure when ready
5. **Learning Opportunity:** Each phase provides feedback for the next

### Technical Rationale

- **Phase 1** requires only documentation changes (zero technical risk)
- **Phase 2** reorganizes files but maintains functional relationships
- **Phase 3** implements proper distribution architecture when proven stable

### Business Rationale

- Immediate user experience improvement without development delays
- Preserved investment in Sprint 0001 deliverables
- Clear evolution toward production-ready architecture
- Reduced barrier to adoption and contribution

---

## Implementation Strategy

### Phase 1 Deliverables (Immediate)

- `STRUCTURE.md` - Comprehensive project layout explanation
- Updated `README.md` with developer vs user sections
- Navigation guide in documentation
- Clear contribution vs usage instructions

### Phase 2 Deliverables (Sprint 0002)

- Reorganized directory structure with logical groupings
- Build processes for template generation and validation
- Separate development and distribution documentation
- Enhanced testing for reorganized structure

### Phase 3 Deliverables (Future)

- Standalone `ai-guardrails-templates` repository
- Updated bootstrap script for external template fetching
- Cross-repository CI/CD synchronization
- Production distribution and release processes

---

## Consequences

### Positive Consequences

- **Immediate:** User confusion resolved through clear documentation
- **Short-term:** Professional project structure without disrupting working system
- **Long-term:** Scalable architecture ready for production adoption
- **Process:** Clear evolution path provides predictable improvement trajectory

### Negative Consequences

- **Maintenance:** Additional documentation to maintain during transition
- **Complexity:** Temporary increase in project complexity during Phase 2
- **Coordination:** Future Phase 3 will require careful cross-repository management
- **Migration:** End users will eventually need to adapt to new distribution model

### Risk Mitigation

- Phase 1 has zero technical risk (documentation only)
- Phase 2 changes will be validated with comprehensive testing
- Phase 3 will maintain backward compatibility during transition
- Each phase can be rolled back if issues arise

---

## Success Metrics

### Phase 1 Success Criteria

- New contributor onboarding time reduced by 50%
- User confusion reports eliminated
- Clear documentation feedback scores >4/5
- Zero disruption to existing functionality

### Phase 2 Success Criteria

- Professional project structure assessment >4/5
- All Sprint 0001 functionality preserved
- Build processes reduce template maintenance time by 25%
- Developer experience improved (measured via feedback)

### Phase 3 Success Criteria

- Template distribution independent of development repository
- Bootstrap script successfully fetches from external repository
- End user installation experience simplified
- Production-ready release and update processes operational

---

## Review and Updates

This ADR will be reviewed at the completion of each phase:

- **Phase 1 Review:** After documentation delivery (Week 1)
- **Phase 2 Review:** After Sprint 0002 completion
- **Phase 3 Review:** After repository split completion

Updates to this decision will be documented as new ADR versions or superseding ADRs as appropriate.

---

## References

- **Sprint 0001:** `docs/sprints/0001-Sprint-Plan-Modular-Bootstrap-Architecture.md`
- **Original Architecture:** `docs/decisions/ADR-001-modular-bootstrap-architecture.md`
- **User Feedback:** Project organization confusion reports
- **Template Repository:** `ai-guardrails-templates/` current implementation

---

*This ADR documents the decision for phased project structure clarification while preserving Sprint 0001 achievements and providing clear evolution toward production-ready architecture.*
