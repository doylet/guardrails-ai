# Project Structure Guide

> **Clear explanation of how this AI Guardrails consumer project is organized and how it relates to the bootstrap development system.**

---

## 🎯 **Quick Navigation**

**👩‍💻 I'm a Developer (using applied guardrails)** → [Development Guide](#for-developers)
**🚀 I'm an End User (want to install guardrails)** → [Installation Guide](#for-end-users)
**🏭 I want to develop the bootstrap system** → [Bootstrap Development](#bootstrap-development)
**❓ I'm Confused** → [FAQ](#frequently-asked-questions)

---

## 📁 **Project Overview**

This repository is a **consumer of AI Guardrails** with applied safety and automation features. It also contains the **bootstrap development workspace** for building the guardrails system itself.

### **🎯 Consumer Environment (Root Directory)**
- **Purpose:** Project using applied AI guardrails for development safety
- **Contains:** Applied configuration, workflows, and automation scripts
- **Users:** Project developers working with AI safety guardrails

### **🏭 Factory Environment (bootstrap-dev/)**
- **Purpose:** Development workspace for building the bootstrap system
- **Contains:** Source code, tests, and build artifacts for guardrails
- **Users:** Developers improving the bootstrap system itself

---

## 🗂️ **Directory Structure Explained**

```
/scripts/sh/                                    # 🏠 PROJECT ROOT (Consumer)
│
├── 🎯 APPLIED AI GUARDRAILS                     # What this project uses
│   ├── .ai/                                   # Applied guardrail configuration
│   │   ├── envelope.json                      # Change tracking and scope
│   │   └── guardrails.yaml                    # Language-specific rules
│   ├── ai/                                    # Applied automation scripts
│   │   ├── scripts/                           # Linting, testing, validation
│   │   └── schemas/                           # Configuration schemas
│   ├── .github/                               # Applied CI/CD workflows
│   │   ├── workflows/                         # Automated safety checks
│   │   ├── chatmodes/                         # AI assistant instructions
│   │   └── pull_request_template.md           # Change tracking template
│   └── docs/                                  # Applied documentation templates
│
├── 🏭 BOOTSTRAP DEVELOPMENT                     # Factory for building guardrails
│   └── bootstrap-dev/                         # Clean development workspace
│       ├── src/                               # Source code and templates
│       │   ├── ai_guardrails_bootstrap_modular.sh    # Main bootstrap script
│       │   ├── ai_guardrails_bootstrap_unified.sh    # Legacy script
│       │   └── ai-guardrails-templates/              # Template repository
│       ├── tests/                             # Development test suites
│       ├── docs/                              # Development documentation
│       └── dist/                              # Build artifacts and releases
│
└── 📖 CONSUMER DOCUMENTATION                    # How to use applied guardrails
    ├── README.md                              # 👋 Start here
    ├── STRUCTURE.md                           # 📍 This document
    └── CONTRIBUTING.md                        # 🤝 How to contribute
```

---

## 👥 **User Guide by Role**

### **🎯 For End Users**
> *"I want to install AI guardrails in my project"*

**🎯 You want:** `bootstrap-dev/src/ai_guardrails_bootstrap_modular.sh`
**📍 Location:** Bootstrap development workspace
**📚 Guide:** [Installation Section](#installation)

```bash
# Quick start
curl -o bootstrap.sh https://raw.githubusercontent.com/.../ai_guardrails_bootstrap_modular.sh
chmod +x bootstrap.sh && ./bootstrap.sh
```

**What you DON'T need:**
- This specific repository (it's a consumer + development workspace)
- The development tools in `bootstrap-dev/tests/` or `bootstrap-dev/docs/`

### **👩‍💻 For Developers (Using Applied Guardrails)**
> *"I want to work on this project with AI safety guardrails"*

**🎯 You want:** Root directory with applied guardrails
**📍 Location:** `.ai/`, `ai/scripts/`, `.github/workflows/`
**📚 Guide:** [CONTRIBUTING.md](CONTRIBUTING.md)

```bash
# Your workflow with applied guardrails
git add . && git commit    # Pre-commit hooks enforce safety
./ai/scripts/lang_lint.sh  # Run applied linting
# CI workflows automatically validate changes
```

**What you DON'T need:**
- `bootstrap-dev/` - That's for bootstrap system development
- Template files - Those are already applied to this project

### **🏭 For Bootstrap System Developers**
> *"I want to improve the AI guardrails bootstrap system itself"*

**🎯 You want:** `bootstrap-dev/` workspace
**📍 Location:** Clean development environment
**📚 Guide:** [bootstrap-dev/README.md](bootstrap-dev/README.md)

```bash
# Bootstrap system development
cd bootstrap-dev/
./src/ai_guardrails_bootstrap_modular.sh --doctor
./tests/run_all_tests.sh
# Build and test the bootstrap system
```

**What you DON'T need:**
- Root directory applied guardrails (that's the consumer environment)
- Mixing your development with the applied guardrails

---

## 🔍 **Key Differences: Consumer vs Factory**

| Aspect | 🎯 Consumer (Root) | 🏭 Factory (bootstrap-dev/) |
|--------|-------------------|----------------------------|
| **Purpose** | Use applied AI guardrails | Build the bootstrap system |
| **Files** | Applied configuration & workflows | Source code & development tools |
| **Users** | Project developers | Bootstrap system developers |
| **Workflow** | Normal development with AI safety | Bootstrap system improvement |
| **AI Config** | `.ai/envelope.json` (applied) | Development configuration |
| **Documentation** | User guides & applied templates | Architecture & development docs |

---

## 🚀 **Installation**

### **For New Projects (End Users)**

```bash
# Install AI guardrails in your project
curl -sSL https://raw.githubusercontent.com/.../ai_guardrails_bootstrap_modular.sh | bash

# What this installs:
# - .ai/guardrails.yaml (AI safety configuration)
# - ai/scripts/ (automation tools)
# - .github/workflows/ (CI safety checks)
# - Pre-commit hooks (prevent unsafe commits)
```

### **For This Project (Already Applied)**

AI guardrails are already applied to this project. You can see them in:
- `.ai/` - Configuration and change tracking
- `ai/scripts/` - Automation and validation tools
- `.github/workflows/` - CI/CD safety workflows

---

## 🏭 **Bootstrap Development**

### **Development Workspace**

The `bootstrap-dev/` directory contains a clean development environment for improving the bootstrap system itself.

**Key Components:**
- **Source Code:** The actual bootstrap scripts and templates
- **Tests:** Comprehensive validation of bootstrap functionality
- **Documentation:** Architecture decisions and development guides
- **Releases:** Build artifacts and version management

### **Why Separate from Consumer Environment?**

**Problem Solved:** Previously, we had namespace contamination where development files mixed with applied guardrail files, making it impossible to distinguish "what we're building" from "what we're using."

**Solution:** Clean separation ensures:
- Clear development workflow for bootstrap system
- No accidental modification of applied guardrails
- Proper testing isolation
- Professional build and release process
- The template repository internals

---

### **For Developers**
> *"I want to improve the bootstrap system or add features"*

**🎯 You want:** Development workspace
**📍 Locations:** `docs/`, `tests/`, `ai/`, source scripts
**📚 Guide:** [CONTRIBUTING.md](#contributing)

```bash
# Development setup
git clone <repository>
cd scripts/sh
./tests/run_all_tests.sh
```

**Key files for development:**
- `ai_guardrails_bootstrap_modular.sh` - Main script source
- `tests/` - Test suites for validation
- `docs/decisions/` - Architecture decisions
- `docs/sprints/` - Development planning
- `ai/` - Development configuration

---

### **For Contributors**
> *"I want to improve templates or add new capabilities"*

**🎯 You want:** Template development
**📍 Location:** `ai-guardrails-templates/templates/`
**📚 Guide:** [Template Development Guide](#template-development)

```bash
# Template contribution
cd ai-guardrails-templates/templates
# Edit template files
# Test with bootstrap script
./../../ai_guardrails_bootstrap_modular.sh --template-repo file://$(pwd)/..
```

**Template categories:**
- `.ai/` - Configuration templates
- `ai/scripts/` - Automation scripts
- `.github/` - CI/CD workflows
- `docs/` - Documentation templates

---

## 🔍 **Key Files Explained**

### **🌟 Core Tools**

| File | Purpose | Audience | Size |
|------|---------|----------|------|
| `ai_guardrails_bootstrap_modular.sh` | ⭐ **Main bootstrap tool** | End Users | 372 lines |
| `ai_guardrails_bootstrap_unified.sh` | 📜 Legacy (being deprecated) | Migration | 1,044 lines |

### **📦 Distribution Content**

| Location | Purpose | Contains |
|----------|---------|----------|
| `ai-guardrails-templates/templates/` | Template files for user projects | 14 template files |
| `ai-guardrails-templates/version.txt` | Version tracking | Current: 1.0.0 |
| `ai-guardrails-templates/CHANGELOG.md` | Version history | Release notes |

### **🔧 Development Infrastructure**

| Location | Purpose | Audience |
|----------|---------|----------|
| `docs/` | Development documentation | Developers |
| `tests/` | Testing infrastructure | Developers |
| `ai/` | Development configuration | Developers |
| `.github/` | CI/CD automation | Developers |

---

## 🚀 **How Everything Works Together**

### **The Bootstrap Process**

1. **User runs bootstrap script** → `ai_guardrails_bootstrap_modular.sh`
2. **Script fetches templates** → From `ai-guardrails-templates/` (local) or remote repository
3. **Templates applied to user project** → Creates `.ai/`, `ai/scripts/`, `.github/` in user's project
4. **User project now has AI guardrails** → Pre-commit hooks, validation, documentation

### **Development Workflow**

1. **Developers modify** → Bootstrap script or template files
2. **Tests validate changes** → `tests/` directory contains validation suites
3. **Documentation updated** → `docs/` reflects changes and decisions
4. **Templates packaged** → `ai-guardrails-templates/` updated with new version
5. **Users get improvements** → Next bootstrap run fetches updated templates

### **Template Evolution**

```
Developer changes template →
Testing validates template →
Version bumped in template repository →
Bootstrap script fetches new version →
User projects get improvements
```

---

## 🎯 **What Phase We're In**

### **Current: Phase 1 - Documentation Clarity** *(This Sprint)*
- ✅ Created this STRUCTURE.md guide
- 🔄 Updating README.md with clear user vs developer sections
- 🔄 Adding navigation and user journey improvements
- 🎯 **Goal:** Eliminate confusion about project organization

### **Next: Phase 2 - Reorganization** *(Future Sprint)*
- Move files to clearer directory structure
- Separate development vs distribution concerns
- Add build processes for template packaging

### **Future: Phase 3 - Repository Split** *(When mature)*
- Extract `ai-guardrails-templates` to standalone repository
- Bootstrap script fetches from external template repository
- Clean separation for production use

---

## 📊 **Architecture Overview**

```
┌─────────────────────────────────────────────────────────────┐
│                    DEVELOPMENT REPOSITORY                   │
│  ┌─────────────────┐              ┌─────────────────────┐   │
│  │   SOURCE CODE   │              │   DOCUMENTATION     │   │
│  │                 │              │                     │   │
│  │ • Bootstrap     │              │ • Architecture      │   │
│  │   script        │              │   decisions         │   │
│  │ • Test suites   │              │ • Sprint plans      │   │
│  │ • CI/CD         │              │ • User guides       │   │
│  └─────────────────┘              └─────────────────────┘   │
│           │                                  │               │
│           ▼                                  ▼               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              TEMPLATE DISTRIBUTION                      │ │
│  │                                                         │ │
│  │  • 14 template files organized by category             │ │
│  │  • Version tracking and changelog                      │ │
│  │  • Ready for deployment to user projects               │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
                   USER PROJECT INSTALLATION
                         │
                         ▼
              ┌─────────────────────────┐
              │    USER'S PROJECT       │
              │                         │
              │ • .ai/ configuration    │
              │ • ai/scripts/ tools     │
              │ • .github/ workflows    │
              │ • Pre-commit hooks      │
              └─────────────────────────┘
```

---

## 🔄 **Migration from Legacy**

If you're coming from the old unified script:

### **What Changed**
- **Before:** 1,044-line monolithic script with embedded templates
- **After:** 372-line modular script + separate template repository
- **Benefit:** 64% code reduction, 83% faster template updates

### **Migration Path**
1. **Automatic Detection:** New script detects and migrates existing installations
2. **Backup Preservation:** Your existing `.ai/` configuration is backed up
3. **Validation:** Migration success is verified before completion
4. **Rollback Available:** Can restore previous state if needed

**See:** [migration-guide.md](migration-guide.md) for detailed instructions

---

## 🤔 **Frequently Asked Questions**

### **Q: Why is the template repository inside the development repository?**
A: This is Phase 1 of our organization improvement. We're keeping everything together during development, then will split into separate repositories for production use. See [ADR-002](docs/decisions/ADR-002-project-structure-reorganization.md).

### **Q: Which files do I need as an end user?**
A: Just `ai_guardrails_bootstrap_modular.sh`. Everything else is development infrastructure or gets fetched automatically.

### **Q: How do I contribute templates vs code improvements?**
A: **Templates:** Edit files in `ai-guardrails-templates/templates/`. **Code:** Modify the bootstrap script or testing infrastructure. See [CONTRIBUTING.md](#contributing).

### **Q: What's the difference between this and the old unified script?**
A: The new modular approach separates the tool (372 lines) from the templates (14 separate files), making updates 83% faster and reducing maintenance burden significantly.

### **Q: Why are there empty directories like `ai-guardrails-templates/scripts/`?**
A: These are placeholders for future utility scripts. They'll be populated in Phase 2 with template validation and packaging tools.

### **Q: How do I know if I have the latest templates?**
A: Run `./ai_guardrails_bootstrap_modular.sh --doctor` to check your installed version against the latest available.

---

## 📞 **Getting Help**

### **For End Users**
- 📖 [Installation Guide](README.md#installation)
- 🔧 [Troubleshooting](README.md#troubleshooting)
- 🐛 [Report Issues](https://github.com/your-org/ai-guardrails/issues)

### **For Developers**
- 📚 [Development Documentation](docs/)
- 🏗️ [Architecture Decisions](docs/decisions/)
- 🚀 [Sprint Planning](docs/sprints/)

### **For Contributors**
- 🤝 [Contributing Guide](CONTRIBUTING.md)
- 📋 [Template Development](docs/template-development.md)
- 💬 [Community Discussions](https://github.com/your-org/ai-guardrails/discussions)

---

## 🎯 **Success Metrics**

This structure documentation succeeds when:

- ✅ **New contributors** can get started in <5 minutes
- ✅ **End users** can install without confusion
- ✅ **Support questions** about organization drop to zero
- ✅ **User feedback** rates clarity >4/5

---

*Last updated: 2025-09-03 | This document evolves with the project - feedback welcome!*

---

**Navigation:** [🏠 README](README.md) | [📋 Sprint Plans](docs/sprints/) | [🏗️ Architecture](docs/decisions/) | [🚀 Deployment](docs/DEPLOYMENT.md)
