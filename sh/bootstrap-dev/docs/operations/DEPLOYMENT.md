# AI Guardrails Bootstrap - Deployment Runbook

**Version:** 1.0.0
**Date:** 2025-09-03
**Status:** Production Ready

---

## Overview

This runbook provides comprehensive instructions for building, installing, and distributing the modular AI Guardrails Bootstrap solution. The architecture transitions from a monolithic 1,044-line script to a maintainable modular system with 64% code reduction and 83% maintenance time improvement.

---

## 🏗️ Build Process

### Prerequisites

- **Git** (version 2.0+)
- **Bash/Zsh** shell
- **curl** or **wget** for template fetching
- **shellcheck** (optional, for validation)
- **pre-commit** (optional, for development)

### Build Steps

1. **Clone the Repository**

   ```bash
   git clone <your-repo-url>
   cd scripts/sh
   ```

2. **Validate the Build**

   ```bash
   # Run comprehensive tests
   ./tests/run_all_tests.sh

   # Validate script syntax
   shellcheck ai_guardrails_bootstrap_modular.sh

   # Test core functionality
   ./ai_guardrails_bootstrap_modular.sh --doctor
   ```

3. **Package Templates**

   ```bash
   # Templates are already organized in ai-guardrails-templates/
   # Verify structure
   ls -la ai-guardrails-templates/templates/

   # Check version
   cat ai-guardrails-templates/version.txt
   ```

4. **Build Validation**

   ```bash
   # Test offline mode (embedded templates)
   ./ai_guardrails_bootstrap_modular.sh --offline --verbose

   # Test network mode (template fetching)
   ./ai_guardrails_bootstrap_modular.sh --template-repo file://$(pwd)/ai-guardrails-templates
   ```

---

## 📦 Distribution Methods

### Method 1: Direct Script Distribution

**Best for:** Quick deployment, single-file distribution

```bash
# Copy the modular script to target systems
scp ai_guardrails_bootstrap_modular.sh user@target:/usr/local/bin/
chmod +x /usr/local/bin/ai_guardrails_bootstrap_modular.sh

# Usage
ai_guardrails_bootstrap_modular.sh
```

**Pros:** Simple, self-contained with embedded fallbacks
**Cons:** Requires manual updates, no automatic template repository

### Method 2: Template Repository + Script

**Best for:** Organizations, version-controlled templates

```bash
# 1. Deploy template repository
git clone <your-repo-url> /opt/ai-guardrails
cd /opt/ai-guardrails

# 2. Install script globally
sudo cp ai_guardrails_bootstrap_modular.sh /usr/local/bin/
sudo chmod +x /usr/local/bin/ai_guardrails_bootstrap_modular.sh

# 3. Configure default template repository
export AI_GUARDRAILS_REPO="file:///opt/ai-guardrails/ai-guardrails-templates"

# Usage
ai_guardrails_bootstrap_modular.sh
```

**Pros:** Version control, organizational customization, local templates
**Cons:** Requires repository deployment

### Method 3: Remote Repository Distribution

**Best for:** Wide distribution, automatic updates

```bash
# 1. Host template repository on GitHub/GitLab
# https://github.com/your-org/ai-guardrails-templates

# 2. Configure script to use remote repository
export AI_GUARDRAILS_REPO="https://raw.githubusercontent.com/your-org/ai-guardrails-templates/main"

# 3. Distribute script only
curl -o ai_guardrails_bootstrap_modular.sh https://raw.githubusercontent.com/your-org/ai-guardrails/main/ai_guardrails_bootstrap_modular.sh
chmod +x ai_guardrails_bootstrap_modular.sh

# Usage
./ai_guardrails_bootstrap_modular.sh
```

**Pros:** Always latest templates, minimal distribution size
**Cons:** Requires network connectivity

### Method 4: Package Manager Distribution

**Best for:** Developer ecosystems, easy installation

#### Homebrew (macOS/Linux)

```bash
# Create Homebrew formula
# File: ai-guardrails-bootstrap.rb
class AiGuardrailsBootstrap < Formula
  desc "Modular AI Guardrails Bootstrap System"
  homepage "https://github.com/your-org/ai-guardrails"
  url "https://github.com/your-org/ai-guardrails/archive/v1.0.0.tar.gz"
  sha256 "..."

  def install
    bin.install "ai_guardrails_bootstrap_modular.sh" => "ai-guardrails"
    prefix.install "ai-guardrails-templates"
  end

  def caveats
    <<~EOS
      Set template repository location:
        export AI_GUARDRAILS_REPO="#{prefix}/ai-guardrails-templates"
    EOS
  end
end

# Install
brew install your-org/tap/ai-guardrails-bootstrap
```

