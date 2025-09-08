# ADR-006: Decouple Plugin Manifests from Target Structure Schema

- Date: 2025-01-07
- Status: Proposed

## Context

The current AI Guardrails Bootstrap System has tight coupling between plugin manifests and the global target structure schema. This creates several architectural problems:

### **Current Coupling Issues**

1. **Target Structure Extensions in Plugin Manifests**
   ```yaml
   # plugin-manifest.yaml (current)
   configuration:
     target_structure_extensions:
       ".ai/guardrails/":
         files:
           "acl.yml":
             required: false
             description: "ACL policy configuration"
   ```

2. **Global Schema Knowledge Required**
   - Plugin developers must understand the entire target structure
   - File patterns are validated against global target schema
   - Changes to target structure can break plugin compatibility

3. **Tight Validation Coupling**
   - Plugin file patterns must align with global expected_structure
   - Validation logic is spread across plugin manifests and global schema
   - No clear separation between "what the plugin provides" vs "what the system expects"

### **Problems with Current Approach**

1. **🔗 Tight Coupling**: Plugins can't be truly independent modules
2. **📚 Knowledge Burden**: Plugin developers need understanding of global architecture
3. **💥 Fragility**: Global schema changes can break plugin compatibility
4. **🔄 Duplication**: Structure information duplicated between plugins and global schema
5. **🧪 Testing Difficulty**: Plugins can't be validated independently
6. **🔌 Composition Complexity**: Adding new plugins requires global schema updates

### **Current Architecture**
```
Plugin Manifest ───────────────┐
│                              ▼
├── file_patterns ──────► Global Target Schema
├── target_structure_extensions ──► Validation
└── post_install                   ▲
                                   │
Core Components ───────────────────┘
```

## Decision

**Implement Plugin Structure Schema Composition** with clear separation of concerns:

### **1. Plugin-Specific Structure Schemas**

Each plugin defines its own structure schema:

```yaml
# src/plugins/guardrails-acl-kit/plugin-structure.schema.yaml
schema_version: "1.0.0"
plugin_name: "guardrails-acl-kit"

provides_structure:
  ".ai/guardrails/":
    files:
      "acl.yml":
        required: false
        description: "Access control list policy configuration"
        schema_ref: "acl.schema.json"
  
  ".ai/scripts/policy/":
    files:
      "acl_check.py":
        required: false
        description: "ACL validation script"
  
  ".githooks/pre-commit.d/":
    files:
      "acl-check.sh":
        required: false
        description: "Pre-commit ACL validation hook"

requires_structure:
  - ".ai/"              # Must exist (from core)
  - ".ai/scripts/"      # Must exist (from scripts component)
  - ".githooks/"        # Must exist (from githooks component)

conflicts_with:
  - "legacy-acl-system"  # Cannot coexist with other ACL plugins
```

### **2. Simplified Plugin Manifests**

Plugin manifests focus only on installation logic:

```yaml
# plugin-manifest.yaml (new format)
plugin:
  name: "guardrails-acl-kit"
  version: "1.0.0"
  description: "Access Control List enforcement"
  
  dependencies:
    - "core"
    - "scripts" 
    - "githooks"

components:
  acl-policy:
    description: "ACL policy configuration"
    source_patterns:
      - ".ai/guardrails/acl.yml"
    
  acl-scripts:
    description: "ACL validation scripts"  
    source_patterns:
      - ".ai/scripts/policy/acl_check.py"

  acl-hooks:
    description: "Git hooks for ACL enforcement"
    source_patterns:
      - ".githooks/pre-commit.d/acl-check.sh"
    hooks:
      pre_commit:
        category: "security"
        priority: 50
        script: "acl-check.sh"

profiles:
  acl-basic:
    components: ["acl-policy", "acl-scripts", "acl-hooks"]

post_install:
  - "chmod +x .ai/scripts/policy/acl_check.py"
  - "echo 'ACL enforcement configured'"
```

### **3. Schema Composition System**

New schema composition architecture:

```python
# src/packages/core/schema_composer.py
class SchemaComposer:
    def compose_target_schema(self, 
                            base_schema: Dict,
                            enabled_plugins: List[str]) -> Dict:
        """Compose final target schema from base + enabled plugins."""
        
        composed = deepcopy(base_schema)
        
        for plugin_name in enabled_plugins:
            plugin_schema = self.load_plugin_schema(plugin_name)
            composed = self.merge_schemas(composed, plugin_schema)
            
        return self.validate_composition(composed)
```

