"""Core data structures for the AI Guardrails Bootstrap System.

This module defines the primary domain models that represent installation plans,
file actions, component metadata, and installation receipts. All models are
immutable dataclasses that contain no business logic, making them easy to test
and reason about.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Sequence, Optional, Dict, Any
from datetime import datetime


# Type aliases for better readability and type safety
ActionKind = Literal["COPY", "MERGE", "TEMPLATE", "SKIP"]
Reason = Literal["new", "hash-diff", "unchanged", "drift"]


@dataclass(frozen=True)
class FileAction:
    """Represents a single file operation to be performed during installation.

    Attributes:
        action_type: The type of action to perform (COPY/MERGE/TEMPLATE/SKIP)
        source_path: Source file path (relative to plugin/template directory)
        target_path: Destination file path (relative to target directory)
        target_hash: Expected SHA256 hash of target file after installation
        mode: File permissions (octal), None to preserve existing or use default
        reason: Why this action is needed (new/hash-diff/unchanged/drift)
        metadata: Additional action-specific data
    """
    action_type: ActionKind
    source_path: Path
    target_path: Path
    target_hash: Optional[str] = None
    mode: Optional[int] = None
    reason: Reason = "new"
    metadata: Optional[Dict[str, Any]] = None

    # Legacy aliases for backward compatibility
    @property
    def kind(self) -> ActionKind:
        """Backward compatibility alias for action_type."""
        return self.action_type

    @property
    def src(self) -> Path:
        """Backward compatibility alias for source_path."""
        return self.source_path

    @property
    def dst(self) -> Path:
        """Backward compatibility alias for target_path."""
        return self.target_path

    def __post_init__(self) -> None:
        """Validate file paths are relative and normalized."""
        if self.source_path.is_absolute():
            raise ValueError(f"Source path must be relative: {self.source_path}")
        if self.target_path.is_absolute():
            raise ValueError(f"Target path must be relative: {self.target_path}")

        # Initialize metadata if None
        if self.metadata is None:
            object.__setattr__(self, 'metadata', {})


@dataclass(frozen=True)
class ComponentPlan:
    """Represents the installation plan for a single component.

    Attributes:
        component_id: Component identifier (unique within a profile)
        file_actions: Sequence of file actions to perform
        manifest_hash: SHA256 hash of the component's manifest file
        plugin_id: Plugin that provides this component (None for built-in)
    """
    component_id: str
    file_actions: Sequence[FileAction]
    manifest_hash: str
    plugin_id: Optional[str] = None

    # Legacy aliases for backward compatibility
    @property
    def name(self) -> str:
        """Backward compatibility alias for component_id."""
        return self.component_id

    @property
    def actions(self) -> Sequence[FileAction]:
        """Backward compatibility alias for file_actions."""
        return self.file_actions

    @property
    def manifest_digest(self) -> str:
        """Backward compatibility alias for manifest_hash."""
        return self.manifest_hash

    def __post_init__(self) -> None:
        """Validate component name and manifest digest format."""
        if not self.component_id or not self.component_id.replace("-", "").replace("_", "").isalnum():
            raise ValueError(f"Invalid component name: {self.component_id}")
        if len(self.manifest_hash) != 64:  # SHA256 hex length
            raise ValueError(f"Invalid manifest digest format: {self.manifest_hash}")

    @property
    def total_files(self) -> int:
        """Total number of file actions in this component."""
        return len(self.file_actions)

    @property
    def actionable_files(self) -> int:
        """Number of file actions that will modify the filesystem."""
        return len([a for a in self.file_actions if a.action_type != "SKIP"])


@dataclass(frozen=True)
class InstallPlan:
    """Complete installation plan for a target directory.

    Attributes:
        profile: Profile name this plan was generated for
        components: Sequence of component plans in dependency order
        total_files: Total file operations across all components
        estimated_size: Estimated disk space needed (bytes)
    """
    profile: str
    components: Sequence[ComponentPlan]
    total_files: int = 0
    estimated_size: int = 0

    def __post_init__(self) -> None:
        """Validate plan consistency and calculate totals."""
        calculated_files = sum(c.total_files for c in self.components)

        # Auto-calculate total_files if not provided
        if self.total_files == 0:
            object.__setattr__(self, 'total_files', calculated_files)
        elif self.total_files != calculated_files:
            raise ValueError(
                f"File count mismatch: declared={self.total_files}, "
                f"calculated={calculated_files}"
            )

    @property
    def component_count(self) -> int:
        """Number of components in this plan."""
        return len(self.components)

    @property
    def actionable_files(self) -> int:
        """Number of file actions that will modify the filesystem."""
        return sum(c.actionable_files for c in self.components)

    def get_component(self, name: str) -> Optional[ComponentPlan]:
        """Get component plan by name."""
        for component in self.components:
            if component.component_id == name:
                return component
        return None

    def has_conflicts(self) -> bool:
        """Check if any components have overlapping destination paths."""
        seen_paths: set[Path] = set()
        for component in self.components:
            for action in component.file_actions:
                if action.action_type != "SKIP":
                    if action.target_path in seen_paths:
                        return True
                    seen_paths.add(action.target_path)
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert plan to dictionary for serialization."""
        return {
            "profile": self.profile,
            "components": [
                {
                    "component_id": comp.component_id,
                    "plugin_id": comp.plugin_id,
                    "manifest_hash": comp.manifest_hash,
                    "file_actions": [
                        {
                            "action_type": action.action_type,
                            "source_path": str(action.source_path),
                            "target_path": str(action.target_path),
                            "target_hash": action.target_hash,
                            "reason": action.reason,
                            "metadata": action.metadata,
                        }
                        for action in comp.file_actions
                    ]
                }
                for comp in self.components
            ],
            "total_files": self.total_files,
            "estimated_size": self.estimated_size,
        }


