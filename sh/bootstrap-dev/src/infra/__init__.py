"""
Infrastructure package for AI Guardrails Bootstrap

This package provides modular infrastructure management for AI guardrails
installation, configuration, and diagnostics.

Public API:
    InfrastructureBootstrap: Main orchestrator class
    Colors: Terminal color utilities  
    
Internal modules:
    - managers: Component, config, state, and plugin management
    - operations: YAML operations and diagnostics
    - utils: Common utilities and helpers
"""

# Main public API
from .bootstrap import InfrastructureBootstrap

# Commonly used utilities
from .utils import Colors

# Manager classes (for advanced usage)
from .component_manager import ComponentManager
from .config_manager import ConfigManager  
from .state_manager import StateManager
from .plugin_system import PluginSystem
from .doctor import Doctor

# Operations (for advanced usage)
from .yaml_operations import YAMLOperations

# Presentation layer (for custom formatting)
from .presenters import StatePresenter, ComponentPresenter, ProfilePresenter

__all__ = [
    # Primary public API
    'InfrastructureBootstrap',
    'Colors',
    
    # Manager classes (advanced)
    'ComponentManager',
    'ConfigManager', 
    'StateManager',
    'PluginSystem',
    'Doctor',
    
    # Operations (advanced)
    'YAMLOperations',
    
    # Presentation (advanced)
    'StatePresenter',
    'ComponentPresenter', 
    'ProfilePresenter',
]

# Version info
__version__ = '1.0.0'
