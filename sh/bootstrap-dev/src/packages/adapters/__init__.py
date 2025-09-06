"""Infrastructure adapters for the AI Guardrails Bootstrap System.

This package contains all infrastructure concerns including filesystem operations,
hashing, logging, and external system integrations. These adapters isolate
domain logic from implementation details.
"""

from .fs import (
    atomic_write,
    safe_mkdir,
    staging,
    cleanup_staging,
)
from .hashing import (
    sha256_file,
    sha256_content,
    verify_hash,
)
from .logging import (
    get_logger,
    configure_logging,
)
from .receipts import (
    Receipt,
    ReceiptsAdapter,
)
from .yaml_ops import (
    YamlOpsAdapter,
)

__all__ = [
    # Filesystem operations
    "atomic_write",
    "safe_mkdir",
    "staging",
    "cleanup_staging",
    # Hashing utilities
    "sha256_file",
    "sha256_content",
    "verify_hash",
    # Logging
    "get_logger",
    "configure_logging",
    # Receipts
    "Receipt",
    "ReceiptsAdapter",
    # YAML operations
    "YamlOpsAdapter",
]
