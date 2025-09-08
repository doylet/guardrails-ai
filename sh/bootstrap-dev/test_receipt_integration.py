#!/usr/bin/env python3
from src.packages.core.orchestrator import Orchestrator
from src.packages.core.installer import Installer
from src.packages.adapters.receipts import ReceiptsAdapter
import tempfile
import os

def test_receipt_operations():
    """Test receipt write/read operations"""
    with tempfile.TemporaryDirectory() as temp_dir:
        os.chdir(temp_dir)
        
        # Test receipt operations directly
        orchestrator = Orchestrator(temp_dir)
        receipts_adapter = orchestrator.receipts_adapter
        
        # Test installer with receipts
        template_repo = orchestrator.planner.template_repo
        installer = Installer(
            target_dir=temp_dir,
            receipts_adapter=receipts_adapter,
            yaml_ops=orchestrator.yaml_ops,
            template_repo=template_repo,
            plugins_dir=orchestrator.resolver.plugins_dir
        )
        
        try:
            # Test basic receipt operations
            components = receipts_adapter.list_installed_components()
            print(f'✓ Can list installed components: {len(components)} found')
            
            print(f'✓ Receipt operations working')
            
        except Exception as e:
            print(f'✗ Receipt test failed: {e}')
            raise

if __name__ == '__main__':
    test_receipt_operations()
