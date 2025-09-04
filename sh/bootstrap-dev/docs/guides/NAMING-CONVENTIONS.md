# Documentation Naming Conventions

This document establishes canonical naming and formatting conventions for all documentation in the project.

---

## Folder Structure Conventions

### Primary Documentation Folders

```
docs/
├── coe/                    # Correction of Error documents
├── sprints/                # Sprint planning and retrospectives
├── decisions/              # Architecture Decision Records (ADRs)
├── guides/                 # User and developer guides
├── specs/                  # Technical specifications
├── runbooks/              # Operational procedures
├── templates/             # Document templates
└── archive/               # Archived/obsolete documents
```

### Specialized Folders

```
docs/
├── api/                   # API documentation
├── architecture/          # System architecture docs
├── compliance/           # Compliance and audit docs
├── integration/          # Integration guides
├── migration/            # Migration procedures
├── security/             # Security documentation
└── training/             # Training materials
```

---

## File Naming Conventions

### General Rules

- Use lowercase with hyphens (kebab-case): `my-document-name.md`
- Include dates in format `YYYY-MM-DD` when relevant
- Use semantic prefixes for document types
- Keep names descriptive but concise (max 50 characters)

### Document Type Prefixes

| Type | Prefix | Example |
|------|--------|---------|
| Architecture Decision Record | `ADR-{NNN}` | `ADR-001-microservices-architecture.md` |
| Correction of Error | `COE-{SYSTEM}-{ID}` | `COE-AUTH-001-login-timeout-fix.md` |
| Sprint Documentation | `{NNNN}-Sprint-Plan` | `0001-Sprint-Plan-Authentication.md` |
| Runbook | `RUN-{SYSTEM}` | `RUN-DEPLOYMENT-production-release.md` |
| Technical Specification | `SPEC-{SYSTEM}` | `SPEC-API-user-authentication.md` |
| User Guide | `GUIDE-{AUDIENCE}` | `GUIDE-DEVELOPER-getting-started.md` |

### Date-based Documents

- Sprint plans: `{NNNN}-Sprint-Plan-{Name}.md`
- Meeting notes: `{YYYY-MM-DD}-meeting-{type}.md`
- Status reports: `{YYYY-MM-DD}-status-report.md`
- Release notes: `{YYYY-MM-DD}-release-v{X.Y.Z}.md`

---

## Document Structure Standards

### Required Front Matter

All documents must include standardized front matter:

```markdown
# Document Title

**Document Type:** {Type from conventions above}
**Date:** YYYY-MM-DD
**Status:** Draft | Review | Approved | Archived
**Owner:** {Team/Individual}
**Version:** X.Y.Z

---
```

### Standard Sections

#### For All Documents

1. **Document Information** - Metadata table
2. **Executive Summary** - One paragraph overview
3. **Purpose & Scope** - Why and what
4. **Content Sections** - Variable based on type
5. **Document Control** - Version history and approvals

#### For Technical Documents

1. **Background & Context**
2. **Requirements**
3. **Technical Details**
4. **Implementation**
5. **Testing & Validation**
6. **Risks & Mitigation**

#### For Process Documents

1. **Process Overview**
2. **Roles & Responsibilities**
3. **Step-by-Step Procedures**
4. **Success Criteria**
5. **Troubleshooting**

---

## Content Formatting Standards

### Headers

- Use sentence case: "Getting started with API"
- Maximum 6 header levels (H1-H6)
- No periods at end of headers
- Use consistent hierarchy

### Lists

- Use `-` for unordered lists
- Use `1.` for ordered lists
- Indent consistently (2 spaces)
- Use parallel structure

### Code Blocks

- Specify language for syntax highlighting
- Include file paths as comments
- Use consistent indentation
- Add explanatory text before/after

### Tables

- Include headers
- Align consistently
- Keep columns manageable width
- Use markdown table format

### Links

- Use descriptive link text (not "click here")
- Include protocol for external links
- Use relative paths for internal docs
- Test all links before publishing

---

## Status and Lifecycle Management

### Document Status Values

- **Draft** - Work in progress, not ready for review
- **Review** - Ready for stakeholder review
- **Approved** - Reviewed and approved for use
- **Archived** - No longer current, kept for reference

### Version Numbering

- Use semantic versioning: `MAJOR.MINOR.PATCH`
- **MAJOR** - Significant restructure or purpose change
- **MINOR** - New sections or substantial updates
- **PATCH** - Small fixes, corrections, clarifications

### Review Cycles

- **Technical docs:** Quarterly review
- **Process docs:** Semi-annual review
- **Standards:** Annual review
- **Archived docs:** No regular review

---

## Quality Standards

### Writing Guidelines

- Use active voice
- Write in present tense
- Use clear, concise language
- Define acronyms on first use
- Include context for all examples

### Accessibility

- Use descriptive alt text for images
- Maintain proper heading hierarchy
- Ensure sufficient color contrast
- Test with screen readers

### Validation

- Spell check all content
- Validate all code examples
- Test all procedures
- Review with target audience

---

## Templates Usage

### When to Use Templates

- **Always** for new documents
- When structure is unclear
- For consistency across teams
- When training new writers

### Template Customization

- Remove unused sections
- Adapt to specific needs
- Maintain core structure
- Document customizations

### Template Updates

- Review templates quarterly
- Update based on feedback
- Version template changes
- Communicate updates to teams

---

## Examples

### Good Naming Examples

✅ `ADR-001-microservices-architecture.md`
✅ `0001-Sprint-Plan-User-Authentication.md`
✅ `COE-STANDARD-002-database-patterns.md`
✅ `GUIDE-DEVELOPER-api-integration.md`
✅ `2025-09-03-release-v2.1.0.md`

### Bad Naming Examples

❌ `Architecture Decision 1.md` (spaces, unclear numbering)
❌ `sprintplan.md` (no structure, unclear content)
❌ `Document1.md` (meaningless name)
❌ `IMPORTANT-READ-THIS.md` (unclear purpose)

### Good Structure Example

```markdown
# API Design Standards

**Document Type:** COE-STANDARD-001
**Date:** 2025-09-03
**Status:** Approved
**Owner:** Platform Team
**Version:** 1.2.0

---

## Executive Summary
This document establishes REST API design standards...

## Purpose & Scope
### Purpose
Define consistent API design patterns...
```

---

## Enforcement

### Automated Checks

- Filename validation in CI/CD
- Required front matter validation
- Link checking
- Spell checking

### Manual Review

- Template compliance
- Content quality
- Audience appropriateness
- Technical accuracy

### Non-Compliance

1. **Warning** - First violation, provide guidance
2. **Review Required** - Second violation, mandatory review
3. **Rejection** - Third violation, document rejected

---

*Last Updated: 2025-09-03 | Version: 1.0.0*
