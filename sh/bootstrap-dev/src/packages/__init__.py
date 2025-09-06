"""
Infrastructure package for AI Guardrails Bootstrap

This package provides modular infrastructure management for AI guardrails
installation, configuration, and diagnostics.

Public API:
    InfrastructureBootstrap: Main orchestrator class
    Colors: Terminal color utilities

Internal modules:
    - core: Main orchestration classes
    - managers: Component, config, state, and plugin management
    - operations: YAML operations and diagnostics
    - presentation: UI and formatting classes
    - utils: Common utilities and helpers
    - scripts: Automation and utility scripts
"""

# Main public API
from .core import InfrastructureBootstrap

# Commonly used utilities
from .utils import Colors

# Manager classes (for advanced usage)
from .managers import ComponentManager, ConfigManager, StateManager, PluginSystem

# Operations (for advanced usage)
from .operations import Doctor, YAMLOperations

# Presentation layer (for custom formatting)
from .presentation import StatePresenter, ComponentPresenter, ProfilePresenter

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