#### NPM (Node.js ecosystem)

```bash
# Create package.json
{
  "name": "ai-guardrails-bootstrap",
  "version": "1.0.0",
  "bin": {
    "ai-guardrails": "./bin/ai-guardrails"
  },
  "files": ["bin/", "templates/"]
}

# Install
npm install -g ai-guardrails-bootstrap
ai-guardrails
```

#### Docker Distribution

```dockerfile
# Dockerfile
FROM alpine:latest
RUN apk add --no-cache bash curl git
COPY ai_guardrails_bootstrap_modular.sh /usr/local/bin/ai-guardrails
COPY ai-guardrails-templates/ /opt/ai-guardrails-templates/
ENV AI_GUARDRAILS_REPO="file:///opt/ai-guardrails-templates"
RUN chmod +x /usr/local/bin/ai-guardrails
ENTRYPOINT ["/usr/local/bin/ai-guardrails"]

# Build and distribute
docker build -t ai-guardrails:1.0.0 .
docker run -v $(pwd):/workspace ai-guardrails:1.0.0 -C /workspace
```

---

## 🚀 Installation Guide

### Quick Start (1-line install)

```bash
# Method 1: Direct download and run
curl -sSL https://raw.githubusercontent.com/your-org/ai-guardrails/main/ai_guardrails_bootstrap_modular.sh | bash

# Method 2: Download, verify, then run
curl -o ai_guardrails_bootstrap_modular.sh https://raw.githubusercontent.com/your-org/ai-guardrails/main/ai_guardrails_bootstrap_modular.sh
chmod +x ai_guardrails_bootstrap_modular.sh
./ai_guardrails_bootstrap_modular.sh
```

### Advanced Installation Options

```bash
# Install with custom template repository
./ai_guardrails_bootstrap_modular.sh --template-repo https://internal.company.com/ai-templates

# Install specific version
./ai_guardrails_bootstrap_modular.sh --template-branch v1.2.0

# Offline installation (embedded templates only)
./ai_guardrails_bootstrap_modular.sh --offline

# Force overwrite existing files
./ai_guardrails_bootstrap_modular.sh --force

# Install to specific directory
./ai_guardrails_bootstrap_modular.sh -C /path/to/project
```

### Organizational Installation

```bash
# 1. Clone your organization's template repository
git clone https://github.com/your-org/ai-guardrails-templates.git

# 2. Install with local templates
./ai_guardrails_bootstrap_modular.sh --template-repo file://$(pwd)/ai-guardrails-templates

# 3. Set environment for organization
echo 'export AI_GUARDRAILS_REPO="https://github.com/your-org/ai-guardrails-templates"' >> ~/.bashrc
```

---

## 🔧 Configuration

### Environment Variables

```bash
# Template repository URL
export AI_GUARDRAILS_REPO="https://github.com/your-org/ai-guardrails-templates"

# Default branch/tag
export AI_GUARDRAILS_BRANCH="main"

# Custom configuration file
export AI_GUARDRAILS_CONFIG="/path/to/config.yaml"
```

### Configuration File (.ai-guardrails-config)

```yaml
# .ai-guardrails-config
template_repository: "https://internal.company.com/ai-templates"
default_branch: "stable"
offline_mode: false
force_updates: false
verbose_logging: true

# Organizational customizations
organization:
  name: "Your Company"
  contact: "devops@company.com"
  internal_docs: "https://wiki.company.com/ai-guardrails"

# Template overrides
templates:
  ".ai/guardrails.yaml":
    custom_rules:
      - "internal-style-guide"
      - "company-security-rules"
```

---

## 📋 Validation & Testing

### Pre-deployment Testing

