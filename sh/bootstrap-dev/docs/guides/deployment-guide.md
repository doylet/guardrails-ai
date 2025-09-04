# Deployment Guide: AI Guardrails Bootstrap

This guide covers building, installing, and distributing the modular AI guardrails bootstrap solution.

## Overview

The modular bootstrap architecture consists of:

- **Bootstrap Script**: `ai_guardrails_bootstrap_modular.sh` (372 lines)
- **Template Repository**: `ai-guardrails-templates/` (14 template files)
- **Documentation**: Migration guides, ADRs, and user documentation

## 🏗️ Build Process

### 1. Template Repository Setup

Create and version the template repository:

```bash
# 1. Initialize template repository
mkdir ai-guardrails-templates
cd ai-guardrails-templates

# 2. Set up structure
mkdir -p templates/{.ai,ai/{schemas,scripts},.github/{workflows,chatmodes},docs/decisions}

# 3. Copy template files
cp ../templates/* templates/

# 4. Create version file
echo "1.0.0" > version.txt

# 5. Create changelog
cat > CHANGELOG.md << 'EOF'
# Changelog

## [1.0.0] - 2025-09-03
### Added
- Initial modular template repository
- 14 template files extracted from monolithic script
- Semantic versioning support
EOF

# 6. Initialize git and tag
git init
git add .
git commit -m "Initial template repository v1.0.0"
git tag v1.0.0
```

### 2. Bootstrap Script Validation

Validate the bootstrap script before distribution:

```bash
# Run comprehensive tests
./tests/run_all_tests.sh

# Shellcheck validation
shellcheck ai_guardrails_bootstrap_modular.sh

# Test offline mode
./ai_guardrails_bootstrap_modular.sh --offline --doctor

# Test with custom repository
./ai_guardrails_bootstrap_modular.sh --template-repo file://$(pwd)/ai-guardrails-templates
```

### 3. Release Preparation

Prepare release artifacts:

```bash
# Create release directory
mkdir -p releases/v1.0.0

# Copy main script
cp ai_guardrails_bootstrap_modular.sh releases/v1.0.0/

# Create installation script
cat > releases/v1.0.0/install.sh << 'EOF'
#!/bin/bash
# AI Guardrails Bootstrap Installer
curl -fsSL https://raw.githubusercontent.com/yourorg/ai-guardrails/main/ai_guardrails_bootstrap_modular.sh -o ai_guardrails_bootstrap_modular.sh
chmod +x ai_guardrails_bootstrap_modular.sh
echo "✅ AI Guardrails Bootstrap installed successfully"
echo "Usage: ./ai_guardrails_bootstrap_modular.sh"
EOF
chmod +x releases/v1.0.0/install.sh

# Create checksums
cd releases/v1.0.0
sha256sum * > checksums.txt
cd ../..
```

## 📦 Distribution Methods

### Method 1: GitHub Releases (Recommended)

**Setup:**

```bash
# 1. Create GitHub repository for templates
gh repo create yourorg/ai-guardrails-templates --public
cd ai-guardrails-templates
git remote add origin https://github.com/yourorg/ai-guardrails-templates.git
git push -u origin main --tags

# 2. Create main repository for bootstrap script
gh repo create yourorg/ai-guardrails --public
git remote add origin https://github.com/yourorg/ai-guardrails.git
git push -u origin main

# 3. Create GitHub release
gh release create v1.0.0 \
  --title "AI Guardrails Bootstrap v1.0.0" \
  --notes "Initial release of modular bootstrap architecture" \
  releases/v1.0.0/*
```

**User Installation:**

```bash
# One-liner installation
curl -fsSL https://raw.githubusercontent.com/yourorg/ai-guardrails/main/releases/v1.0.0/install.sh | bash

# Manual installation
curl -fsSL https://raw.githubusercontent.com/yourorg/ai-guardrails/main/ai_guardrails_bootstrap_modular.sh -o ai_guardrails_bootstrap_modular.sh
chmod +x ai_guardrails_bootstrap_modular.sh
```

### Method 2: Package Managers

**Homebrew (macOS/Linux):**

```ruby
# Formula: ai-guardrails.rb
class AiGuardrails < Formula
  desc "AI Guardrails Bootstrap for development workflows"
  homepage "https://github.com/yourorg/ai-guardrails"
  url "https://github.com/yourorg/ai-guardrails/archive/v1.0.0.tar.gz"
  sha256 "your-sha256-here"
  version "1.0.0"

  def install
    bin.install "ai_guardrails_bootstrap_modular.sh" => "ai-guardrails"
  end

  test do
    system "#{bin}/ai-guardrails", "--help"
  end
end
```

**APT Package (Ubuntu/Debian):**

```bash
# Build .deb package
mkdir -p ai-guardrails-1.0.0/DEBIAN
mkdir -p ai-guardrails-1.0.0/usr/bin

# Control file
cat > ai-guardrails-1.0.0/DEBIAN/control << 'EOF'
Package: ai-guardrails
Version: 1.0.0
Architecture: all
Maintainer: Your Name <email@example.com>
Description: AI Guardrails Bootstrap
 Modular bootstrap script for AI development workflows
Depends: bash, curl
EOF

# Install script
cp ai_guardrails_bootstrap_modular.sh ai-guardrails-1.0.0/usr/bin/ai-guardrails
chmod +x ai-guardrails-1.0.0/usr/bin/ai-guardrails

# Build package
dpkg-deb --build ai-guardrails-1.0.0
```

