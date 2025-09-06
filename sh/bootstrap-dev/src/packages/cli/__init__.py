"""Command-line interface for the AI Guardrails Bootstrap System.

This package provides the main entry point and argument parsing for the
bootstrap system, coordinating between the resolver, planner, and installer
components to provide a cohesive user experience.
"""

from .main import main
from .args import parse_args, BootstrapArgs

__all__ = [
    "main",
    "parse_args",
    "BootstrapArgs",
]