```bash
# 1. Run comprehensive test suite
./tests/run_all_tests.sh

# 2. Test installation in clean environment
docker run --rm -v $(pwd):/src alpine:latest sh -c "
  apk add bash curl git &&
  cd /src &&
  ./ai_guardrails_bootstrap_modular.sh --offline --verbose
"

# 3. Validate template syntax
find ai-guardrails-templates/templates -name '*.yaml' -exec yamllint {} \;
find ai-guardrails-templates/templates -name '*.json' -exec jq . {} \;

# 4. Cross-platform testing
# Test on macOS, Linux, Windows (WSL)
```

### Post-deployment Validation

```bash
# 1. Verify installation
./ai_guardrails_bootstrap_modular.sh --doctor

# 2. Check version tracking
cat .ai/version.txt

# 3. Validate pre-commit hooks
git add . && git commit -m "test" --dry-run

# 4. Test update mechanism
./ai_guardrails_bootstrap_modular.sh --update
```

---

## 🔄 Update & Maintenance

### Template Updates

```bash
# 1. Update template repository
cd ai-guardrails-templates
git pull origin main

# 2. Update version
echo "1.1.0" > version.txt
git add . && git commit -m "Update to v1.1.0"
git tag v1.1.0 && git push --tags

# 3. Test update process
./ai_guardrails_bootstrap_modular.sh --update --verbose
```

### Script Updates

```bash
# 1. Update modular script
# Edit ai_guardrails_bootstrap_modular.sh

# 2. Run validation
shellcheck ai_guardrails_bootstrap_modular.sh
./tests/run_all_tests.sh

# 3. Update version in script
sed -i 's/VERSION="1.0.0"/VERSION="1.1.0"/' ai_guardrails_bootstrap_modular.sh

# 4. Distribute updated script
```

---

## 🚨 Troubleshooting

### Common Issues

**Issue:** Template fetching fails

```bash
# Solution: Use offline mode
./ai_guardrails_bootstrap_modular.sh --offline

# Or specify alternative repository
./ai_guardrails_bootstrap_modular.sh --template-repo https://backup-repo.com/templates
```

**Issue:** Permission denied

```bash
# Solution: Fix permissions
chmod +x ai_guardrails_bootstrap_modular.sh
sudo chown -R $USER:$USER ai-guardrails-templates/
```

**Issue:** Network connectivity problems

```bash
# Solution: Configure proxy or use local repository
export https_proxy="http://proxy.company.com:8080"
# Or use local file:// URL
```

### Debugging

```bash
# Enable verbose logging
./ai_guardrails_bootstrap_modular.sh --verbose

# Check connectivity
curl -I https://github.com/your-org/ai-guardrails-templates

# Validate templates manually
./ai_guardrails_bootstrap_modular.sh --doctor
```

---

## 📊 Metrics & Success Criteria

### Deployment Success Metrics

- **Installation Success Rate:** > 95% across environments
- **Template Fetch Success:** > 99% with network connectivity
- **Offline Mode Success:** 100% (embedded templates)
- **Update Success Rate:** > 98% for existing installations

### Performance Metrics

- **Installation Time:** < 30 seconds (network mode)
- **Offline Installation:** < 10 seconds
- **Template Update Time:** < 15 seconds
- **Version Check Time:** < 5 seconds

### Maintenance Improvements

- **Template Update Time:** 30min → 5min (83% reduction)
- **Script Size:** 1,044 → 372 lines (64% reduction)
- **Template Organization:** 14 separate files vs embedded heredocs
- **Version Control:** Full Git history vs no versioning

---

## 🎯 Rollout Strategy

### Phase 1: Internal Testing (Week 1)

- Deploy to development environments
- Test with existing projects
- Validate migration process
- Collect feedback from developers

### Phase 2: Soft Launch (Week 2-3)

- Deploy alongside existing unified script
- Add deprecation warnings
- Provide migration tools
- Monitor adoption metrics

### Phase 3: Full Rollout (Week 4+)

- Announce full availability
- Migrate all existing installations
- Monitor success rates
- Address user feedback

### Phase 4: Legacy Sunset (Month 2)

- Deprecate unified script
- Archive old documentation
- Establish maintenance procedures
- Document lessons learned

---

## 📞 Support & Contact

- **Documentation:** [Repository Wiki](https://github.com/your-org/ai-guardrails/wiki)
- **Issues:** [GitHub Issues](https://github.com/your-org/ai-guardrails/issues)
- **Support:** <devops@company.com>
- **Emergency:** On-call rotation (internal)

---

*This runbook is version-controlled. Last updated: 2025-09-03*
