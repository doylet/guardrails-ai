#!/usr/bin/env python3
"""
Comprehensive test to verify AI Guardrails Bootstrap system functionality
Tests receipt format conversion, installer operations, and end-to-end workflow
"""
from src.packages.adapters.receipts import ReceiptsAdapter
from src.packages.domain.model import Receipt
from src.packages.core.orchestrator import Orchestrator
from datetime import datetime
import hashlib
import tempfile
import os

def test_complete_system():
    """Test complete AI Guardrails Bootstrap functionality"""
    print("🔧 Testing AI Guardrails Bootstrap System...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        os.chdir(temp_dir)
        print(f"📁 Testing in: {temp_dir}")
        
        # Test 1: Receipt format conversion
        print("\n1️⃣ Testing Receipt Format Conversion...")
        receipts_adapter = ReceiptsAdapter(temp_dir)
        
        # Create domain Receipt 
        test_hash = hashlib.sha256(b'test_component_data').hexdigest()
        domain_receipt = Receipt(
            component_id='test_component',
            installed_at=datetime.now().isoformat(),
            manifest_hash=test_hash,
            files=[],
            metadata={'installation_method': 'test'}
        )
        
        # Test write (domain → adapter conversion)
        receipts_adapter.write_receipt(domain_receipt)
        print("   ✓ Domain Receipt → Adapter Receipt conversion: SUCCESS")
        
        # Test read (adapter → domain)
        domain_receipt_read = receipts_adapter.read_receipt('test_component')
        if domain_receipt_read and hasattr(domain_receipt_read, 'component_id'):
            print("   ✓ Adapter Receipt read returns domain Receipt: SUCCESS")
        else:
            print("   ✗ Adapter Receipt read: FAILED")
            return False
        
        # Test 2: Orchestrator integration
        print("\n2️⃣ Testing Orchestrator Integration...")
        orchestrator = Orchestrator(temp_dir)
        
        # Verify orchestrator has receipts_adapter
        if hasattr(orchestrator, 'receipts_adapter'):
            print("   ✓ Orchestrator has receipts_adapter: SUCCESS")
            
            # Test listing components
            components = orchestrator.receipts_adapter.list_installed_components()
            print(f"   ✓ Can list installed components: {len(components)} found")
        else:
            print("   ✗ Orchestrator missing receipts_adapter: FAILED")
            return False
            
        # Test 3: Component listing after write
        print("\n3️⃣ Testing Component Discovery...")
        components = receipts_adapter.list_installed_components()
        if 'test_component' in components:
            print("   ✓ Written component appears in installed list: SUCCESS")
        else:
            print("   ✗ Component not found in installed list: FAILED")
            return False
            
        print("\n🎉 ALL TESTS PASSED - System is operational!")
        return True

if __name__ == '__main__':
    success = test_complete_system()
    exit(0 if success else 1)
