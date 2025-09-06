"""Core data structures for the AI Guardrails Bootstrap System.

This module defines the primary domain models that represent installation plans,
file actions, and component metadata. All models are immutable dataclasses that
contain no business logic, making them easy to test and reason about.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Sequence, Optional


# Type aliases for better readability and type safety
ActionKind = Literal["COPY", "MERGE", "TEMPLATE", "SKIP"]
Reason = Literal["new", "hash-diff", "unchanged", "drift"]


@dataclass(frozen=True)
class FileAction:
    """Represents a single file operation to be performed during installation.

    Attributes:
        kind: The type of action to perform (COPY/MERGE/TEMPLATE/SKIP)
        src: Source file path (relative to plugin/template directory)
        dst: Destination file path (relative to target directory)
        mode: File permissions (octal), None to preserve existing or use default
        reason: Why this action is needed (new/hash-diff/unchanged/drift)
    """
    kind: ActionKind
    src: Path
    dst: Path
    mode: Optional[int]
    reason: Reason

    def __post_init__(self) -> None:
        """Validate file paths are relative and normalized."""
        if self.src.is_absolute():
            raise ValueError(f"Source path must be relative: {self.src}")
        if self.dst.is_absolute():
            raise ValueError(f"Destination path must be relative: {self.dst}")


@dataclass(frozen=True)
class ComponentPlan:
    """Represents the installation plan for a single component.

    Attributes:
        name: Component identifier (unique within a profile)
        actions: Sequence of file actions to perform
        manifest_digest: SHA256 hash of the component's manifest file
        plugin_id: Plugin that provides this component (None for built-in)
    """
    name: str
    actions: Sequence[FileAction]
    manifest_digest: str
    plugin_id: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate component name and manifest digest format."""
        if not self.name or not self.name.replace("-", "").replace("_", "").isalnum():
            raise ValueError(f"Invalid component name: {self.name}")
        if len(self.manifest_digest) != 64:  # SHA256 hex length
            raise ValueError(f"Invalid manifest digest format: {self.manifest_digest}")

    @property
    def total_files(self) -> int:
        """Total number of file actions in this component."""
        return len(self.actions)

    @property
    def actionable_files(self) -> int:
        """Number of file actions that will modify the filesystem."""
        return len([a for a in self.actions if a.kind != "SKIP"])


@dataclass(frozen=True)
class InstallPlan:
    """Complete installation plan for a target directory.

    Attributes:
        components: Sequence of component plans in dependency order
        total_files: Total file operations across all components
        estimated_size: Estimated disk space needed (bytes)
    """
    components: Sequence[ComponentPlan]
    total_files: int
    estimated_size: int

    def __post_init__(self) -> None:
        """Validate plan consistency."""
        calculated_files = sum(c.total_files for c in self.components)
        if self.total_files != calculated_files:
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
            if component.name == name:
                return component
        return None

    def has_conflicts(self) -> bool:
        """Check if any components have overlapping destination paths."""
        seen_paths: set[Path] = set()
        for component in self.components:
            for action in component.actions:
                if action.kind != "SKIP":
                    if action.dst in seen_paths:
                        return True
                    seen_paths.add(action.dst)
        return False
