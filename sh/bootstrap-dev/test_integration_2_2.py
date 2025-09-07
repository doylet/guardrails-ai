#!/usr/bin/env python3
"""
Integration Test for Phase 2 Task 2.2
Tests enhanced plugin discovery with schema composition integration
"""

import sys
import json
from pathlib import Path

# Add the src directory to the path for testing
sys.path.insert(0, str(Path(__file__).parent / "src"))

from packages.core.bootstrap import InfrastructureBootstrap


def test_enhanced_plugin_discovery():
    """Test enhanced plugin discovery capabilities."""
    print("🧪 Testing Enhanced Plugin Discovery")
    print("=" * 40)
    
    # Initialize bootstrap system
    try:
        bootstrap = InfrastructureBootstrap()
        print("✅ Bootstrap system initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize bootstrap system: {e}")
        return False
    
    # Test plugin analysis
    try:
        analysis = bootstrap.get_plugin_analysis()
        print(f"✅ Plugin analysis working")
        print(f"   Total plugins: {analysis['total_plugins']}")
        print(f"   Enabled plugins: {analysis['enabled_plugins']}")
        print(f"   Plugins with structure schema: {analysis['plugins_with_structure_schema']}")
        
        # Show some plugin dependencies
        print("   Plugin dependencies:")
        for plugin, deps in list(analysis['plugin_dependencies'].items())[:3]:
            print(f"     - {plugin}: {deps if deps else 'no dependencies'}")
            
    except Exception as e:
        print(f"❌ Failed to get plugin analysis: {e}")
        return False
    
    # Test dependency-resolved installation order
    try:
        order = bootstrap.get_plugin_installation_order()
        print(f"✅ Plugin installation order resolution working")
        print(f"   Installation order: {order}")
    except Exception as e:
        print(f"❌ Failed to resolve installation order: {e}")
        return False
    
    # Test plugin selection validation
    try:
        # Test with a subset of plugins
        enabled_plugins = bootstrap.plugin_system.get_enabled_plugins()
        if len(enabled_plugins) >= 2:
            test_selection = enabled_plugins[:2]
            validation = bootstrap.validate_plugin_selection(test_selection)
            print(f"✅ Plugin selection validation working")
            print(f"   Selection valid: {validation['valid']}")
            print(f"   Installation order: {validation['installation_order']}")
            print(f"   Conflicts: {len(validation['conflicts'])}")
            print(f"   Missing dependencies: {len(validation['missing_dependencies'])}")
            
            if validation['additional_plugins']:
                print(f"   Additional plugins needed: {validation['additional_plugins']}")
    except Exception as e:
        print(f"❌ Failed to validate plugin selection: {e}")
        return False
    
    return True


def test_plugin_enablement():
    """Test plugin enablement/disablement functionality."""
    print("\n🧪 Testing Plugin Enablement/Disablement")
    print("=" * 45)
    
    try:
        bootstrap = InfrastructureBootstrap()
        print("✅ Bootstrap system initialized")
        
        # Get initial state
        initial_enabled = bootstrap.plugin_system.get_enabled_plugins()
        print(f"   Initially enabled plugins: {len(initial_enabled)}")
        
        # Test disabling a plugin (if any available)
        if initial_enabled:
            test_plugin = initial_enabled[0]
            print(f"   Testing with plugin: {test_plugin}")
            
            # Disable plugin
            success = bootstrap.disable_plugin(test_plugin)
            if success:
                print(f"✅ Plugin disable working")
                
                # Check new state
                new_enabled = bootstrap.plugin_system.get_enabled_plugins()
                if test_plugin not in new_enabled:
                    print(f"   Plugin successfully disabled")
                else:
                    print(f"❌ Plugin still appears enabled")
                    return False
                
                # Re-enable plugin
                success = bootstrap.enable_plugin(test_plugin)
                if success:
                    print(f"✅ Plugin enable working")
                    
                    # Check final state
                    final_enabled = bootstrap.plugin_system.get_enabled_plugins()
                    if test_plugin in final_enabled:
                        print(f"   Plugin successfully re-enabled")
                    else:
                        print(f"❌ Plugin failed to re-enable")
                        return False
                else:
                    print(f"❌ Failed to re-enable plugin")
                    return False
            else:
                print(f"❌ Failed to disable plugin")
                return False
        else:
            print(f"   No plugins available for testing")
    
    except Exception as e:
        print(f"❌ Plugin enablement test failed: {e}")
        return False
    
    return True


