# Migration Guide: Unified to Modular Bootstrap

## Overview

The AI Guardrails Bootstrap is transitioning from a unified script approach to a modular template repository architecture. This guide will help you migrate seamlessly while preserving all existing functionality.

## Why Migrate?

The modular approach provides:

- **Faster Updates**: Template changes deploy instantly without script updates
- **Better Version Management**: Semantic versioning with clear change tracking
- **Offline Support**: Embedded fallbacks for network-restricted environments
- **Organization Customization**: Easy template repository forking and customization
- **Improved Maintainability**: Separate template files instead of embedded heredocs

## Quick Migration

### 1. Download the Modular Script

```bash
# Get the new modular script
curl -O https://your-repo.com/ai_guardrails_bootstrap_modular.sh
chmod +x ai_guardrails_bootstrap_modular.sh
```

### 2. Test Compatibility

```bash
# Run doctor mode to validate your environment
./ai_guardrails_bootstrap_modular.sh --doctor

# Test in a temporary directory first
mkdir test_migration && cd test_migration
git init
../ai_guardrails_bootstrap_modular.sh --apply
```

### 3. Migrate Your Project

```bash
# In your existing project directory
./ai_guardrails_bootstrap_modular.sh --apply --force
```

The `--force` flag ensures existing files are updated to the latest templates.

## Command Equivalence

All commands from the unified script work identically in the modular script:

| Unified Script | Modular Script | Description |
|---------------|----------------|-------------|
| `./ai_guardrails_bootstrap_unified.sh --apply` | `./ai_guardrails_bootstrap_modular.sh --apply` | Install/update templates |
| `./ai_guardrails_bootstrap_unified.sh --doctor` | `./ai_guardrails_bootstrap_modular.sh --doctor` | Diagnose issues |
| `./ai_guardrails_bootstrap_unified.sh --ensure` | `./ai_guardrails_bootstrap_modular.sh --ensure` | Create minimal setup |

## New Features in Modular Script

### Version Management

```bash
# Check available versions
./ai_guardrails_bootstrap_modular.sh --list-versions

# Update to latest
./ai_guardrails_bootstrap_modular.sh --update
```

### Offline Mode

```bash
# Use embedded templates (no network required)
./ai_guardrails_bootstrap_modular.sh --offline
```

### Custom Template Repository

```bash
# Use your organization's template repository
./ai_guardrails_bootstrap_modular.sh --template-repo https://github.com/yourorg/ai-templates
```

## Validation

After migration, verify everything works correctly:

### 1. Run Doctor Mode

```bash
./ai_guardrails_bootstrap_modular.sh --doctor
```

Should output:

```
== Doctor ==
✅ Key files present.
-- Doctor complete --
✅ Done.
```

### 2. Check Key Files

Verify these files exist and look correct:

- `.ai/guardrails.yaml`
- `.ai/envelope.json`
- `ai/schemas/copilot_envelope.schema.json`
- `ai/scripts/check_envelope.py`
- `.pre-commit-config.yaml`
- `.github/workflows/ai_guardrails_on_commit.yaml`

### 3. Test Pre-commit Hooks

```bash
# Install and test pre-commit (if you use it)
pre-commit install
pre-commit run --all-files
```

## Rollback Plan

If you encounter issues, you can easily rollback:

### Quick Rollback

```bash
# Restore from the last working unified installation
git checkout HEAD~1 -- .ai/ ai/ .github/ .pre-commit-config.yaml
```

### Full Rollback

```bash
# Remove modular installation and reinstall with unified script
rm -rf .ai/ ai/ .github/workflows/ai_guardrails_on_commit.yaml .pre-commit-config.yaml
./ai_guardrails_bootstrap_unified.sh --apply
```

## Troubleshooting

### Common Issues

#### "Unknown arg" Error

**Problem**: Using `--template-repo=URL` format
**Solution**: Use space-separated format: `--template-repo URL`

```bash
# Wrong
./ai_guardrails_bootstrap_modular.sh --template-repo=https://example.com/templates

# Correct
./ai_guardrails_bootstrap_modular.sh --template-repo https://example.com/templates
```

#### Network Connectivity Issues

**Problem**: Cannot fetch templates from repository
**Solution**: Use offline mode

```bash
./ai_guardrails_bootstrap_modular.sh --offline
```

#### Template Version Mismatch

**Problem**: Templates seem outdated
**Solution**: Force update to latest

```bash
./ai_guardrails_bootstrap_modular.sh --update --force
```

### Getting Help

1. **Check the logs**: Use `--verbose` for detailed output
2. **Run doctor mode**: `./ai_guardrails_bootstrap_modular.sh --doctor`
3. **Test in isolation**: Create a new directory and test there first
4. **Check network**: Ensure you can reach the template repository

## Organization Customization

### Fork Template Repository

Organizations can customize templates by forking the template repository:

1. Fork `ai-guardrails-templates` repository
2. Customize templates in your fork
3. Use your fork with `--template-repo`

```bash
./ai_guardrails_bootstrap_modular.sh --template-repo https://github.com/yourorg/ai-guardrails-templates
```

### Environment Variable

Set the default repository for your organization:

```bash
export AI_GUARDRAILS_REPO="https://github.com/yourorg/ai-guardrails-templates"
./ai_guardrails_bootstrap_modular.sh --apply
```

## Timeline

- **Now**: Unified script shows deprecation warning
- **2 weeks**: Unified script marked as legacy
- **4 weeks**: Unified script support ends
- **6 weeks**: Unified script removed

## Support

If you encounter issues during migration:

1. Check this guide's troubleshooting section
2. Run with `--verbose` for detailed logs
3. Test in a clean environment first
4. Report issues with full error output

The modular approach maintains 100% compatibility while providing significant improvements in maintainability and user experience.
