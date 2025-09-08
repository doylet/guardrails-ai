# AI Guardrails Bootstrap - Distribution Strategy

## Overview

The AI Guardrails Bootstrap system with declarative plugin architecture can be distributed in multiple ways to suit different deployment scenarios.

## Distribution Methods

### 1. Git Repository Distribution (Recommended)

**Setup**: Clone the entire repository including plugins
```bash
git clone https://github.com/your-org/ai-guardrails-bootstrap.git
cd ai-guardrails-bootstrap

# Install base profile
python3 infrastructure_bootstrap.py install standard

# Install plugin profiles
python3 infrastructure_bootstrap.py install demo-full
```

**Benefits**:
- ✅ Complete system with all plugins
- ✅ Version control for plugins and base system
- ✅ Easy updates via `git pull`
- ✅ Plugin development workflow

### 2. Standalone Script Distribution

**Setup**: Single-file installer with embedded manifests
```bash
curl -sSL https://raw.githubusercontent.com/your-org/ai-guardrails-bootstrap/main/install.sh | bash
```

**Implementation**: Create `install.sh` that:
- Downloads infrastructure_bootstrap.py
- Downloads installation-manifest.yaml
- Downloads template repository
- Optionally downloads plugins

### 3. Package Manager Distribution

**PyPI Package** (for Python environments):
```bash
pip install ai-guardrails-bootstrap
ai-guardrails install standard
```

**NPM Package** (for Node.js environments):
```bash
npx ai-guardrails-bootstrap install standard
```

### 4. Container Distribution

**Docker Image**:
```dockerfile
FROM python:3.11-slim
COPY . /app/ai-guardrails-bootstrap
WORKDIR /app/ai-guardrails-bootstrap
ENTRYPOINT ["python3", "infrastructure_bootstrap.py"]
```

Usage:
```bash
docker run --rm -v $(pwd):/workspace ai-guardrails-bootstrap install standard
```

### 5. CI/CD Integration Distribution

**GitHub Action**:
```yaml
- name: Setup AI Guardrails
  uses: your-org/ai-guardrails-bootstrap@v1
  with:
    profile: 'standard'
    plugins: 'demos-on-rails-kit'
```

## Plugin Distribution Strategies

### 1. Bundled Plugins (Current)
- Plugins included in main repository
- Versioned together with base system
- Best for tightly coupled plugins

### 2. External Plugin Repositories
```bash
# Install plugin from external repo
python3 infrastructure_bootstrap.py plugin add https://github.com/your-org/demo-plugin.git
python3 infrastructure_bootstrap.py install demo-profile
```

### 3. Plugin Registry
```bash
# Install from plugin registry
python3 infrastructure_bootstrap.py plugin install demos-on-rails-kit@latest
```

## Template Repository Distribution

### Option 1: Embedded Templates
- Templates bundled with infrastructure_bootstrap.py
- Single file distribution
- No external dependencies

### Option 2: Git Submodule
- Templates as git submodule
- Versioned separately
- Easy template updates

### Option 3: Download on Demand
- Templates downloaded when needed
- Reduced initial package size
- Requires internet connectivity

## Recommended Distribution Architecture

```
ai-guardrails-bootstrap/
├── infrastructure_bootstrap.py      # Core engine
├── installation-manifest.yaml       # Base manifest
├── install.sh                      # Standalone installer
├── src/ai-guardrails-templates/    # Base templates
├── plugins/                        # Official plugins
│   ├── demos-on-rails-kit/
│   ├── security-plugin/
│   └── custom-linting/
└── dist/                          # Distribution artifacts
    ├── pypi/                      # Python package
    ├── npm/                       # Node.js package
    └── docker/                    # Container images
```

## Implementation: Standalone Installer

Let me create a standalone installer script:

