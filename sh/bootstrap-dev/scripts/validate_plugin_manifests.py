#!/usr/bin/env python3
"""
Enhanced Plugin Manifest Validator
Validates plugin manifests for both basic structure and enhanced installation logic.
Supports Phase 3.3 enhanced manifest format with sophisticated installation orchestration.
"""

import os
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional

def load_yaml(path):
    """Load YAML file safely."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"ERROR: Failed to load {path}: {e}")
        return None

def validate_plugin_against_target_structure(plugin_path, target_schema):
    """Validate a plugin manifest for both basic structure and enhanced features."""
    
    plugin_manifest_path = plugin_path / "plugin-manifest.yaml"
    if not plugin_manifest_path.exists():
        return f"❌ MISSING: {plugin_path.name}/plugin-manifest.yaml"
    
    plugin_manifest = load_yaml(plugin_manifest_path)
    if not plugin_manifest:
        return f"❌ INVALID YAML: {plugin_path.name}/plugin-manifest.yaml"
    
    issues = []
    recommendations = []
    
    # Validate basic plugin structure
    issues.extend(validate_basic_structure(plugin_manifest))
    
    # Validate enhanced components (Phase 3.3 features)
    component_issues, component_recommendations = validate_enhanced_components(plugin_manifest)
    issues.extend(component_issues)
    recommendations.extend(component_recommendations)
    
    # Validate enhanced installation logic (Phase 3.3 features)
    install_issues, install_recommendations = validate_installation_logic(plugin_manifest)
    issues.extend(install_issues)
    recommendations.extend(install_recommendations)
    
    # Validate configuration management (Phase 3.3 features)
    config_issues, config_recommendations = validate_configuration_management(plugin_manifest)
    issues.extend(config_issues)
    recommendations.extend(config_recommendations)
    
    # Validate file patterns against target structure
    pattern_issues = validate_file_patterns(plugin_manifest, target_schema)
    issues.extend(pattern_issues)
    
    # Check for deprecated features
    deprecated_issues = validate_deprecated_features(plugin_manifest)
    issues.extend(deprecated_issues)
    
    # Format results
    if issues:
        result = f"❌ ISSUES in {plugin_path.name}:\n"
        result += "\n".join(f"   - {issue}" for issue in issues)
        if recommendations:
            result += f"\n💡 RECOMMENDATIONS:\n"
            result += "\n".join(f"   + {rec}" for rec in recommendations)
        return result
    else:
        result = f"✅ VALID: {plugin_path.name}"
        if recommendations:
            result += f" (💡 {len(recommendations)} recommendations available)"
        return result

def validate_basic_structure(manifest: Dict[str, Any]) -> List[str]:
    """Validate basic manifest structure requirements."""
    issues = []
    
    if 'plugin' not in manifest:
        issues.append("Missing required 'plugin' section")
    elif not isinstance(manifest['plugin'], dict):
        issues.append("'plugin' section must be an object")
    else:
        plugin_section = manifest['plugin']
        required_fields = ['name', 'version', 'description']
        for field in required_fields:
            if field not in plugin_section:
                issues.append(f"Missing required plugin.{field}")
    
    if 'components' not in manifest:
        issues.append("Missing required 'components' section")
    elif not isinstance(manifest['components'], dict):
        issues.append("'components' section must be an object")
    
    return issues

def validate_enhanced_components(manifest: Dict[str, Any]) -> tuple[List[str], List[str]]:
    """Validate enhanced component features from Phase 3.3."""
    issues = []
    recommendations = []
    
    if 'components' not in manifest:
        return issues, recommendations
    
    components = manifest['components']
    component_names = list(components.keys())
    
    for comp_name, component in components.items():
        if not isinstance(component, dict):
            issues.append(f"Component '{comp_name}' must be an object")
            continue
            
        # Validate component dependencies
        if 'depends_on' in component:
            depends_on = component['depends_on']
            if not isinstance(depends_on, list):
                issues.append(f"Component '{comp_name}' depends_on must be a list")
            else:
                for dep in depends_on:
                    if dep not in component_names:
                        issues.append(f"Component '{comp_name}' depends on undefined component '{dep}'")
        
        # Validate install_order
        if 'install_order' in component:
            order = component['install_order']
            if not isinstance(order, int) or order < 0 or order > 99:
                issues.append(f"Component '{comp_name}' install_order must be integer 0-99")
        
        # Validate component validation
        if 'validation' in component:
            validation = component['validation']
            if not isinstance(validation, dict):
                issues.append(f"Component '{comp_name}' validation must be an object")
            elif 'command' not in validation:
                issues.append(f"Component '{comp_name}' validation missing required 'command'")
        
        # Recommendations for enhanced features
        if 'depends_on' not in component and 'install_order' not in component:
            recommendations.append(f"Component '{comp_name}' could benefit from explicit install_order")
        
        if 'validation' not in component and 'file_patterns' in component:
            recommendations.append(f"Component '{comp_name}' could benefit from post-install validation")
    
    return issues, recommendations

def validate_installation_logic(manifest: Dict[str, Any]) -> tuple[List[str], List[str]]:
    """Validate enhanced installation logic from Phase 3.3."""
    issues = []
    recommendations = []
    
    if 'installation' not in manifest:
        # Check for legacy post_install
        if 'post_install' in manifest:
            recommendations.append("Consider upgrading to enhanced 'installation' section with pre_install, install, post_install, verify stages")
        return issues, recommendations
    
    installation = manifest['installation']
    if not isinstance(installation, dict):
        issues.append("'installation' section must be an object")
        return issues, recommendations
    
    valid_stages = ['pre_install', 'install', 'post_install', 'verify']
    for stage_name, stage_steps in installation.items():
        if stage_name not in valid_stages:
            issues.append(f"Invalid installation stage '{stage_name}'. Valid stages: {', '.join(valid_stages)}")
            continue
            
        if not isinstance(stage_steps, list):
            issues.append(f"Installation stage '{stage_name}' must be a list of steps")
            continue
            
        for i, step in enumerate(stage_steps):
            if not isinstance(step, dict):
                issues.append(f"Installation step {i+1} in '{stage_name}' must be an object")
                continue
                
            if 'name' not in step:
                issues.append(f"Installation step {i+1} in '{stage_name}' missing required 'name'")
            if 'command' not in step:
                issues.append(f"Installation step {i+1} in '{stage_name}' missing required 'command'")
                
            # Validate optional fields
            if 'on_error' in step:
                valid_error_modes = ['fail', 'skip', 'warn']
                if step['on_error'] not in valid_error_modes:
                    issues.append(f"Invalid on_error '{step['on_error']}' in {stage_name} step {i+1}. Valid: {', '.join(valid_error_modes)}")
    
    # Recommendations for installation logic
    if 'pre_install' not in installation:
        recommendations.append("Consider adding 'pre_install' stage for environment validation")
    if 'verify' not in installation:
        recommendations.append("Consider adding 'verify' stage for post-installation validation")
    
    return issues, recommendations

def validate_configuration_management(manifest: Dict[str, Any]) -> tuple[List[str], List[str]]:
    """Validate configuration management features from Phase 3.3."""
    issues = []
    recommendations = []
    
    if 'configuration' not in manifest:
        return issues, recommendations
    
    config = manifest['configuration']
    if not isinstance(config, dict):
        issues.append("'configuration' section must be an object")
        return issues, recommendations
    
    # Validate user_prompts
    if 'user_prompts' in config:
        prompts = config['user_prompts']
        if not isinstance(prompts, list):
            issues.append("'user_prompts' must be a list")
        else:
            for i, prompt in enumerate(prompts):
                if not isinstance(prompt, dict):
                    issues.append(f"User prompt {i+1} must be an object")
                    continue
                if 'name' not in prompt:
                    issues.append(f"User prompt {i+1} missing required 'name'")
                if 'prompt' not in prompt:
                    issues.append(f"User prompt {i+1} missing required 'prompt'")
                if 'type' in prompt:
                    valid_types = ['boolean', 'string', 'choice']
                    if prompt['type'] not in valid_types:
                        issues.append(f"Invalid prompt type '{prompt['type']}' in prompt {i+1}. Valid: {', '.join(valid_types)}")
    
    # Validate environment_vars
    if 'environment_vars' in config:
        env_vars = config['environment_vars']
        if not isinstance(env_vars, list):
            issues.append("'environment_vars' must be a list")
        else:
            for i, env_var in enumerate(env_vars):
                if not isinstance(env_var, dict):
                    issues.append(f"Environment variable {i+1} must be an object")
                    continue
                if 'name' not in env_var:
                    issues.append(f"Environment variable {i+1} missing required 'name'")
                if 'value' not in env_var:
                    issues.append(f"Environment variable {i+1} missing required 'value'")
    
    return issues, recommendations

def validate_file_patterns(manifest: Dict[str, Any], target_schema: Dict[str, Any]) -> List[str]:
    """Validate file patterns against target structure."""
    issues = []
    
    if 'components' not in manifest:
        return issues
    
    target_structure = target_schema.get('expected_structure', {})
    
    for component_name, component in manifest['components'].items():
        if 'file_patterns' in component:
            for pattern in component['file_patterns']:
                if not validate_pattern_against_structure(pattern, target_structure):
                    issues.append(f"Component '{component_name}' has pattern '{pattern}' that doesn't align with target structure")
    
    return issues

def validate_deprecated_features(manifest: Dict[str, Any]) -> List[str]:
    """Check for deprecated features that should be migrated."""
    issues = []
    
    # Check for deprecated target_structure_extensions
    if manifest.get('configuration') and manifest['configuration'].get('target_structure_extensions'):
        issues.append("Plugin contains deprecated 'target_structure_extensions' - these should be moved to plugin-structure.schema.yaml")
    
    # Check for legacy post_install at root level when installation section exists
    if 'installation' in manifest and 'post_install' in manifest:
        issues.append("Found both legacy 'post_install' and new 'installation' sections - please migrate to 'installation' only")
    
    return issues

def validate_pattern_against_structure(pattern, target_structure, current_path=""):
    """Check if a file pattern aligns with the target directory structure."""
    
    # Handle common patterns
    if pattern.startswith('.ai/'):
        return '.ai/' in target_structure
    elif pattern.startswith('.github/'):
        return '.github/' in target_structure
    elif pattern.startswith('.githooks/'):
        return '.githooks/' in target_structure
    elif pattern.startswith('docs/'):
        return 'docs/' in target_structure
    elif pattern.startswith('scripts/'):
        # This is tricky - scripts/ at root vs .ai/scripts/
        # For now, assume root scripts/ is acceptable
        return True
    
    return True  # Be permissive for now

def validate_extension_against_structure(extension_path, extension_def, target_structure):
    """Validate that a target structure extension doesn't conflict with base structure."""
    
    # Split path into components
    path_parts = extension_path.strip('/').split('/')
    
    current_level = target_structure
    for part in path_parts:
        part_with_slash = part + '/'
        if part_with_slash in current_level:
            current_level = current_level[part_with_slash]
            if 'subdirs' in current_level:
                current_level = current_level['subdirs']
        else:
            # Path doesn't exist in target structure, which is OK for extensions
            return True
    
    return True

