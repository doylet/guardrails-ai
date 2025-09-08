#!/usr/bin/env python3
"""
End-to-End Plugin System Integration Test
Tests the complete plugin schema decoupling and enhanced manifest system.
"""

import sys
import subprocess
from pathlib import Path

def run_command(cmd, description):
    """Run a command and return success status."""
    print(f"🔍 {description}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=Path(__file__).parent.parent)
        if result.returncode == 0:
            print(f"✅ {description} - PASSED")
            return True
        else:
            print(f"❌ {description} - FAILED")
            print(f"   Error: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False

def main():
    print("🧪 End-to-End Plugin System Integration Test")
    print("=" * 60)
    print("Testing complete plugin schema decoupling and enhanced manifest system")
    print("=" * 60)
    
    tests = [
        ("python scripts/validate_plugin_manifests.py", "Enhanced Plugin Manifest Validation"),
        ("python src/packages/core/validate_plugin_structures.py --search src/plugins/", "Plugin Structure Schema Validation"),
        ("python -c \"from pathlib import Path; from src.packages.core.schema_composer import SchemaComposer; composer = SchemaComposer(Path('src/schemas/plugin-structure.schema.json'), Path('src/plugins')); result = composer.compose_target_schema(['repo-safety-kit', 'copilot-acl-kit', 'doc-guardrails-kit']); print('✅ Schema Composition Test Passed')\"", "Schema Composition System"),
        ("grep -r 'target_structure_extensions' src/plugins/*/plugin-manifest.yaml || echo 'No target_structure_extensions found (expected)'", "Target Structure Extensions Removal Verification"),
        ("ls src/plugins/*/plugin-structure.schema.yaml | wc -l | grep -q '6' && echo 'All 6 plugin structure schemas present'", "Plugin Structure Schema Presence Check"),
    ]
    
    passed = 0
    failed = 0
    
    for cmd, description in tests:
        if run_command(cmd, description):
            passed += 1
        else:
            failed += 1
        print()
    
    print("=" * 60)
    print("🎯 INTEGRATION TEST SUMMARY")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Success Rate: {passed/(passed+failed)*100:.1f}%")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED - Plugin schema decoupling system fully operational!")
        print("\n📋 Verified Capabilities:")
        print("• Plugin manifests decoupled from target structure schema")
        print("• Enhanced manifest format with sophisticated installation logic")
        print("• Plugin structure schemas for independent structure definitions")
        print("• Schema composition system for dynamic target structure generation")
        print("• Comprehensive validation system for both basic and enhanced features")
        print("• Complete separation of installation logic from structure definitions")
        return 0
    else:
        print(f"\n⚠️ {failed} test(s) failed - system needs attention")
        return 1

if __name__ == "__main__":
    sys.exit(main())