```bash
#!/bin/bash
# AI Guardrails Bootstrap - Standalone Installer
# Usage: curl -sSL https://raw.githubusercontent.com/.../install.sh | bash

set -euo pipefail

REPO_URL="https://github.com/your-org/ai-guardrails-bootstrap"
INSTALL_DIR="${AI_GUARDRAILS_DIR:-$HOME/.ai-guardrails}"
PROFILE="${AI_GUARDRAILS_PROFILE:-standard}"

echo "🚀 Installing AI Guardrails Bootstrap..."

# Create installation directory
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# Download core files
echo "📥 Downloading core files..."
curl -sSL "$REPO_URL/raw/main/infrastructure_bootstrap.py" -o infrastructure_bootstrap.py
curl -sSL "$REPO_URL/raw/main/installation-manifest.yaml" -o installation-manifest.yaml

# Download templates
echo "📥 Downloading templates..."
curl -sSL "$REPO_URL/archive/main.tar.gz" | tar xz --strip-components=1 "*/src/ai-guardrails-templates"

# Download plugins (optional)
if [[ "${AI_GUARDRAILS_PLUGINS:-}" ]]; then
    echo "📦 Downloading plugins..."
    for plugin in ${AI_GUARDRAILS_PLUGINS//,/ }; do
        mkdir -p "plugins/$plugin"
        curl -sSL "$REPO_URL/raw/main/plugins/$plugin/plugin-manifest.yaml" -o "plugins/$plugin/plugin-manifest.yaml"
    done
fi

# Install profile
echo "⚙️  Installing profile: $PROFILE"
python3 infrastructure_bootstrap.py install "$PROFILE"

echo "✅ AI Guardrails Bootstrap installed successfully!"
echo "📁 Installation directory: $INSTALL_DIR"
echo "🔧 To install additional profiles: python3 $INSTALL_DIR/infrastructure_bootstrap.py install <profile>"
```

## Usage Examples

### For End Users
```bash
# Quick install with defaults
curl -sSL https://ai-guardrails.example.com/install | bash

# Custom install
export AI_GUARDRAILS_PROFILE=full
export AI_GUARDRAILS_PLUGINS=demos-on-rails-kit,security-plugin
curl -sSL https://ai-guardrails.example.com/install | bash
```

### For CI/CD
```yaml
# .github/workflows/setup.yml
- name: Setup AI Guardrails
  run: |
    curl -sSL https://ai-guardrails.example.com/install | bash
    export PATH="$HOME/.ai-guardrails:$PATH"
```

### For Development Teams
```bash
# Clone full repository for development
git clone https://github.com/your-org/ai-guardrails-bootstrap.git
cd ai-guardrails-bootstrap

# Install development profile
python3 infrastructure_bootstrap.py install full

# Develop custom plugins
mkdir plugins/my-team-plugin
cat > plugins/my-team-plugin/plugin-manifest.yaml << 'EOF'
plugin:
  name: "my-team-plugin"
  version: "1.0.0"
  description: "Team-specific AI guardrails"
# ... rest of plugin definition
EOF
```

## Plugin Development Kit

### Plugin Scaffold Generator
```bash
python3 infrastructure_bootstrap.py plugin create my-plugin
# Creates: plugins/my-plugin/plugin-manifest.yaml with template
```

### Plugin Testing
```bash
python3 infrastructure_bootstrap.py plugin test my-plugin
# Validates plugin manifest and tests installation
```

### Plugin Publishing
```bash
python3 infrastructure_bootstrap.py plugin publish my-plugin
# Packages plugin for distribution
```

## Security Considerations

1. **Source Verification**: All downloads should verify checksums/signatures
2. **Plugin Sandboxing**: Plugins should not execute arbitrary code during installation
3. **Template Validation**: All templates should be validated before installation
4. **Network Security**: Support offline installation for secure environments

## Migration Path

1. **Phase 1**: Implement standalone installer
2. **Phase 2**: Create PyPI/NPM packages
3. **Phase 3**: Add plugin registry
4. **Phase 4**: Container and CI/CD integration
5. **Phase 5**: Plugin development kit

This distribution strategy provides flexibility for different use cases while maintaining the declarative, infrastructure-as-code approach.
