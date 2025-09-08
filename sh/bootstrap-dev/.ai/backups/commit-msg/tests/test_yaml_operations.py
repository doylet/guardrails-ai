#!/usr/bin/env python3
"""
Test for YAML Operations Module
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from infra.yaml_operations import YAMLOperations


def test_deep_merge():
    """Test deep merge functionality"""
    target = {
        'repos': [
            {
                'repo': 'https://github.com/pre-commit/pre-commit-hooks',
                'hooks': [{'id': 'trailing-whitespace'}]
            }
        ]
    }

    source = {
        'repos': [
            {
                'repo': 'https://github.com/pre-commit/pre-commit-hooks',
                'hooks': [{'id': 'end-of-file-fixer'}]
            }
        ]
    }

    result = YAMLOperations.deep_merge_dict(target, source)

    # Should have both hooks
    assert len(result['repos']) == 1
    assert len(result['repos'][0]['hooks']) == 2

    print("✅ Deep merge test passed")


def test_clean_yaml_nulls():
    """Test YAML null cleaning"""
    data = {
        'precommit': {
            'disabled_hooks': None,
            'disabled_languages': None
        }
    }

    YAMLOperations.clean_yaml_nulls(data)

    assert data['precommit']['disabled_hooks'] == []
    assert data['precommit']['disabled_languages'] == []

    print("✅ YAML null cleaning test passed")


if __name__ == "__main__":
    print("Testing YAML Operations...")
    test_deep_merge()
    test_clean_yaml_nulls()
    print("All tests passed! ✅")