### Method 3: Container Distribution

**Docker Image:**

```dockerfile
FROM alpine:latest
RUN apk add --no-cache bash curl git
COPY ai_guardrails_bootstrap_modular.sh /usr/local/bin/ai-guardrails
RUN chmod +x /usr/local/bin/ai-guardrails
ENTRYPOINT ["/usr/local/bin/ai-guardrails"]
```

```bash
# Build and publish
docker build -t yourorg/ai-guardrails:1.0.0 .
docker push yourorg/ai-guardrails:1.0.0

# User usage
docker run --rm -v $(pwd):/workspace -w /workspace yourorg/ai-guardrails:1.0.0
```

## 🚀 Installation Guide

### For End Users

**Quick Start:**

```bash
# 1. Install via curl
curl -fsSL https://raw.githubusercontent.com/yourorg/ai-guardrails/main/install.sh | bash

# 2. Apply to current project
./ai_guardrails_bootstrap_modular.sh

# 3. Verify installation
./ai_guardrails_bootstrap_modular.sh --doctor
```

**Advanced Installation:**

```bash
# Install to specific directory
curl -fsSL https://raw.githubusercontent.com/yourorg/ai-guardrails/main/ai_guardrails_bootstrap_modular.sh -o /usr/local/bin/ai-guardrails
chmod +x /usr/local/bin/ai-guardrails

# Use custom template repository
ai-guardrails --template-repo https://github.com/yourcompany/custom-templates

# Install specific version
ai-guardrails --template-branch v1.2.0

# Offline installation
ai-guardrails --offline
```

### For Organizations

**Custom Template Repository:**

```bash
# 1. Fork the template repository
gh repo fork yourorg/ai-guardrails-templates --clone

# 2. Customize templates
cd ai-guardrails-templates
# Edit templates in templates/ directory
# Update version.txt and CHANGELOG.md

# 3. Deploy to organization
git commit -am "Customize for organization"
git push

# 4. Configure users
export AI_GUARDRAILS_REPO="https://github.com/yourcompany/ai-guardrails-templates"
ai-guardrails
```

**Internal Distribution:**

```bash
# Host on internal GitLab/GitHub
git clone https://github.com/yourorg/ai-guardrails.git
cd ai-guardrails

# Update default repository URL in script
sed -i 's|DEFAULT_REPO=.*|DEFAULT_REPO="https://internal.company.com/ai-templates"|' ai_guardrails_bootstrap_modular.sh

# Distribute via internal package manager
# Upload to internal artifact repository
# Create internal documentation
```

## 🔄 Release Management

### Version Management

**Template Repository Versioning:**

```bash
# 1. Update version
echo "1.1.0" > version.txt

# 2. Update changelog
cat >> CHANGELOG.md << 'EOF'

## [1.1.0] - 2025-09-10
### Added
- New Python linting rules
- Support for TypeScript projects
### Fixed
- Pre-commit hook compatibility
EOF

# 3. Commit and tag
git add .
git commit -m "Release v1.1.0: Enhanced linting support"
git tag v1.1.0
git push --tags
```

**Bootstrap Script Versioning:**

```bash
# Update version in script
sed -i 's/SCRIPT_VERSION=.*/SCRIPT_VERSION="1.1.0"/' ai_guardrails_bootstrap_modular.sh

# Test new version
./tests/run_all_tests.sh

# Create release
gh release create v1.1.0 \
  --title "AI Guardrails v1.1.0" \
  --notes-file RELEASE_NOTES.md \
  ai_guardrails_bootstrap_modular.sh
```

### Automated Release Pipeline

**GitHub Actions:**

```yaml
# .github/workflows/release.yml
name: Release
on:
  push:
    tags: ['v*']

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3

    - name: Run tests
      run: ./tests/run_all_tests.sh

    - name: Create release
      uses: ncipollo/release-action@v1
      with:
        artifacts: "ai_guardrails_bootstrap_modular.sh"
        generateReleaseNotes: true
```

## 📊 Monitoring & Analytics

### Usage Tracking

**Add telemetry (optional):**

```bash
# In bootstrap script (with user consent)
if [[ "${AI_GUARDRAILS_TELEMETRY:-}" == "true" ]]; then
  curl -s -X POST https://analytics.yourorg.com/usage \
    -d "version=$SCRIPT_VERSION&repo=$PWD" \
    -H "Content-Type: application/json" || true
fi
```

**Monitor adoption:**

```bash
# GitHub API to track downloads
curl -s "https://api.github.com/repos/yourorg/ai-guardrails/releases" | \
  jq '.[] | {tag_name, published_at, download_count: [.assets[].download_count] | add}'
```

## 🛠️ Maintenance

### Regular Updates

**Template Maintenance:**

```bash
# Weekly template review
cd ai-guardrails-templates
git log --since="1 week ago" --oneline

# Update dependencies
# Review and update schema files
# Test with latest tool versions
```

**User Feedback Integration:**

```bash
# Monitor issues and discussions
gh issue list --repo yourorg/ai-guardrails --state open

# Create improvement roadmap
# Prioritize based on user feedback
# Update documentation
```

## 🎯 Success Metrics

Track deployment success with:

- **Download counts** from GitHub releases
- **Installation success rate** from user feedback
- **Template repository activity** (stars, forks, issues)
- **Migration completion rate** from unified script
- **Support request volume** and resolution time

This deployment strategy transforms the modular bootstrap architecture into a production-ready, scalable solution for AI guardrails distribution!
