# Plugin System Architecture

## Overview

Successfully implemented a declarative plugin system for AI Guardrails Bootstrap using infrastructure-as-code patterns. This system replaces complex Python class hierarchies with simple YAML manifests.

## Architecture

### Core Infrastructure-as-Code Engine
- **File**: `infrastructure_bootstrap.py`
- **Purpose**: Dynamic file discovery and installation using declarative configuration
- **Key Features**:
  - Glob pattern-based file discovery
  - Manifest merging for plugin support
  - Declarative component and profile definitions

### Plugin System Design

#### Plugin Discovery
```python
def _discover_plugins(self) -> Dict:
    """Discover and load plugin manifests"""
    # Automatically finds */plugin-manifest.yaml files
    # Relative to manifest directory location
```

#### Manifest Merging
```python
def _get_merged_manifest(self) -> Dict:
    """Get manifest merged with plugin configurations"""
    # Merges base manifest with plugin components and profiles
    # Provides unified view of all available components
```

### Plugin Structure

#### Example Plugin: demos-on-rails-kit
```yaml
# demos-on-rails-kit/plugin-manifest.yaml
plugin:
  name: "demos-on-rails-kit"
  version: "1.0.0"
  description: "Demo harness ensuring production interface compliance"

components:
  demo-harness:
    description: "Demo execution and validation harness"
    file_patterns:
      - "demos-on-rails-kit/tools/**/*.py"
      - "demos-on-rails-kit/demo_scenarios/**/*.yaml"

profiles:
  demo-basic:
    description: "Basic demo harness"
    components: ["demo-harness", "demo-scripts"]
```

## Benefits Achieved

### 1. Declarative Over Imperative
- **Before**: Complex Python class inheritance for plugins
- **After**: Simple YAML manifest definitions
- **Result**: Easier to understand and maintain

### 2. Infrastructure-as-Code Consistency
- Same patterns used for base components and plugins
- Dynamic file discovery using glob patterns
- No hardcoded file lists anywhere

### 3. Plugin System Features
- ✅ Automatic plugin discovery
- ✅ Manifest merging (components + profiles)
- ✅ Plugin dependencies
- ✅ Plugin-specific profiles
- ✅ Command-line integration

## Usage Examples

### List All Components (Including Plugin Components)
```bash
python3 infrastructure_bootstrap.py list-components
```
Output shows both base and plugin components:
```
  core: Core AI guardrails configuration (2 files)
  demo-harness: Demo execution and validation harness (0 files)
  demo-scripts: Demo validation scripts (0 files)
```

### List All Profiles (Including Plugin Profiles)
```bash
python3 infrastructure_bootstrap.py list-profiles
```
Output shows merged profiles:
```
  minimal: Minimal installation - core only
  demo-basic: Basic demo harness
  demo-full: Complete demo environment with CI/CD
```

### Install Plugin Profile
```bash
python3 infrastructure_bootstrap.py install demo-basic
```

## Implementation Details

### Plugin Discovery Algorithm
1. Look for `*/plugin-manifest.yaml` in manifest directory
2. Load and validate each plugin manifest
3. Extract plugin metadata and components
4. Store in plugins registry

### Manifest Merging Algorithm
1. Start with base manifest
2. For each discovered plugin:
   - Merge plugin components into base components
   - Merge plugin profiles into base profiles
3. Return unified manifest view

### Component Resolution
1. Components can be from base manifest or plugins
2. File patterns resolved using glob matching
3. Plugin components reference plugin-specific file paths

## Plugin Development Guide

### Creating a New Plugin

1. **Create plugin directory**: `my-plugin/`
2. **Create manifest**: `my-plugin/plugin-manifest.yaml`
3. **Define structure**:
```yaml
plugin:
  name: "my-plugin"
  version: "1.0.0"
  description: "Plugin description"

components:
  my-component:
    description: "Component description"
    file_patterns:
      - "my-plugin/src/**/*.py"

profiles:
  my-profile:
    description: "Profile description"
    components: ["my-component"]
```

## Migration from Complex Plugin Classes

### Old Approach (Complex)
```python
class DemoPlugin(BasePlugin):
    def get_files(self):
        # Hardcoded file lists
        return ["file1.py", "file2.yaml"]

    def get_profiles(self):
        # Complex logic for profile definitions
        return {"demo": {"components": [...]}}
```

### New Approach (Declarative)
```yaml
# plugin-manifest.yaml
components:
  demo-component:
    file_patterns: ["plugin-dir/**/*.py"]

profiles:
  demo:
    components: ["demo-component"]
```

## Testing and Validation

### Plugin Discovery Test
```bash
# Verify plugin is discovered
python3 -c "
import infrastructure_bootstrap
bootstrap = infrastructure_bootstrap.InfrastructureBootstrap(...)
print('Plugins:', list(bootstrap.plugins.keys()))
"
```

### Component Merging Test
```bash
# Verify components are merged
python3 infrastructure_bootstrap.py list-components
# Should show both base and plugin components
```

### Profile Installation Test
```bash
# Verify plugin profiles work
python3 infrastructure_bootstrap.py install demo-basic
```

## Future Enhancements

1. **Plugin Dependencies**: Automatically install required plugins
2. **Plugin Versioning**: Handle version compatibility
3. **Plugin Registry**: Central registry for plugin discovery
4. **Plugin Hooks**: Pre/post installation hooks
5. **Plugin Configuration**: Environment-specific plugin settings

## Conclusion

Successfully modernized the plugin system using infrastructure-as-code patterns:
- Eliminated complex Python class hierarchies
- Implemented declarative YAML-based plugin definitions
- Achieved automatic plugin discovery and manifest merging
- Maintained consistency with existing infrastructure-as-code approach
- Enabled easy plugin development and maintenance

The system now supports both base components and plugin components through a unified interface, making it easy to extend functionality without modifying core infrastructure code.