### **4. New Directory Structure**

```
src/plugins/guardrails-acl-kit/
├── plugin-manifest.yaml          # Installation logic only
├── plugin-structure.schema.yaml  # Structure provided by plugin
├── templates/                     # Plugin files
│   ├── .ai/guardrails/acl.yml
│   ├── .ai/scripts/policy/acl_check.py
│   └── .githooks/pre-commit.d/acl-check.sh
└── schemas/                       # Plugin-specific schemas
    └── acl.schema.json
```

### **5. Validation Pipeline**

```bash
# New validation approach
1. Validate plugin structure schema (independent)
2. Compose target schema from base + enabled plugins  
3. Validate composed schema for conflicts
4. Validate actual installation against composed schema
```

## Consequences

### **Positive Consequences**

1. **🔌 Plugin Independence**: Plugins can be developed, tested, and validated independently
2. **📦 True Modularity**: Clear separation between plugin capabilities and system requirements
3. **🧪 Testability**: Each plugin's structure can be validated in isolation
4. **🔄 Composability**: System composes final structure from base + enabled plugins
5. **📚 Reduced Complexity**: Plugin developers only need to understand their own structure
6. **🛡️ Conflict Detection**: System can detect structural conflicts between plugins
7. **🎯 Single Responsibility**: Plugin manifests focus on "how to install", schemas on "what structure"
8. **📈 Scalability**: Adding new plugins doesn't require global schema updates

### **Negative Consequences**

1. **🔄 Major Refactoring Required**: Significant changes to existing plugin system
2. **📚 Learning Curve**: New concepts for plugin developers (structure schemas)
3. **⚙️ Tooling Complexity**: Need schema composition and validation tools
4. **🐛 Debugging Complexity**: Composed schemas may be harder to debug
5. **📖 Documentation Overhead**: Need comprehensive guides for new architecture

### **Migration Plan**

**Phase 1: Extract Existing Structure Extensions**
```bash
# For each plugin with target_structure_extensions:
1. Create plugin-structure.schema.yaml 
2. Move structure extensions from manifest to schema
3. Update validation to use new schemas
```

**Phase 2: Implement Schema Composition**
```bash
1. Create SchemaComposer class
2. Update target structure validation to use composed schemas
3. Create conflict detection logic
4. Update CLI to show composed structure
```

**Phase 3: Update Plugin Manifests**
```bash
1. Remove target_structure_extensions from plugin manifests
2. Simplify manifests to focus on installation logic
3. Update plugin validation to use structure schemas
```

**Phase 4: Documentation and Tools**
```bash
1. Create plugin development guide with new architecture
2. Build tools for plugin structure validation
3. Create migration utilities for existing plugins
```

### **Success Metrics**

1. **Plugin Independence**: Plugins can be validated without global schema
2. **Conflict Detection**: System identifies plugin structure conflicts
3. **Developer Experience**: Plugin developers only need to understand their own structure
4. **Modularity**: Plugins can be added/removed without global schema changes
5. **Validation Quality**: Composed schemas accurately reflect final installation

### **Implementation Strategy**

**Contract-Based Interfaces**
```yaml
# Plugin declares what it provides and requires
provides:
  - "acl-enforcement"
  - "security-validation"
  
requires:
  - "git-hooks"
  - "python-scripts"
  
conflicts:
  - "legacy-acl-system"
```

**Namespace Isolation**
```yaml
# Each plugin operates in its own namespace
plugin_namespace: ".ai/plugins/acl-kit/"
structure_extensions:
  relative_to: "plugin_namespace"
```

**Composition Validation**
```python
def validate_composition(self, schemas: List[PluginSchema]) -> ValidationResult:
    """Validate that plugin schemas can be composed without conflicts."""
    conflicts = self.detect_file_conflicts(schemas)
    dependencies = self.validate_dependencies(schemas)
    return ValidationResult(conflicts=conflicts, dependencies=dependencies)
```

### **Alternative Considered and Rejected**

**Status Quo (Embedded Extensions)**
- ❌ Tight coupling
- ❌ Global knowledge required
- ✅ Simple implementation

**Namespace Isolation (Plugin Subdirectories)**
- ✅ Complete isolation
- ❌ Doesn't match existing structure conventions
- ❌ Breaks integration patterns

**Configuration-Only Approach**
- ✅ No schema changes needed
- ❌ Doesn't solve validation problems
- ❌ Still requires global knowledge
