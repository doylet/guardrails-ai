#!/usr/bin/env python3
"""
Interactive Conflict Resolution System

Provides user-guided conflict resolution for plugin schema composition with
CLI prompting, resolution persistence, and integration with existing conflict
detection framework.

Phase 3 Task 3.1: Interactive Conflict Resolution
"""

import hashlib
import json
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import yaml

from .schema_composer import PluginConflict, MergeStrategy
from ..adapters.logging import get_logger


@dataclass
class ConflictResolution:
    """Structured representation of a conflict resolution."""
    
    strategy: str  # 'union', 'override', 'custom', 'skip'
    chosen_plugin: Optional[str] = None  # For override strategy
    custom_value: Optional[Any] = None   # For custom strategy
    resolved_value: Optional[Any] = None # Final resolved value
    apply_to_similar: bool = False       # Apply to similar conflicts
    resolved_at: str = ""                # ISO timestamp
    
    def __post_init__(self):
        if not self.resolved_at:
            self.resolved_at = datetime.now().isoformat()


class InteractiveConflictResolver:
    """Handles user-guided conflict resolution with persistence."""
    
    def __init__(self, config_path: Optional[Path] = None, interactive: bool = True):
        """
        Initialize the conflict resolver.
        
        Args:
            config_path: Path to plugin configuration file
            interactive: Whether to prompt user interactively
        """
        self.logger = get_logger(__name__)
        self.interactive = interactive and sys.stdin.isatty()
        self.config_path = config_path or Path(".ai/plugin_config.yaml")
        self.saved_resolutions: Dict[str, ConflictResolution] = {}
        self.session_resolutions: Dict[str, ConflictResolution] = {}
        self.global_preferences: Dict[str, str] = {}
        
        self._load_saved_resolutions()
    
    def resolve_conflict(self, conflict: PluginConflict, 
                        current_value: Any = None, 
                        new_value: Any = None) -> ConflictResolution:
        """
        Resolve a conflict either from saved resolution or user prompt.
        
        Args:
            conflict: The conflict to resolve
            current_value: Current value in target schema  
            new_value: New value from plugin being merged
            
        Returns:
            ConflictResolution with strategy and resolved value
        """
        # Generate conflict signature for persistence
        conflict_key = self._generate_conflict_key(conflict)
        
        # Check for saved resolution
        if conflict_key in self.saved_resolutions:
            resolution = self.saved_resolutions[conflict_key]
            self.logger.info(f"Using saved resolution for {conflict.path}: {resolution.strategy}")
            return resolution
        
        # Check global preferences for this conflict type
        if conflict.type in self.global_preferences:
            preference = self.global_preferences[conflict.type]
            if preference != "prompt":
                resolution = self._apply_preference_strategy(
                    preference, conflict, current_value, new_value
                )
                self.session_resolutions[conflict_key] = resolution
                return resolution
        
        # Interactive resolution required
        if self.interactive:
            resolution = self._prompt_user_resolution(conflict, current_value, new_value)
        else:
            # Non-interactive fallback
            self.logger.warning(f"Non-interactive mode: using union strategy for {conflict.path}")
            resolution = ConflictResolution(
                strategy="union",
                resolved_value=self._merge_values_union(current_value, new_value)
            )
        
        # Save resolution if requested
        if resolution.apply_to_similar:
            self.saved_resolutions[conflict_key] = resolution
            self._save_resolutions()
        else:
            self.session_resolutions[conflict_key] = resolution
        
        return resolution
    
    def _prompt_user_resolution(self, conflict: PluginConflict, 
                               current_value: Any, new_value: Any) -> ConflictResolution:
        """Present CLI prompt for user to resolve conflict."""
        
        print("\n" + "="*70)
        print("🔴 CONFLICT DETECTED: Plugin schema composition")
        print("="*70)
        print(f"Path: {conflict.path}")
        print(f"Type: {conflict.type}")
        print(f"Severity: {conflict.severity}")
        print(f"Message: {conflict.message}")
        print()
        
        # Show conflicting values
        if len(conflict.plugins) >= 2:
            print(f"Plugin: {conflict.plugins[0]}")
            print(f"Value: {self._format_value(current_value)}")
            print()
            print(f"Plugin: {conflict.plugins[1]}")
            print(f"Value: {self._format_value(new_value)}")
            print()
        
        # Show resolution options
        print("Resolution Options:")
        print(f"[1] Use {conflict.plugins[0]} value (override)")
        print(f"[2] Use {conflict.plugins[1]} value (override)")
        print("[3] Merge both values (union)")
        print("[4] Enter custom value")
        print("[5] Skip this path (exclude from schema)")
        print()
        print("[6] Apply this choice to all similar conflicts")
        print("[p] Set preference for this conflict type")
        print("[q] Quit and use non-interactive mode")
        print()
        
        while True:
            try:
                choice = input("Choice [1-6,p,q]: ").strip().lower()
                
                if choice == 'q':
                    print("Switching to non-interactive mode...")
                    self.interactive = False
                    return ConflictResolution(
                        strategy="union",
                        resolved_value=self._merge_values_union(current_value, new_value)
                    )
                
                elif choice == 'p':
                    self._set_global_preference(conflict.type)
                    continue
                
                elif choice == '1':
                    return ConflictResolution(
                        strategy="override",
                        chosen_plugin=conflict.plugins[0],
                        resolved_value=current_value
                    )
                
                elif choice == '2':
                    return ConflictResolution(
                        strategy="override", 
                        chosen_plugin=conflict.plugins[1],
                        resolved_value=new_value
                    )
                
                elif choice == '3':
                    merged_value = self._merge_values_union(current_value, new_value)
                    print(f"✓ Merged value: {self._format_value(merged_value)}")
                    return ConflictResolution(
                        strategy="union",
                        resolved_value=merged_value
                    )
                
                elif choice == '4':
                    custom_value = self._prompt_custom_value(current_value, new_value)
                    return ConflictResolution(
                        strategy="custom",
                        custom_value=custom_value,
                        resolved_value=custom_value
                    )
                
                elif choice == '5':
                    print("✓ Path will be excluded from final schema")
                    return ConflictResolution(strategy="skip")
                
                elif choice == '6':
                    # Re-prompt for strategy, then set apply_to_similar
                    print("Select strategy to apply to similar conflicts:")
                    base_resolution = self._prompt_user_resolution(conflict, current_value, new_value)
                    base_resolution.apply_to_similar = True
                    print("✓ Resolution will be saved for similar conflicts")
                    return base_resolution
                
                else:
                    print("Invalid choice. Please select 1-6, p, or q.")
                    
            except (EOFError, KeyboardInterrupt):
                print("\nInterrupted. Using union strategy...")
                return ConflictResolution(
                    strategy="union",
                    resolved_value=self._merge_values_union(current_value, new_value)
                )
    
    def _prompt_custom_value(self, current_value: Any, new_value: Any) -> Any:
        """Prompt user for custom value with validation."""
        print("Enter custom value:")
        print(f"Current type: {type(current_value).__name__}")
        print(f"Example format: {self._format_value(current_value)}")
        
        while True:
            try:
                user_input = input("Custom value: ").strip()
                
                # Try to parse as same type as current value
                if isinstance(current_value, bool):
                    return user_input.lower() in ('true', '1', 'yes', 'on')
                elif isinstance(current_value, int):
                    return int(user_input)
                elif isinstance(current_value, float):
                    return float(user_input)
                elif isinstance(current_value, list):
                    # Parse as JSON array or comma-separated
                    if user_input.startswith('['):
                        return json.loads(user_input)
                    else:
                        return [item.strip() for item in user_input.split(',')]
                elif isinstance(current_value, dict):
                    return json.loads(user_input)
                else:
                    return user_input
                    
            except (ValueError, json.JSONDecodeError) as e:
                print(f"Invalid format: {e}. Please try again.")
    
    def _merge_values_union(self, current: Any, new: Any) -> Any:
        """Merge two values using union strategy."""
        if isinstance(current, list) and isinstance(new, list):
            # Union of lists, preserve order and remove duplicates
            result = current.copy()
            for item in new:
                if item not in result:
                    result.append(item)
            return result
        elif isinstance(current, dict) and isinstance(new, dict):
            # Deep merge dictionaries
            result = current.copy()
            for key, value in new.items():
                if key in result:
                    result[key] = self._merge_values_union(result[key], value)
                else:
                    result[key] = value
            return result
        elif isinstance(current, str) and isinstance(new, str):
            if current == new:
                return current
            else:
                return f"{current},{new}"
        elif isinstance(current, (int, float)) and isinstance(new, (int, float)):
            return max(current, new)
        elif isinstance(current, bool) and isinstance(new, bool):
            return current or new
        else:
            # Fallback: create list of both values
            return [current, new]
    
    def _set_global_preference(self, conflict_type: str) -> None:
        """Set global preference for a conflict type."""
        print(f"\nSet global preference for {conflict_type} conflicts:")
        print("[1] Always prompt (current)")
        print("[2] Always use union strategy")
        print("[3] Always use first plugin (override)")
        print("[4] Always use last plugin (override)")
        print("[5] Always skip")
        
        while True:
            choice = input("Preference [1-5]: ").strip()
            preferences = {
                '1': 'prompt',
                '2': 'union', 
                '3': 'override_first',
                '4': 'override_last',
                '5': 'skip'
            }
            
            if choice in preferences:
                self.global_preferences[conflict_type] = preferences[choice]
                print(f"✓ Set preference for {conflict_type}: {preferences[choice]}")
                self._save_resolutions()  # Save preferences immediately
                break
            else:
                print("Invalid choice. Please select 1-5.")
    
    def _apply_preference_strategy(self, preference: str, conflict: PluginConflict,
                                  current_value: Any, new_value: Any) -> ConflictResolution:
        """Apply a global preference strategy."""
        if preference == "union":
            return ConflictResolution(
                strategy="union",
                resolved_value=self._merge_values_union(current_value, new_value)
            )
        elif preference == "override_first":
            return ConflictResolution(
                strategy="override",
                chosen_plugin=conflict.plugins[0] if conflict.plugins else None,
                resolved_value=current_value
            )
        elif preference == "override_last":
            return ConflictResolution(
                strategy="override", 
                chosen_plugin=conflict.plugins[-1] if conflict.plugins else None,
                resolved_value=new_value
            )
        elif preference == "skip":
            return ConflictResolution(strategy="skip")
        else:
            # Fallback to union
            return ConflictResolution(
                strategy="union",
                resolved_value=self._merge_values_union(current_value, new_value)
            )
    
    def _generate_conflict_key(self, conflict: PluginConflict) -> str:
        """Generate unique key for conflict persistence."""
        # Create deterministic signature from conflict attributes
        signature_data = {
            'path': conflict.path,
            'type': conflict.type,
            'plugins': sorted(conflict.plugins) if conflict.plugins else []
        }
        signature_str = json.dumps(signature_data, sort_keys=True)
        return hashlib.md5(signature_str.encode()).hexdigest()[:16]
    
    def _format_value(self, value: Any) -> str:
        """Format value for display in CLI."""
        if isinstance(value, (list, dict)):
            return json.dumps(value, indent=2)
        elif isinstance(value, str) and len(value) > 100:
            return f"{value[:100]}..."
        else:
            return str(value)
    
    def _load_saved_resolutions(self) -> None:
        """Load saved resolutions from configuration file."""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    config = yaml.safe_load(f) or {}
                
                # Load saved resolutions
                resolutions_data = config.get('conflict_resolutions', {})
                for key, data in resolutions_data.items():
                    self.saved_resolutions[key] = ConflictResolution(**data)
                
                # Load global preferences
                self.global_preferences = config.get('global_resolution_preferences', {})
                
                self.logger.debug(f"Loaded {len(self.saved_resolutions)} saved resolutions")
                
        except Exception as e:
            self.logger.warning(f"Failed to load saved resolutions: {e}")
            self.saved_resolutions = {}
            self.global_preferences = {}
    
    def _save_resolutions(self) -> None:
        """Save resolutions to configuration file."""
        try:
            # Load existing config or create new
            config = {}
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    config = yaml.safe_load(f) or {}
            
            # Update conflict resolutions
            config['conflict_resolutions'] = {
                key: asdict(resolution) 
                for key, resolution in self.saved_resolutions.items()
            }
            
            # Update global preferences
            config['global_resolution_preferences'] = self.global_preferences
            
            # Ensure directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save atomically
            temp_path = self.config_path.with_suffix('.tmp')
            with open(temp_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, indent=2)
            temp_path.replace(self.config_path)
            
            self.logger.debug(f"Saved {len(self.saved_resolutions)} resolutions to {self.config_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to save resolutions: {e}")
    
    def get_resolution_summary(self) -> Dict[str, Any]:
        """Get summary of resolutions for this session."""
        return {
            'saved_resolutions': len(self.saved_resolutions),
            'session_resolutions': len(self.session_resolutions),
            'global_preferences': self.global_preferences.copy(),
            'interactive_mode': self.interactive
        }
