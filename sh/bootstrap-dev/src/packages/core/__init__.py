"""
Core orchestration module for AI Guardrails Bootstrap

Contains the main orchestration components for the new architecture:
- Orchestrator: Main coordination layer
- Resolver: Dependency resolution and manifest loading
- Planner: Pure planning logic with deterministic file actions
- Installer: Transaction-safe installation engine
- Doctor: State validation and repair system
"""

from .bootstrap import InfrastructureBootstrap  # Legacy support
from .orchestrator import Orchestrator
from .resolver import Resolver, ResolvedSpec
from .planner import Planner
from .installer import Installer
from .doctor import Doctor, DoctorDiagnostic

__all__ = [
    # New architecture
    'Orchestrator',
    'Resolver',
    'ResolvedSpec',
    'Planner',
    'Installer',
    'Doctor',
    'DoctorDiagnostic',
    # Legacy support
    'InfrastructureBootstrap',
]