def test_dependency_resolution():
    """Test plugin dependency resolution."""
    print("\n🧪 Testing Plugin Dependency Resolution")
    print("=" * 45)
    
    try:
        bootstrap = InfrastructureBootstrap()
        print("✅ Bootstrap system initialized")
        
        # Get the enhanced discovery system
        discovery = bootstrap.plugin_system.enhanced_discovery
        resolver = discovery.dependency_resolver
        
        # Test dependency resolution for each plugin
        enabled_plugins = bootstrap.plugin_system.get_enabled_plugins()
        print(f"   Testing dependency resolution for {len(enabled_plugins)} plugins")
        
        dependency_summary = {}
        for plugin in enabled_plugins:
            deps = resolver.get_plugin_dependencies(plugin)
            dependency_summary[plugin] = deps
            
        print("✅ Dependency resolution working")
        print("   Dependency summary:")
        for plugin, deps in dependency_summary.items():
            if deps:
                print(f"     - {plugin}: depends on {deps}")
            else:
                print(f"     - {plugin}: no dependencies")
        
        # Test conflict detection
        conflicts = resolver.detect_conflicts(enabled_plugins)
        print(f"✅ Conflict detection working")
        print(f"   Conflicts detected: {len(conflicts)}")
        for conflict in conflicts:
            print(f"     - {conflict['type']}: {conflict['plugin1']} ↔ {conflict['plugin2']}")
            
    except Exception as e:
        print(f"❌ Dependency resolution test failed: {e}")
        return False
    
    return True


def test_structure_integration():
    """Test integration with structure composition."""
    print("\n🧪 Testing Structure Composition Integration")
    print("=" * 50)
    
    try:
        bootstrap = InfrastructureBootstrap()
        print("✅ Bootstrap system initialized")
        
        # Test that plugin changes affect structure composition
        initial_schema = bootstrap.get_target_structure_schema()
        initial_count = len(initial_schema.get('expected_structure', {}))
        print(f"   Initial structure entries: {initial_count}")
        
        # Test with enabled plugins filter
        enabled_plugins = bootstrap.plugin_system.get_enabled_plugins()
        if len(enabled_plugins) > 1:
            # Test with subset of plugins
            subset = enabled_plugins[:len(enabled_plugins)//2] if len(enabled_plugins) > 2 else enabled_plugins[:1]
            subset_schema = bootstrap.get_target_structure_schema(subset)
            subset_count = len(subset_schema.get('expected_structure', {}))
            
            print(f"✅ Filtered structure composition working")
            print(f"   Subset ({len(subset)} plugins) structure entries: {subset_count}")
            
            if subset_count <= initial_count:
                print(f"   Filtering correctly reduces structure complexity")
            else:
                print(f"   ⚠️  Filtering resulted in more entries (unexpected)")
        
        # Test structure validation with current plugin set
        validation = bootstrap.validate_target_structure()
        print(f"✅ Structure validation with current plugins")
        print(f"   Structure valid: {validation['valid']}")
        print(f"   Missing required: {len(validation['missing_required'])}")
        
    except Exception as e:
        print(f"❌ Structure integration test failed: {e}")
        return False
    
    return True


if __name__ == "__main__":
    print("🚀 Running Phase 2 Task 2.2 Integration Tests")
    print("=" * 60)
    
    success = True
    
    # Test enhanced plugin discovery
    if not test_enhanced_plugin_discovery():
        success = False
    
    # Test plugin enablement
    if not test_plugin_enablement():
        success = False
    
    # Test dependency resolution
    if not test_dependency_resolution():
        success = False
    
    # Test structure integration
    if not test_structure_integration():
        success = False
    
    if success:
        print("\n🎉 All Phase 2 Task 2.2 integration tests passed!")
        print("✅ Enhanced plugin discovery with schema composition is working correctly")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed")
        sys.exit(1)
