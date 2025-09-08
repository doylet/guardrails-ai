# 🏭 AI Guardrails Bootstrap Development Guide

> **Factory Environment:** This is where we build and improve the AI guardrails bootstrap system

## 🎯 Purpose

This `bootstrap-dev/` workspace is a **clean development environment** for improving the AI guardrails bootstrap system itself. It's completely separate from the consumer environment (root directory) to avoid namespace contamination.

## 🔍 What's Here vs What's Not

### ✅ **What IS in bootstrap-dev/**
- **Source code** for the bootstrap scripts
- **Template repository** management
- **Testing infrastructure** for validation
- **Development documentation** and architecture decisions
- **Build and release** artifacts

### ❌ **What is NOT in bootstrap-dev/**
- Applied AI guardrails (those are in the root directory)
- Consumer project files
- End-user configuration

## 🛠️ Development Workflow

### **1. Setup Development Environment**

```bash
cd bootstrap-dev/
```

### **2. Run Bootstrap System Tests**

```bash
# Test the modular bootstrap
./tests/test_modular_bootstrap.sh

# Test template system
./tests/test_templates.sh

# Test all components
./tests/run_all_tests.sh
```

### **3. Development and Testing**

```bash
# Doctor mode - verify system health
./src/ai_guardrails_bootstrap_modular.sh --doctor

# Test offline fallbacks
./src/ai_guardrails_bootstrap_modular.sh --offline

# Validate template repository
./tests/test_template_repo.sh
```

### **4. Building and Releases**

```bash
# Prepare release
cd dist/
./build_release.sh

# Test release candidate
./validate_release.sh
```

## 📁 Directory Structure

```
bootstrap-dev/
├── src/                           # Source code
│   ├── ai_guardrails_bootstrap_modular.sh    # Main modular script
│   └── ai_guardrails_bootstrap_unified.sh    # Legacy unified script
├── ai-guardrails-templates/       # Template repository
│   ├── .ai/                      # AI configuration templates
│   ├── ai/scripts/              # Automation script templates
│   └── .github/workflows/       # CI/CD workflow templates
├── tests/                        # Testing infrastructure
│   ├── test_modular_bootstrap.sh
│   ├── test_templates.sh
│   ├── test_template_repo.sh
│   └── run_all_tests.sh
├── docs/                         # Development documentation
│   └── decisions/               # Architecture Decision Records
├── dist/                         # Build and release artifacts
│   ├── releases/               # Version releases
│   └── build_release.sh        # Release automation
└── README.md                     # Bootstrap development guide
```

## 🧪 Testing Philosophy

### **Comprehensive Validation**

1. **Unit Tests**: Individual component functionality
2. **Integration Tests**: Full bootstrap workflow simulation
3. **Template Tests**: Verify template repository integrity
4. **Offline Tests**: Validate fallback mechanisms

### **Test Categories**

- **Functional**: Does the bootstrap work correctly?
- **Safety**: Are AI guardrails properly applied?
- **Robustness**: Does it handle edge cases and failures?
- **Performance**: Is the bootstrap efficient and fast?

## 🏗️ Architecture Principles

### **Modular Design**
- Clear separation of concerns
- Template-based configuration
- Offline fallback capabilities
- Version management

### **Safety First**
- AI guardrails applied by default
- Validation at every step
- Rollback mechanisms
- Comprehensive logging

### **Developer Experience**
- Clear error messages
- Doctor mode for diagnostics
- Extensive documentation
- Automated testing

## 🚀 Making Changes

### **Modifying Bootstrap Logic**

1. Edit `src/ai_guardrails_bootstrap_modular.sh`
2. Run `./tests/test_modular_bootstrap.sh`
3. Validate with `--doctor` mode
4. Update documentation if needed

### **Adding New Templates**

1. Modify `ai-guardrails-templates/`
2. Run `./tests/test_templates.sh`
3. Test full bootstrap with new templates
4. Document template changes

### **Release Process**

1. All tests pass: `./tests/run_all_tests.sh`
2. Build release: `cd dist && ./build_release.sh`
3. Validate release: `./validate_release.sh`
4. Tag and distribute

## 🔄 Consumer Environment Integration

### **How They're Separate**

- **bootstrap-dev/**: Factory where we build the system
- **Root directory**: Consumer environment with applied guardrails

### **How They Connect**

- Bootstrap scripts from `bootstrap-dev/src/` are distributed to end users
- Templates from `bootstrap-dev/ai-guardrails-templates/` are applied to consumer projects
- The root directory shows what a "successful bootstrap" looks like

### **Development Safety**

- Changes in `bootstrap-dev/` don't affect the applied guardrails in root
- Testing is isolated to the development environment
- Clear separation prevents accidental modification of consumer configuration

## 📝 Documentation Standards

- **ADR Format**: Architecture decisions in `docs/decisions/`
- **Inline Comments**: Explain complex bootstrap logic
- **README Updates**: Keep bootstrap-dev/README.md current
- **Change Logs**: Document all modifications

## 🎯 Success Metrics

- **All tests pass**: `./tests/run_all_tests.sh` returns 0
- **Doctor mode clean**: `--doctor` reports no issues
- **Template integrity**: Repository validation succeeds
- **Performance**: Bootstrap completes in < 30 seconds

## 🤝 Contributing

1. **Understand the separation**: Factory (bootstrap-dev/) vs Consumer (root)
2. **Test thoroughly**: All test suites must pass
3. **Document changes**: Update relevant documentation
4. **Follow patterns**: Maintain consistency with existing code
5. **Validate safety**: Ensure AI guardrails remain effective

---

> **Remember**: This is a development workspace. End users will never see these files - they only interact with the distributed bootstrap scripts and templates.
