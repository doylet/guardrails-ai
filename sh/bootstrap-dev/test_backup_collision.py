#!/usr/bin/env python3
"""
Test backup collision handling in AI Guardrails Bootstrap system
"""
import tempfile
import shutil
from pathlib import Path
from src.packages.adapters.fs import staging


def test_backup_collision_scenario():
    """Test what happens when backup directory already exists"""
    print("🔧 Testing Backup Collision Scenario...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Setup: create existing backup directory structure like community_research
        backup_dir = temp_path / ".backup-core"
        backup_dir.mkdir()
        
        # Create some existing content in backup (like app directory)
        app_backup = backup_dir / "app"
        app_backup.mkdir()
        (app_backup / "existing_file.py").write_text("# existing backup content")
        
        # Create current project content to backup
        app_current = temp_path / "app"
        app_current.mkdir()
        (app_current / "current_file.py").write_text("# current content")
        
        print(f"📁 Setup complete in: {temp_path}")
        print(f"   Existing backup: {backup_dir} with {list(backup_dir.rglob('*'))}")
        print(f"   Current content: {app_current} with {list(app_current.rglob('*'))}")
        
        # Test the transaction context that fails
        try:
            with staging("core", temp_path) as staging_dir:
                # Create some staged content
                staged_app = staging_dir / "app"
                staged_app.mkdir()
                (staged_app / "staged_file.py").write_text("# new content")
                print("   ✓ Staging successful")
            
            print("   ✓ Transaction completed successfully")
            
        except Exception as e:
            print(f"   ✗ Transaction failed: {e}")
            print(f"   Error type: {type(e)}")
            
            # Check what directories exist after failure
            print(f"   Post-failure state:")
            for item in temp_path.iterdir():
                print(f"     - {item.name}: {item.is_dir()}")


if __name__ == '__main__':
    test_backup_collision_scenario()
