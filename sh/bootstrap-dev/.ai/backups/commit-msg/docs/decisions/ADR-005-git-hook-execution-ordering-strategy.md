# ADR-005: Git Hook Execution Ordering Strategy

- Date: 2025-01-07
- Status: Proposed

## Context

The AI Guardrails Bootstrap System uses modular git hooks where multiple plugins can contribute hook scripts to `.githooks/{hook-type}.d/` directories. The current `_run_hook` script executes these hooks in simple alphabetical order using `LC_ALL=C` sorting. This creates coordination challenges:

1. **Coordination Nightmare**: Independent plugin developers must coordinate on numbering schemes (e.g., `10-acl.sh`, `15-security.sh`) 
2. **Conflict Potential**: Multiple plugins could use the same prefix numbers
3. **Arbitrary Ordering**: Alphabetical sorting doesn't reflect logical dependencies or execution requirements
4. **Maintenance Burden**: Someone must manage a global numbering registry

**Current Implementation:**
```bash
# _run_hook script
LC_ALL=C
for s in "$dir"/*; do
    [ -f "$s" ] && [ -x "$s" ] || continue
    "$s" "$@"
done
```

**Existing Hook Examples:**
- `10-repo-safety.sh` (backup after commit)
- `15-acl.sh` (security validation) 
- `10-commit-msg.sh` (message formatting)
- `10-root-hygiene.sh` (cleanup)

## Decision

**Adopt a Semantic Priority System** with the following characteristics:

### 1. **Semantic Categories with Base Priorities**
```
10-19: VALIDATION    (format, lint, syntax)
30-39: SECURITY      (ACL, secrets, permissions)
50-59: QUALITY       (tests, coverage, metrics)
70-79: INTEGRATION   (external APIs, notifications)
90-99: CLEANUP       (backup, housekeeping)
```

### 2. **Plugin Manifest Hook Declaration**
```yaml
# plugin-manifest.yaml
hooks:
  pre_commit:
    category: "security"     # validation|security|quality|integration|cleanup
    priority: 50            # 0-100 within category
    script: "acl-check.sh"
    description: "Access control validation"
```

### 3. **Automatic Filename Generation**
System generates hook filenames as: `{base_priority + (priority/10):02d}-{plugin-name}-{script}.sh`

Examples:
- ACL plugin (security, priority 50) → `35-acl-kit-check.sh`
- Repo safety (cleanup, priority 10) → `91-repo-safety-backup.sh`
- Lint checks (validation, priority 20) → `12-lint-kit-check.sh`

### 4. **Fallback Rules**
1. **Within category**: Sort by plugin priority (0-100)
2. **Same priority**: Sort by plugin name alphabetically
3. **Missing category**: Default to `quality` category (50-59 range)

### 5. **Enhanced _run_hook Implementation**
```bash
#!/usr/bin/env bash
set -euo pipefail
hook="$(basename "$0")"
repo="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
dir="$repo/.githooks/${hook}.d"

if [ -d "$dir" ]; then
    LC_ALL=C  # Stable sorting
    for s in "$dir"/*; do
        [ -f "$s" ] && [ -x "$s" ] || continue
        echo "🔗 Executing: $(basename "$s")" >&2  # Optional: show execution order
        "$s" "$@"
    done
fi
```

## Consequences

### **Positive Consequences**

1. **🎯 Predictable Ordering**: Clear semantic categories ensure logical execution flow
2. **🔌 Plugin Independence**: No coordination needed between plugin developers
3. **📖 Self-Documenting**: Hook filenames indicate purpose and execution order
4. **🔧 Maintainable**: Easy to reason about and debug hook execution
5. **📈 Scalable**: New categories can be added without breaking existing hooks
6. **🔒 Conflict-Free**: System-generated filenames eliminate naming conflicts

### **Negative Consequences**

1. **🔄 Migration Required**: Existing numbered hooks need to be updated
2. **📚 Learning Curve**: Plugin developers must understand category system
3. **🎛️ Complexity**: More complex than simple alphabetical sorting
4. **⚙️ Tooling Dependency**: Requires manifest processing during installation

### **Migration Plan**

**Phase 1: Update Current Plugins**
```bash
# Convert existing hooks
10-repo-safety.sh     → 91-repo-safety-backup.sh     (cleanup)
15-acl.sh             → 35-acl-kit-check.sh          (security)
10-commit-msg.sh      → 12-commit-msg-format.sh      (validation)
10-root-hygiene.sh    → 19-root-hygiene-cleanup.sh   (validation)
```

**Phase 2: Update Plugin Manifests**
- Add `hooks` section with category and priority
- Update installation system to generate semantic filenames
- Validate category assignments

**Phase 3: Documentation and Guidelines**
- Create plugin development guide with category descriptions
- Document priority assignment best practices
- Provide migration tools for existing plugins

### **Success Metrics**

1. **Developer Experience**: Plugin developers can add hooks without coordination
2. **Execution Reliability**: Hooks execute in predictable, logical order
3. **Maintainability**: System administrators can understand hook flow
4. **Conflict Reduction**: Zero filename conflicts between plugins
5. **Documentation Quality**: Clear mapping from hook purpose to execution order

### **Alternative Considered and Rejected**

**Simple Alphabetical (Status Quo)**
- ❌ Arbitrary ordering
- ❌ Coordination required
- ✅ Simple implementation

**Plugin-Named Hooks (No Numbers)**
- ✅ No coordination needed
- ❌ No execution order control
- ❌ Unpredictable behavior

**Installation-Order Based**
- ❌ Non-deterministic across environments
- ❌ Difficult to reason about
- ❌ Breaks when plugins are reinstalled

**Full Dependency Resolution**
- ❌ Over-engineered for hook execution
- ❌ Complex dependency graph management
- ❌ Difficult to debug circular dependencies