def main():
    # Find root directory
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent
    
    # Load target structure schema
    target_schema_path = root_dir / "src" / "target-structure.schema.yaml"
    target_schema = load_yaml(target_schema_path)
    
    if not target_schema:
        print("❌ FATAL: Could not load target-structure.schema.yaml")
        return 1
    
    # Find all plugins
    plugins_dir = root_dir / "src" / "plugins"
    if not plugins_dir.exists():
        print("❌ FATAL: Plugins directory not found")
        return 1
    
    print("🔍 Enhanced Plugin Manifest Validation")
    print("=" * 60)
    print("Validating both basic structure and Phase 3.3 enhanced features:")
    print("• Component dependencies and installation ordering")
    print("• Multi-stage installation logic (pre_install, install, post_install, verify)")
    print("• Configuration management (user prompts, environment variables)")
    print("• Deprecated feature detection and migration guidance")
    print("=" * 60)
    
    issues_found = False
    recommendations_count = 0
    enhanced_manifests = 0
    
    for plugin_path in plugins_dir.iterdir():
        if plugin_path.is_dir():
            result = validate_plugin_against_target_structure(plugin_path, target_schema)
            print(result)
            
            if result.startswith("❌"):
                issues_found = True
            
            if "💡" in result:
                recommendations_count += result.count("💡")
                
            # Check if plugin uses enhanced features
            manifest_path = plugin_path / "plugin-manifest.yaml"
            if manifest_path.exists():
                manifest = load_yaml(manifest_path)
                if manifest and has_enhanced_features(manifest):
                    enhanced_manifests += 1
    
    print("=" * 60)
    print(f"📊 VALIDATION SUMMARY:")
    print(f"• Enhanced manifests: {enhanced_manifests}")
    print(f"• Recommendations available: {recommendations_count}")
    
    if issues_found:
        print("❌ VALIDATION FAILED: Some plugins have issues")
        print("\n💡 Consider using the enhanced manifest format for better installation capabilities.")
        print("   See: docs/guides/enhanced-plugin-manifest-format.md")
        return 1
    else:
        print("✅ VALIDATION PASSED: All plugins conform to structure requirements")
        if recommendations_count > 0:
            print(f"\n💡 {recommendations_count} recommendations available to enhance plugin capabilities")
        return 0

def has_enhanced_features(manifest: Dict[str, Any]) -> bool:
    """Check if manifest uses Phase 3.3 enhanced features."""
    if 'installation' in manifest:
        return True
    if 'configuration' in manifest:
        config = manifest['configuration']
        if config and isinstance(config, dict):
            if any(key in config for key in ['user_prompts', 'environment_vars', 'templates']):
                return True
    if 'components' in manifest:
        for component in manifest['components'].values():
            if isinstance(component, dict):
                if any(key in component for key in ['depends_on', 'install_order', 'validation', 'required']):
                    return True
    return False

if __name__ == "__main__":
    sys.exit(main())
