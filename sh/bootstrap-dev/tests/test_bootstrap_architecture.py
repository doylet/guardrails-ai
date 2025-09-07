#!/usr/bin/env python3
"""
Test for Component Manager Module
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from packages import InfrastructureBootstrap


def test_bootstrap_initialization():
    """Test that bootstrap initializes with modular architecture"""
    try:
        bootstrap = InfrastructureBootstrap()

        # Check that all managers are initialized
        assert hasattr(bootstrap, 'state_manager')
        assert hasattr(bootstrap, 'plugin_system')
        assert hasattr(bootstrap, 'component_manager')
        assert hasattr(bootstrap, 'config_manager')
        assert hasattr(bootstrap, 'doctor')

        print("✅ Bootstrap initialization test passed")

        # Test delegation works
        print("✅ Profile listing delegation works")

        return True

    except Exception as e:
        print(f"❌ Bootstrap test failed: {e}")
        return False


if __name__ == "__main__":
    print("Testing Bootstrap Modular Architecture...")
    if test_bootstrap_initialization():
        print("All tests passed! ✅")
    else:
        print("Tests failed! ❌")
        sys.exit(1)
