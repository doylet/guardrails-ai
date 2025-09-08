#!/usr/bin/env python3
"""
Integration Test for Phase 2 Task 2.1
Tests bootstrap integration points with schema composition system
"""

import sys
import json
from pathlib import Path

# Add the src directory to the path for testing
sys.path.insert(0, str(Path(__file__).parent / "src"))

from packages.core.bootstrap import InfrastructureBootstrap


def test_bootstrap_integration():
    """Test the bootstrap integration with target structure manager."""
    print("🧪 Testing Bootstrap Integration with Schema Composition System")
    print("=" * 60)
    
    # Initialize bootstrap system
    try:
        bootstrap = InfrastructureBootstrap()
        print("✅ Bootstrap system initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize bootstrap system: {e}")
        return False
    
    # Test target structure schema composition
    try:
        schema = bootstrap.get_target_structure_schema()
        print(f"✅ Target structure schema composed successfully")
        print(f"   Schema version: {schema.get('schema_version', 'unknown')}")
        print(f"   Structure entries: {len(schema.get('expected_structure', {}))}")
    except Exception as e:
        print(f"❌ Failed to compose target structure schema: {e}")
        return False
    
    # Test plugin discovery integration
    try:
        enabled_plugins = bootstrap.plugin_system.get_enabled_plugins()
        print(f"✅ Plugin discovery working")
        print(f"   Enabled plugins: {len(enabled_plugins)}")
        for plugin in enabled_plugins:
            print(f"     - {plugin}")
    except Exception as e:
        print(f"❌ Failed to discover plugins: {e}")
        return False
    
    # Test plugin structure loading
    try:
        plugin_structures = bootstrap.plugin_system.get_plugin_structures()
        print(f"✅ Plugin structures loaded")
        print(f"   Plugin structures found: {len(plugin_structures)}")
        for structure in plugin_structures:
            plugin_name = structure.get('plugin_name', 'unknown')
            provides_count = len(structure.get('provides_structure', {}))
            print(f"     - {plugin_name}: {provides_count} structure entries")
    except Exception as e:
        print(f"❌ Failed to load plugin structures: {e}")
        return False
    
    # Test structure validation
    try:
        validation_result = bootstrap.validate_target_structure()
        print(f"✅ Structure validation working")
        print(f"   Structure valid: {validation_result['valid']}")
        if validation_result['missing_required']:
            print(f"   Missing required: {len(validation_result['missing_required'])}")
            for missing in validation_result['missing_required'][:3]:  # Show first 3
                print(f"     - {missing}")
            if len(validation_result['missing_required']) > 3:
                print(f"     ... and {len(validation_result['missing_required']) - 3} more")
    except Exception as e:
        print(f"❌ Failed to validate structure: {e}")
        return False
    
    # Test comprehensive structure report
    try:
        report = bootstrap.get_structure_report()
        print(f"✅ Structure report generation working")
        print(f"   Total plugins: {report['total_plugins']}")
        print(f"   Structure valid: {report['structure_valid']}")
        print(f"   Plugin dependencies: {len(report['plugin_dependencies'])}")
    except Exception as e:
        print(f"❌ Failed to generate structure report: {e}")
        return False
    
    print("\n🎉 All integration tests passed!")
    return True


def test_schema_composer_directly():
    """Test the schema composer directly."""
    print("\n🧪 Testing Schema Composer Directly")
    print("=" * 40)
    
    try:
        from packages.core.schema_composer import SchemaComposer
        
        # Test with minimal schemas and proper paths
        base_schema_path = Path("src/target-structure.schema.yaml")
        plugins_dir = Path("src/plugins")
        
        composer = SchemaComposer(base_schema_path, plugins_dir)
        print("✅ Schema composer created successfully")
        
        # Test with minimal schemas
        base_schema = {
            "schema_version": "1.0.0",
            "expected_structure": {
                ".ai/": {
                    "required": True,
                    "description": "Base AI directory"
                }
            }
        }
        
        plugin_structures = [
            {
                "plugin_name": "test-plugin",
                "provides_structure": {
                    ".ai/test/": {
                        "description": "Test directory",
                        "required": True
                    }
                }
            }
        ]
        
        composed = composer.compose_target_schema(base_schema, plugin_structures)
        
        # Handle CompositionResult
        if hasattr(composed, 'composed_schema'):
            schema = composed.composed_schema
        else:
            schema = composed
            
        print("✅ Schema composition working")
        print(f"   Composed structure entries: {len(schema.get('expected_structure', {}))}")
        
    except Exception as e:
        print(f"❌ Schema composer test failed: {e}")
        return False
    
    return True


if __name__ == "__main__":
    print("🚀 Running Phase 2 Task 2.1 Integration Tests")
    print("=" * 60)
    
    success = True
    
    # Test schema composer directly first
    if not test_schema_composer_directly():
        success = False
    
    # Test full bootstrap integration
    if not test_bootstrap_integration():
        success = False
    
    if success:
        print("\n🎉 All Phase 2 Task 2.1 integration tests passed!")
        print("✅ Bootstrap integration points are working correctly")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed")
        sys.exit(1)
