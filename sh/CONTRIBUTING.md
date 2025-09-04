# Contributing to AI Guardrails Bootstrap

> **Welcome! This guide helps you contribute effectively whether you're improving the bootstrap system itself or adding/enhancing templates.**

---

## 🎯 **Quick Start by Contribution Type**

**🔧 I want to improve the bootstrap system** → [System Development](#system-development)
**📋 I want to add/improve templates** → [Template Development](#template-development)
**📚 I want to improve documentation** → [Documentation](#documentation)
**🐛 I found a bug** → [Bug Reports](#bug-reports)
**💡 I have a feature idea** → [Feature Requests](#feature-requests)

---

## 🏗️ **Development Setup**

### Prerequisites
- **Git** (version 2.0+)
- **Bash/Zsh** shell
- **curl** or **wget**
- **Python 3.8+** (for validation scripts)
- **shellcheck** (recommended for script validation)

### Initial Setup
```bash
# 1. Fork and clone the repository
git clone https://github.com/YOUR-USERNAME/ai-guardrails.git
cd ai-guardrails/scripts/sh

# 2. Install development dependencies
pip install pre-commit yamllint jsonschema
npm install -g markdownlint-cli

# 3. Set up pre-commit hooks
pre-commit install

# 4. Validate your setup
./tests/run_all_tests.sh
./ai_guardrails_bootstrap_modular.sh --doctor
```

---

## 🔧 **System Development**

> **For improving the bootstrap script, testing infrastructure, or core functionality**

### What Counts as System Development
- Modifying `ai_guardrails_bootstrap_modular.sh`
- Adding/improving test suites in `tests/`
- Updating CI/CD workflows in `.github/`
- Improving build and deployment processes
- Adding new command-line options or features

### Development Workflow
```bash
# 1. Create feature branch
git checkout -b feature/your-feature-name

# 2. Make your changes
# Edit ai_guardrails_bootstrap_modular.sh or related files

# 3. Run tests
./tests/run_all_tests.sh
shellcheck ai_guardrails_bootstrap_modular.sh

# 4. Test with real projects
./ai_guardrails_bootstrap_modular.sh -C /path/to/test/project

# 5. Update documentation if needed
# Edit docs/ files as appropriate

# 6. Commit and push
git add .
git commit -m "feat: add new feature description"
git push origin feature/your-feature-name
```

### Testing Requirements
- [ ] All existing tests pass: `./tests/run_all_tests.sh`
- [ ] New functionality has test coverage
- [ ] Script passes shellcheck validation
- [ ] Manual testing with real projects completed
- [ ] Documentation updated for user-facing changes

---

## 📋 **Template Development**

> **For adding new templates or improving existing template files**

### What Counts as Template Development
- Adding new files to `ai-guardrails-templates/templates/`
- Modifying existing template files
- Updating template documentation
- Adding new template categories or capabilities

### Template Structure
```
ai-guardrails-templates/templates/
├── .ai/                          # Configuration templates
│   ├── guardrails.yaml
│   └── envelope.json
├── ai/scripts/                   # Automation script templates
│   ├── check_envelope.py
│   ├── lang_lint.sh
│   └── lang_test.sh
├── .github/                      # CI/CD workflow templates
│   ├── workflows/
│   └── pull_request_template.md
├── docs/                         # Documentation templates
│   └── decisions/ADR-template.md
└── .pre-commit-config.yaml       # Pre-commit configuration
```

### Template Development Workflow
```bash
# 1. Create template branch
git checkout -b template/your-template-name

# 2. Add or modify template files
cd ai-guardrails-templates/templates
# Create or edit template files

# 3. Test template integration
cd ../../
./ai_guardrails_bootstrap_modular.sh --template-repo file://$(pwd)/ai-guardrails-templates --force

# 4. Validate in real project
mkdir /tmp/test-project && cd /tmp/test-project
git init
/path/to/ai_guardrails_bootstrap_modular.sh --template-repo file:///path/to/ai-guardrails-templates

# 5. Update version and changelog
cd /path/to/ai-guardrails-templates
echo "1.1.0" > version.txt
echo "## 1.1.0 - Your changes description" >> CHANGELOG.md

# 6. Commit and test
git add .
git commit -m "feat(templates): add new template description"
./tests/test_bootstrap_modular.sh
```

### Template Guidelines
- **Idempotent:** Templates should be safe to apply multiple times
- **Configurable:** Use placeholder values that can be customized
- **Documented:** Include comments explaining purpose and usage
- **Validated:** Ensure templates produce valid configuration files
- **Compatible:** Test with different project types and structures

### Template Categories
| Category | Purpose | Examples |
|----------|---------|----------|
| `.ai/` | Core configuration | guardrails.yaml, envelope.json |
| `ai/scripts/` | Automation tools | linting, testing, validation |
| `.github/` | CI/CD integration | workflows, PR templates |
| `docs/` | Documentation | ADR templates, guides |
| Root files | Project setup | .pre-commit-config.yaml |

---

## 📚 **Documentation**

> **For improving guides, adding examples, or clarifying instructions**

### Documentation Types
- **User Guides:** README.md, STRUCTURE.md, installation guides
- **Developer Docs:** Architecture decisions (ADRs), technical specs
- **Process Docs:** Sprint plans, runbooks, deployment guides
- **Template Docs:** Template usage and customization guides

### Documentation Workflow
```bash
# 1. Create documentation branch
git checkout -b docs/your-improvement

# 2. Edit documentation files
# Follow NAMING-CONVENTIONS.md for structure

# 3. Validate documentation
markdownlint docs/
# Test any code examples
# Check all links work

# 4. Get feedback
# Share with team for review before committing

# 5. Commit changes
git add .
git commit -m "docs: improve explanation of feature X"
```

### Documentation Standards
- **Clear Audience:** Specify who the document is for
- **Actionable:** Readers should be able to complete tasks
- **Current:** Keep documentation in sync with code changes
- **Scannable:** Use headers, lists, and formatting for easy reading
- **Tested:** Verify all examples and procedures work

---

## 🐛 **Bug Reports**

### Before Reporting
1. **Check existing issues:** Search for similar problems
2. **Reproduce the issue:** Confirm it's reproducible
3. **Test with latest version:** Ensure you're using current code
4. **Gather information:** Collect relevant details

### Bug Report Template
```markdown
**Environment:**
- OS: macOS/Linux/Windows
- Shell: bash/zsh/fish
- Bootstrap version: [from --doctor output]
- Template version: [from .ai/version.txt]

**Steps to Reproduce:**
1. Command run: `./ai_guardrails_bootstrap_modular.sh ...`
2. Expected behavior: What should happen
3. Actual behavior: What actually happened

**Error Output:**
```
[Paste any error messages here]
```

**Additional Context:**
- Project type (Python, JavaScript, etc.)
- Any custom configuration
- Related issues or workarounds tried
```

---

## 💡 **Feature Requests**

### Before Requesting
1. **Check existing issues:** Look for similar requests
2. **Consider scope:** Does this fit the project goals?
3. **Think about implementation:** How might this work?
4. **Gather use cases:** Why is this needed?

### Feature Request Template
```markdown
**Problem Statement:**
Clear description of what problem this solves

**Proposed Solution:**
How you envision this working

**Use Cases:**
Specific scenarios where this would be helpful

**Alternative Solutions:**
Other ways this could be addressed

**Additional Context:**
Any mockups, examples, or related research
```

---

## 📋 **Pull Request Process**

### PR Checklist
- [ ] **Branch naming:** `feature/`, `template/`, `docs/`, or `fix/` prefix
- [ ] **Tests pass:** All existing tests continue to work
- [ ] **New tests added:** If adding functionality
- [ ] **Documentation updated:** For user-facing changes
- [ ] **Changelog updated:** For template changes
- [ ] **Self-review completed:** Code is clean and well-commented

### PR Description Template
```markdown
## Summary
Brief description of what this PR does

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Template addition/improvement
- [ ] Documentation update
- [ ] Breaking change

## Testing
- [ ] Tested manually with real projects
- [ ] All existing tests pass
- [ ] New tests added for new functionality

## Related Issues
Fixes #123, Addresses #456
```

### Review Process
1. **Automated checks:** CI/CD, linting, tests must pass
2. **Code review:** At least one team member approval
3. **Manual testing:** Reviewer tests changes locally
4. **Documentation review:** Ensure docs are accurate and complete

---

## 🎯 **Development Guidelines**

### Code Style
- **Shell scripts:** Follow Google Shell Style Guide
- **Python scripts:** Follow PEP 8
- **Documentation:** Follow project NAMING-CONVENTIONS.md
- **Commit messages:** Use conventional commits format

### Commit Message Format
```
type(scope): description

feat(templates): add new Python linting template
fix(bootstrap): resolve template fetching timeout
docs(readme): clarify installation instructions
test(integration): add cross-platform testing
```

### Branch Naming
- `feature/description` - New functionality
- `template/description` - Template additions/changes
- `fix/description` - Bug fixes
- `docs/description` - Documentation improvements
- `test/description` - Testing improvements

---

## 🤝 **Community Guidelines**

### Code of Conduct
- **Be respectful:** Treat all contributors with respect
- **Be collaborative:** Work together to improve the project
- **Be inclusive:** Welcome contributors of all backgrounds
- **Be constructive:** Provide helpful feedback and suggestions

### Getting Help
- **GitHub Discussions:** For questions and brainstorming
- **GitHub Issues:** For bugs and feature requests
- **Documentation:** Check STRUCTURE.md and guides first
- **Code Review:** Ask questions in PR comments

### Recognition
Contributors are recognized in:
- GitHub contributors list
- Release notes for significant contributions
- Documentation acknowledgments
- Community highlights

---

## 📊 **Release Process**

### Version Numbers
- **Major (X.0.0):** Breaking changes
- **Minor (X.Y.0):** New features, backward compatible
- **Patch (X.Y.Z):** Bug fixes, no new features

### Release Workflow
1. **Testing:** Comprehensive validation across environments
2. **Documentation:** Update guides and examples
3. **Changelog:** Document all changes
4. **Tagging:** Create git tags for versions
5. **Distribution:** Update template repositories

---

**Questions?** Check [STRUCTURE.md](STRUCTURE.md) for project organization or open a [GitHub Discussion](https://github.com/your-org/ai-guardrails/discussions).

---

*Last updated: 2025-09-03 | This guide evolves with the project*
