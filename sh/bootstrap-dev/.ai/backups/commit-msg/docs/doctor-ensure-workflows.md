# Doctor & Ensure Workflows

The `ai-guardrails` CLI provides diagnostic and repair workflows to maintain installation integrity.

## Doctor Workflow

Validates installation integrity without making changes.

### Commands

```bash
# Full diagnostic check
ai-guardrails doctor

# YAML-specific validation only
ai-guardrails doctor::yaml
ai-guardrails doctor yaml
```

### What Doctor Checks

1. **YAML Structure**: Validates syntax of key configuration files
   - `.ai/guardrails.yaml`
   - `.ai/envelope.json`
   - `.pre-commit-config.yaml`

2. **File Integrity**: Verifies all expected files are present for each component

3. **Component Status**: Reports installation status (fully/partially/not installed)

4. **Environment**: Checks dependencies (git, Python, pre-commit)

### Exit Codes

- `0`: All checks passed
- `1`: Issues found

## Ensure Workflow

Repairs installation issues automatically or in dry-run mode.

### Commands

```bash
# Dry run - show what would be fixed
ai-guardrails ensure

# Apply all repairs
ai-guardrails ensure --apply

# Apply only YAML-specific repairs
ai-guardrails ensure --apply-yaml

# Focus on specific area
ai-guardrails ensure yaml --apply
```

### What Ensure Fixes

1. **Missing YAML Files**: Reinstalls core configuration files
2. **Missing Components**: Reinstalls components with missing files
3. **Environment Issues**: Installs missing dependencies like pre-commit

### Repair Strategy

- **Safe**: Only installs missing files, never overwrites existing ones
- **Component-level**: Reinstalls entire components if any files are missing
- **Focused**: Can target specific areas (YAML, components, environment)

## Usage Examples

```bash
# Check installation health
ai-guardrails doctor

# Quick YAML validation
ai-guardrails doctor::yaml

# See what repairs are needed
ai-guardrails ensure

# Fix all issues automatically
ai-guardrails ensure --apply

# Fix only YAML issues
ai-guardrails ensure --apply-yaml
```

## Integration with CI/CD

```yaml
# Example GitHub Action
- name: Validate AI Guardrails Installation
  run: ai-guardrails doctor

- name: Auto-repair Installation
  run: ai-guardrails ensure --apply
```

The doctor/ensure pattern follows infrastructure-as-code principles, providing declarative validation and repair capabilities for consistent, reliable installations.
