"""
Manager modules for AI Guardrails Bootstrap

Contains specialized managers for different aspects of the system:
- ComponentManager: Handles component discovery and installation
- ConfigManager: Manages configuration files and settings
- StateManager: Tracks installation state and history
- PluginSystem: Manages plugin discovery and integration
"""

from .component_manager import ComponentManager
from .config_manager import ConfigManager
from .state_manager import StateManager
from .plugin_system import PluginSystem

__all__ = [
    'ComponentManager',
    'ConfigManager',
    'StateManager',
    'PluginSystem'
]
