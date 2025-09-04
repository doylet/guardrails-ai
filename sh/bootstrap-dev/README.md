# AI Guardrails Bootstrap - Development Workspace

> **Clean development environment for building the AI Guardrails Bootstrap system**

**🏭 Factory Status:** This is the development workspace - NOT the applied product
**📦 Product Location:** Parent directory (`../`) contains applied guardrails
**🎯 Purpose:** Build, test, and distribute the bootstrap system

---

## 🗂️ **Development Structure**

```
bootstrap-dev/                         # 🏭 CLEAN DEVELOPMENT WORKSPACE
├── src/                               # 📦 Source code and templates
│   ├── ai_guardrails_bootstrap_modular.sh     # Main bootstrap script (372 lines)
│   ├── ai_guardrails_bootstrap_unified.sh     # Legacy script (1,044 lines)
│   └── ai-guardrails-templates/               # Template repository
├── tests/                             # 🧪 Development test suites
├── docs/                              # 📚 Development documentation
├── dist/                              # 📦 Build artifacts and releases
└── README.md                          # This file
```

---

## 🎯 **What This Workspace Contains**

### **Source Code (`src/`)**
- **Main Script:** `ai_guardrails_bootstrap_modular.sh` - The modular bootstrap system
- **Legacy Script:** `ai_guardrails_bootstrap_unified.sh` - Original monolithic version
- **Templates:** `ai-guardrails-templates/` - Template files distributed to user projects

### **Testing (`tests/`)**
- **Unit Tests:** Bootstrap script functionality validation
- **Integration Tests:** End-to-end template deployment testing
- **Network Tests:** Template fetching and fallback scenarios

### **Documentation (`docs/`)**
- **Architecture Decisions:** ADR documents for design choices
- **Sprint Plans:** Development iteration planning
- **Deployment Guides:** Build and distribution procedures

### **Distribution (`dist/`)**
- **Releases:** Versioned builds ready for distribution
- **Release Notes:** Version history and changelog

---

## 🏭 **Development vs Applied Environment**

### **🏭 Development (THIS workspace):**
```bash
cd bootstrap-dev/
./src/ai_guardrails_bootstrap_modular.sh --help    # Development version
./tests/run_all_tests.sh                          # Run test suite
```

### **🎯 Applied Guardrails (Parent directory):**
```bash
cd ../                                   # Consumer environment
ls .ai/ ai/ .github/                    # Applied guardrail files
cat .ai/envelope.json                   # Applied configuration
```

---

## 🚀 **Development Workflow**

### **Setup Development Environment**
```bash
cd bootstrap-dev/
./tests/run_all_tests.sh                # Validate everything works
./src/ai_guardrails_bootstrap_modular.sh --doctor  # Test script functionality
```

### **Testing Changes**
```bash
# Test in clean environment
mkdir /tmp/test-project && cd /tmp/test-project
git init
/path/to/bootstrap-dev/src/ai_guardrails_bootstrap_modular.sh --apply

# Validate applied guardrails
ls .ai/ ai/ .github/                    # Check applied files
```

### **Building Releases**
```bash
cd bootstrap-dev/
./scripts/build-release.sh v1.1.0      # Build new release
ls dist/releases/v1.1.0/               # Verify artifacts
```

---

## 🔍 **Functionality Verification**

### **Unified vs Modular Comparison**
- **Unified Script:** 1,044 lines with embedded templates (legacy)
- **Modular Script:** 372 lines with template fetching (current)
- **Coverage Verification:** All unified functionality preserved in modular approach

### **AI Safety Features Preserved**
- ✅ **Envelope System:** JSON envelope for change tracking
- ✅ **Pre-commit Hooks:** Prevent unsafe code commits
- ✅ **Language Linting:** Multi-language code quality enforcement
- ✅ **Scope Checking:** Prevent AI from exceeding declared scope
- ✅ **Workflow Validation:** CI/CD integration for continuous safety

---

## 📋 **Key Differences from Parent Directory**

| Aspect | Bootstrap-Dev (Factory) | Parent Directory (Applied) |
|--------|------------------------|----------------------------|
| **Purpose** | Build the bootstrap system | Use applied guardrails |
| **AI Config** | Development configuration | Applied guardrail configuration |
| **Documentation** | Architecture & development | User guides & applied templates |
| **Tests** | System development tests | User project validation |
| **Scripts** | Bootstrap source code | Applied automation scripts |

---

## 🎯 **Important Notes**

### **Namespace Clarity**
- **THIS workspace:** Developing the bootstrap system
- **Parent workspace:** Using the bootstrap system
- **No contamination:** Clear separation of concerns

### **Safety Verification**
- All AI guardrail functionality from unified script preserved
- Template system ensures consistent guardrail application
- Development testing validates safety feature completeness

### **Development Guidelines**
- Always test changes in clean environments
- Never modify parent directory applied guardrails from here
- Use version control for all development changes
- Follow release process for distribution

---

**🏭 Development Lead:** Architecture Team
**📦 Product Owner:** Project Lead
**🎯 Consumer:** Parent directory project

---

*Clean namespace separation enables clear development while preserving applied guardrails integrity.*
