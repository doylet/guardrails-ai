"""Atomic filesystem operations for safe component installation.

This module provides transaction-safe filesystem operations with staging,
backup, and rollback capabilities. All operations use sentinel files to
prevent accidental deletion of user data.
"""

import shutil
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional, Union

from ..domain.constants import (
    DEFAULT_DIR_MODE,
    DEFAULT_FILE_MODE,
    STAGING_PREFIX,
    BACKUP_PREFIX,
    SENTINEL_SUFFIX,
)
from ..domain.errors import TransactionError


def atomic_write(
    content: Union[str, bytes],
    target_path: Path,
    mode: Optional[int] = None,
    encoding: str = "utf-8",
) -> None:
    """Write content to a file atomically using staging and promotion.

    Args:
        content: Content to write (string or bytes)
        target_path: Final destination path
        mode: File permissions (octal), defaults to DEFAULT_FILE_MODE
        encoding: Text encoding for string content

    Raises:
        TransactionError: If atomic write operation fails
    """
    if mode is None:
        mode = DEFAULT_FILE_MODE

    target_path = Path(target_path).resolve()
    staging_path = target_path.with_suffix(target_path.suffix + ".staging")

    try:
        # Ensure parent directory exists
        target_path.parent.mkdir(parents=True, exist_ok=True)

        # Write to staging file
        if isinstance(content, str):
            staging_path.write_text(content, encoding=encoding)
        else:
            staging_path.write_bytes(content)

        # Set permissions
        staging_path.chmod(mode)

        # Atomic promotion (rename)
        staging_path.rename(target_path)

    except Exception as e:
        # Cleanup staging file if it exists
        if staging_path.exists():
            staging_path.unlink()
        raise TransactionError(
            f"Failed to atomically write {target_path}: {e}",
            component="fs",
            operation="atomic_write",
        ) from e


def safe_mkdir(
    path: Path,
    mode: Optional[int] = None,
    create_sentinel: bool = True,
) -> None:
    """Create directory with optional sentinel file for safe cleanup.

    Args:
        path: Directory path to create
        mode: Directory permissions (octal), defaults to DEFAULT_DIR_MODE
        create_sentinel: Whether to create sentinel file for cleanup protection

    Raises:
        TransactionError: If directory creation fails
    """
    if mode is None:
        mode = DEFAULT_DIR_MODE

    path = Path(path).resolve()

    try:
        path.mkdir(parents=True, exist_ok=True)
        path.chmod(mode)

        if create_sentinel:
            sentinel_path = path / f"{path.name}{SENTINEL_SUFFIX}"
            sentinel_path.write_text(f"Created by bootstrap system at {path}")

    except Exception as e:
        raise TransactionError(
            f"Failed to create directory {path}: {e}",
            component="fs",
            operation="safe_mkdir",
        ) from e


@contextmanager
def staging(component_name: str, target_dir: Path) -> Generator[Path, None, None]:
    """Context manager for component-level staging directory.

    Creates a temporary staging directory for atomic component installation.
    On successful completion, promotes staged files to target. On error,
    cleans up staging directory.

    Args:
        component_name: Component identifier for staging directory
        target_dir: Final target directory

    Yields:
        Path to staging directory

    Raises:
        TransactionError: If staging operations fail
    """
    target_dir = Path(target_dir).resolve()
    staging_dir = target_dir / f"{STAGING_PREFIX}-{component_name}"
    backup_dir = target_dir / f"{BACKUP_PREFIX}-{component_name}"

    try:
        # Create staging directory
        safe_mkdir(staging_dir, create_sentinel=True)

        yield staging_dir

        # Success: backup existing files and promote staged files
        if any(target_dir.iterdir()):
            safe_mkdir(backup_dir, create_sentinel=True)
            for item in target_dir.iterdir():
                if item.name.startswith((STAGING_PREFIX, BACKUP_PREFIX)):
                    continue
                backup_item = backup_dir / item.name
                if item.is_dir():
                    shutil.copytree(item, backup_item)
                else:
                    shutil.copy2(item, backup_item)

        # Promote staged files
        for item in staging_dir.iterdir():
            if item.name.endswith(SENTINEL_SUFFIX):
                continue
            target_item = target_dir / item.name
            if item.is_dir():
                shutil.copytree(item, target_item, dirs_exist_ok=True)
            else:
                shutil.copy2(item, target_item)

    except Exception as e:
        # Error: cleanup staging directory
        cleanup_staging(staging_dir)
        raise TransactionError(
            f"Staging failed for component {component_name}: {e}",
            component=component_name,
            operation="staging",
        ) from e
    finally:
        # Always cleanup staging directory
        cleanup_staging(staging_dir)


def cleanup_staging(staging_path: Path) -> None:
    """Safely remove staging directory with sentinel validation.

    Only removes directories that contain a sentinel file, preventing
    accidental deletion of user data.

    Args:
        staging_path: Path to staging directory
    """
    staging_path = Path(staging_path).resolve()

    if not staging_path.exists():
        return

    if not staging_path.is_dir():
        return

    # Check for sentinel file
    sentinel_files = list(staging_path.glob(f"*{SENTINEL_SUFFIX}"))
    if not sentinel_files:
        # No sentinel found - refuse to delete
        return

    try:
        shutil.rmtree(staging_path)
    except Exception:
        # Best effort cleanup - don't raise errors
        pass


def backup_file(file_path: Path, backup_dir: Path) -> Path:
    """Create a backup copy of a file before modification.

    Args:
        file_path: File to backup
        backup_dir: Directory to store backup

    Returns:
        Path to backup file

    Raises:
        TransactionError: If backup operation fails
    """
    file_path = Path(file_path).resolve()
    backup_dir = Path(backup_dir).resolve()

    if not file_path.exists():
        raise TransactionError(
            f"Cannot backup non-existent file: {file_path}",
            component="fs",
            operation="backup_file",
        )

    try:
        safe_mkdir(backup_dir, create_sentinel=True)
        backup_path = backup_dir / file_path.name
        shutil.copy2(file_path, backup_path)
        return backup_path

    except Exception as e:
        raise TransactionError(
            f"Failed to backup {file_path}: {e}",
            component="fs",
            operation="backup_file",
        ) from e


def restore_from_backup(backup_path: Path, target_path: Path) -> None:
    """Restore a file from backup.

    Args:
        backup_path: Path to backup file
        target_path: Destination for restored file

    Raises:
        TransactionError: If restore operation fails
    """
    backup_path = Path(backup_path).resolve()
    target_path = Path(target_path).resolve()

    if not backup_path.exists():
        raise TransactionError(
            f"Backup file not found: {backup_path}",
            component="fs",
            operation="restore_from_backup",
        )

    try:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(backup_path, target_path)

    except Exception as e:
        raise TransactionError(
            f"Failed to restore {backup_path} to {target_path}: {e}",
            component="fs",
            operation="restore_from_backup",
        ) from e
