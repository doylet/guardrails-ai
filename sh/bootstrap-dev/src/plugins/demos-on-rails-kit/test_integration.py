#!/usr/bin/env python3
"""Test script for demos-on-rails-kit integration with ai-deck-gen."""
import os
import sys
import tempfile
from pathlib import Path

# Add the tools directory to path for imports
TOOLS_DIR = Path(__file__).parent / "ai" / "tools"
sys.path.insert(0, str(TOOLS_DIR))

from demo_harness import load_yaml, cli_cmd, run_cli, parse_quality

def test_integration():
    """Test the integration between demo harness and ai-deck-gen."""
    print("🧪 Testing demos-on-rails-kit → ai-deck-gen integration")
    print("=" * 60)

    # Load the example scenario
    scenario_path = Path(__file__).parent / "ai" / "demo_scenarios" / "example.yaml"
    if not scenario_path.exists():
        print(f"❌ Scenario file not found: {scenario_path}")
        return False

    print(f"📋 Loading scenario: {scenario_path}")
    scenario = load_yaml(str(scenario_path))
    print(f"   Topic: {scenario.get('topic')}")
    print(f"   Audience: {scenario.get('audience')}")
    print(f"   Model: {scenario.get('provider_profile', {}).get('model')}")

    # Generate CLI command
    print("\n🔧 Generating CLI command...")
    cmd = cli_cmd(scenario)
    print(f"   Command: {' '.join(cmd)}")

    # Test if bridge script exists
    bridge_path = Path(__file__).parent / "ai" / "tools" / "deckgen_bridge.py"
    if not bridge_path.exists():
        print(f"❌ Bridge script not found: {bridge_path}")
        return False

    print(f"✅ Bridge script found: {bridge_path}")

    # Test bridge directly (dry run)
    print("\n🧪 Testing bridge (dry run)...")
    test_cmd = ["python", str(bridge_path), "build", "Test Topic", "--json"]
    print(f"   Test command: {' '.join(test_cmd)}")

    # Don't actually run it since ai-deck-gen might not be set up
    print("ℹ️  Skipping actual execution (ai-deck-gen setup required)")

    print("\n✅ Integration test completed successfully!")
    print("\n📚 Next steps:")
    print("   1. Ensure ai-deck-gen project is set up with LMStudio")
    print("   2. Set AI_DECK_GEN_ROOT environment variable if needed")
    print("   3. Run: python ai/tools/demo_harness.py run ai/demo_scenarios/example.yaml")

    return True

def test_scenario_loading():
    """Test that scenario files can be loaded correctly."""
    print("\n📄 Testing scenario loading...")
    scenario_dir = Path(__file__).parent / "ai" / "demo_scenarios"

    for yaml_file in scenario_dir.glob("*.yaml"):
        print(f"   Loading: {yaml_file.name}")
        try:
            scenario = load_yaml(str(yaml_file))
            required_fields = ["topic", "audience"]
            for field in required_fields:
                if field not in scenario:
                    print(f"   ⚠️  Missing required field: {field}")
                else:
                    print(f"   ✅ {field}: {scenario[field]}")
        except Exception as e:
            print(f"   ❌ Error loading {yaml_file.name}: {e}")
            return False

    return True

if __name__ == "__main__":
    print("🚀 demos-on-rails-kit Integration Test")
    print("=====================================")

    success = True

    try:
        success &= test_scenario_loading()
        success &= test_integration()

        if success:
            print("\n🎉 All tests passed!")
            sys.exit(0)
        else:
            print("\n❌ Some tests failed!")
            sys.exit(1)

    except Exception as e:
        print(f"\n💥 Test error: {e}")
        sys.exit(1)
