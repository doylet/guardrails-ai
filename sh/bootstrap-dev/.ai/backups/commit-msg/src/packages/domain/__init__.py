"""Domain models and business logic for the AI Guardrails Bootstrap System.

This package contains pure domain models, typed exceptions, and business rules
that are free from infrastructure concerns and side effects.
"""

from .model import (
    ActionKind,
    Reason,
    FileAction,
    ComponentPlan,
    InstallPlan,
)
from .errors import (
    BootstrapError,
    ConflictError,
    DepError,
    DriftError,
)
from .constants import (
    GUARDRAILS_DIR,
    DEFAULT_PROFILE,
    DEFAULT_FILE_MODE,
    RECEIPT_DIR,
    MANIFEST_FILENAME,
)

__all__ = [
    # Models
    "ActionKind",
    "Reason",
    "FileAction",
    "ComponentPlan",
    "InstallPlan",
    # Errors
    "BootstrapError",
    "ConflictError",
    "DepError",
    "DriftError",
    # Constants
    "GUARDRAILS_DIR",
    "DEFAULT_PROFILE",
    "DEFAULT_FILE_MODE",
    "RECEIPT_DIR",
    "MANIFEST_FILENAME",
]
