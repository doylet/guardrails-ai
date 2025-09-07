# Enhanced Plugin Manifest Format
**Version:** 1.1.0  
**Phase:** 3.3 Enhanced Plugin Manifest Focus  
**Date:** January 6, 2025

## Overview
This document defines the enhanced plugin manifest format that focuses on sophisticated installation logic while maintaining clean separation from structure definitions (achieved in Phase 3.2).

## Enhanced Manifest Capabilities

### 🔧 **Enhanced Components System**
Components now support sophisticated installation logic:

```yaml
components:
  component-name:
    description: "Component description"
    file_patterns:
      - "path/to/files"
    required: true|false           # Whether component is mandatory
    install_order: 1               # Installation order (0-99)
    depends_on: [other-component]  # Component dependencies
    validation:                    # Post-install validation
      command: "validation command"
```

### 🎯 **Multi-Stage Installation Process**
Installation now supports multiple stages with sophisticated control:

```yaml
installation:
  pre_install:
    - name: "Check requirements"
      command: "validation command"
      on_error: "fail|skip|warn"
      error_message: "Custom error message"
      
  install:
    - name: "Installation step"
      command: "install command"
      condition: "not_exists(file) | profile_includes(component)"
      
  post_install:
    - name: "Post-install configuration"
      command: "configuration command"
      
  verify:
    - name: "Installation verification"
      command: "test command"
```

### ⚙️ **Configuration Management**
Enhanced configuration system with templates, user interaction, and environment variables:

```yaml
configuration:
  templates:
    config_name: "path/to/template.yaml"
    
  defaults:
    setting_name: default_value
    
  user_prompts:
    - name: "setting_name"
      prompt: "User-friendly question"
      default: "default_value"
      type: "boolean|string|choice"
      
  environment_vars:
    - name: "ENV_VAR_NAME"
      value: "${user.setting_name}"
```

### 🔄 **Conditional Execution**
Installation steps support conditional execution:

- `not_exists(file)` - Execute if file doesn't exist
- `profile_includes(component)` - Execute if component is in selected profile
- `user.setting_name` - Use user prompt responses
- `defaults.setting_name` - Use default configuration values

## Example: Enhanced ACL Plugin

The `copilot-acl-kit` serves as the reference implementation showcasing:

1. **Component Dependencies**: ACL scripts depend on policy configuration
2. **Installation Ordering**: Components install in specified order (0-4)
3. **Component Validation**: Each component can self-validate after installation
4. **Multi-stage Installation**: Pre-checks, installation, post-configuration, verification
5. **User Configuration**: Interactive prompts for strict mode and GitHub integration
6. **Conditional Logic**: Different behavior based on user choices and selected profiles
7. **Error Handling**: Meaningful error messages and failure modes

## Benefits of Enhanced Format

### ✅ **Installation Reliability**
- Pre-install validation catches issues early
- Component dependencies ensure proper installation order
- Post-install verification confirms successful installation

### ✅ **User Experience**
- Interactive configuration for customization
- Clear error messages when issues occur
- Flexible profile-based installation options

### ✅ **Maintainability**
- Clean separation between installation logic and structure definitions
- Self-documenting component dependencies and requirements
- Consistent installation patterns across plugins

## Migration Path

1. **Existing manifests continue working** - Enhanced features are additive
2. **Gradual adoption** - Plugins can adopt enhanced features incrementally  
3. **Reference implementation** - Use copilot-acl-kit as template for enhancements
4. **Backward compatibility** - Installation system supports both formats

## Next Steps

1. **Test enhanced installation logic** with copilot-acl-kit prototype
2. **Enhance installation system** to support new manifest features
3. **Create migration guides** for other plugins to adopt enhanced format
4. **Update validation** to support and encourage enhanced format features

## Related Documentation

- Phase 3.2: Target Structure Extensions Removal
- ADR-006: Plugin Schema Independence  
- Plugin Architecture Best Practices