@dataclass(frozen=True)
class Receipt:
    """Installation receipt for tracking component state and enabling idempotency.

    Attributes:
        component_id: Unique identifier for the installed component
        installed_at: Timestamp of installation (ISO format)
        manifest_hash: SHA256 hash of the component manifest at installation time
        files: List of file actions that were performed
        metadata: Additional installation metadata
    """
    component_id: str
    installed_at: str  # ISO timestamp
    manifest_hash: str
    files: Sequence[FileAction]
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self) -> None:
        """Validate receipt structure."""
        if not self.component_id:
            raise ValueError("Component ID cannot be empty")
        if len(self.manifest_hash) != 64:  # SHA256 hex length
            raise ValueError(f"Invalid manifest hash format: {self.manifest_hash}")

        # Initialize metadata if None
        if self.metadata is None:
            object.__setattr__(self, 'metadata', {})

    @classmethod
    def create(
        cls,
        component_id: str,
        manifest_hash: str,
        files: Sequence[FileAction],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "Receipt":
        """Create a new receipt with current timestamp.

        Args:
            component_id: Component identifier
            manifest_hash: SHA256 hash of component manifest
            files: File actions that were performed
            metadata: Additional metadata

        Returns:
            New Receipt instance
        """
        return cls(
            component_id=component_id,
            installed_at=datetime.now().isoformat(),
            manifest_hash=manifest_hash,
            files=files,
            metadata=metadata or {},
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert receipt to dictionary for serialization."""
        return {
            "component_id": self.component_id,
            "installed_at": self.installed_at,
            "manifest_hash": self.manifest_hash,
            "files": [
                {
                    "action_type": action.action_type,
                    "source_path": str(action.source_path),
                    "target_path": str(action.target_path),
                    "target_hash": action.target_hash,
                    "reason": action.reason,
                    "metadata": action.metadata,
                }
                for action in self.files
            ],
            "metadata": self.metadata,
        }
