# AI Guardrails Bootstrap - Quick Start

## Installation Options

### Option 1: Direct Use (No Installation)
```bash
git clone <repository>
cd ai-guardrails-bootstrap
bin/ai-guardrails list-profiles
bin/ai-guardrails install standard
```

### Option 2: System-wide Installation
```bash
git clone <repository>
cd ai-guardrails-bootstrap
./install
ai-guardrails list-profiles    # Works from anywhere
```

### Option 3: Temporary PATH Addition
```bash
export PATH="/path/to/ai-guardrails-bootstrap/bin:$PATH"
ai-guardrails list-profiles
```

## Project Structure

```
ai-guardrails-bootstrap/
├── bin/                               # Executable files
│   ├── ai-guardrails                  # Main CLI wrapper
│   ├── infrastructure_bootstrap.py    # Core engine
│   └── install.sh                     # System installer
├── src/                               # Source configuration
│   ├── installation-manifest.yaml     # Base manifest
│   ├── ai-guardrails-templates/       # Base templates
│   └── plugins/                       # Plugin directory
│       └── demos-on-rails-kit/        # Example plugin
└── install                            # Top-level installer
```

## Common Commands

```bash
# List available profiles and components
ai-guardrails list-profiles
ai-guardrails list-components

# Install profiles
ai-guardrails install minimal      # Core only
ai-guardrails install standard     # Recommended
ai-guardrails install full         # Everything
ai-guardrails install demo-basic   # Plugin profile

# Install specific components
ai-guardrails component core
ai-guardrails component demo-harness

# Target different directories
ai-guardrails --target ./my-project install standard
```

## Distribution

**For Teams**: Share the repository and run `./install.sh` on each machine.

**For CI/CD**: Use direct execution without installation:
```yaml
- name: Setup AI Guardrails
  run: |
    git clone <repo> ai-guardrails
    ./ai-guardrails/ai-guardrails install standard
```
