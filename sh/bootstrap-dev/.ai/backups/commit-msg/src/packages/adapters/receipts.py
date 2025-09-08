"""Receipt management for idempotency tracking and state validation.

This module manages installation receipts that track what component                f"Fail        try:
            atomic_write(receipt_json, receipt_path)
            # Create adapter Receipt for cache
            adapter_receipt = Receipt.from_dict(receipt_data)
            self._receipt_cache[receipt.component_id] = adapter_receipt
            logger.debug(f"Wrote receipt for component: {receipt.component_id}")

        except Exception as e:
            raise TransactionError(
                f"Failed to write receipt for {receipt.component_id}: {e}",
                component="receipts",
                operation="write_receipt"
            )te receipt for {receipt.component_id}: {e}",
                receipt.component_id,have been
installed, their file hashes, and metadata needed for drift detection and
idempotent operations.
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Set

from ..domain.constants import (
    GUARDRAILS_DIR,
    RECEIPT_DIR,
    RECEIPT_VERSION,
)
from ..domain.errors import TransactionError
from ..adapters.hashing import sha256_file
from ..adapters.fs import safe_mkdir, atomic_write
from ..adapters.logging import get_logger

logger = get_logger(__name__)


class Receipt:
    """Represents an installation receipt for a component."""

    def __init__(
        self,
        component_name: str,
        plugin_id: Optional[str] = None,
        manifest_digest: str = "",
        installed_at: Optional[float] = None,
        version: str = RECEIPT_VERSION,
    ):
        self.component_name = component_name
        self.plugin_id = plugin_id
        self.manifest_digest = manifest_digest
        self.installed_at = installed_at or time.time()
        self.version = version
        self.files: Dict[str, Dict] = {}  # path -> file metadata

    def add_file(
        self,
        relative_path: str,
        file_hash: str,
        file_size: int,
        file_mode: int,
        action_taken: str,
    ) -> None:
        """Add file metadata to receipt."""
        self.files[relative_path] = {
            "hash": file_hash,
            "size": file_size,
            "mode": file_mode,
            "action": action_taken,
            "installed_at": time.time(),
        }

    def to_dict(self) -> Dict:
        """Convert receipt to dictionary for serialization."""
        return {
            "version": self.version,
            "component_name": self.component_name,
            "plugin_id": self.plugin_id,
            "manifest_digest": self.manifest_digest,
            "installed_at": self.installed_at,
            "files": self.files,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Receipt":
        """Create receipt from dictionary."""
        # Handle both old and new receipt formats
        component_name = data.get("component_name") or data.get("component_id")
        if not component_name:
            raise ValueError("Receipt missing component_name/component_id")
            
        receipt = cls(
            component_name=component_name,
            plugin_id=data.get("plugin_id"),
            manifest_digest=data.get("manifest_digest", ""),
            installed_at=data.get("installed_at"),
            version=data.get("version", RECEIPT_VERSION),
        )
        receipt.files = data.get("files", {})
        return receipt

    def get_file_hash(self, relative_path: str) -> Optional[str]:
        """Get expected hash for a file."""
        file_data = self.files.get(relative_path)
        return file_data.get("hash") if file_data else None

    def has_file(self, relative_path: str) -> bool:
        """Check if receipt tracks a file."""
        return relative_path in self.files

    def get_file_paths(self) -> Set[str]:
        """Get all file paths tracked by this receipt."""
        return set(self.files.keys())


class ReceiptsAdapter:
    """Manages component installation receipts for idempotency."""

    def __init__(self, target_dir: Path):
        """Initialize receipts adapter.

        Args:
            target_dir: Target directory containing receipts
        """
        self.target_dir = Path(target_dir)
        self.receipts_dir = self.target_dir / GUARDRAILS_DIR / RECEIPT_DIR
        self._receipt_cache: Dict[str, Receipt] = {}

    def ensure_receipts_dir(self) -> None:
        """Ensure receipts directory exists."""
        safe_mkdir(self.receipts_dir, create_sentinel=True)

    def write_receipt(self, receipt: Receipt) -> None:
        """Write component receipt to disk.

        Args:
            receipt: Receipt to write

        Raises:
            TransactionError: If receipt cannot be written
        """
        self.ensure_receipts_dir()

        receipt_path = self.receipts_dir / f"{receipt.component_id}.json"
        
        # Convert domain Receipt to adapter format
        if hasattr(receipt, 'to_dict') and callable(receipt.to_dict):
            # Domain Receipt - convert to adapter format
            receipt_data = {
                "component_name": receipt.component_id,  # Map component_id to component_name
                "installed_at": receipt.installed_at,
                "manifest_digest": receipt.manifest_hash,
                "plugin_id": getattr(receipt, 'plugin_id', None),
                "version": RECEIPT_VERSION,
                "files": {}
            }
            # Convert FileAction list to dict format
            if hasattr(receipt, 'files') and receipt.files:
                for action in receipt.files:
                    receipt_data["files"][str(action.target_path)] = {
                        "hash": action.target_hash,
                        "action": action.action_type,
                        "source": str(action.source_path)
                    }
        else:
            # Adapter Receipt - use as is
            receipt_data = receipt.to_dict()
            
        receipt_json = json.dumps(receipt_data, indent=2, sort_keys=True)

        try:
            atomic_write(receipt_json, receipt_path)
            self._receipt_cache[receipt.component_id] = receipt
            logger.debug(f"Wrote receipt for component: {receipt.component_id}")

        except Exception as e:
            raise TransactionError(
                f"Failed to write receipt for {receipt.component_name}: {e}",
                receipt.component_name,
                "write_receipt",
            ) from e

    def read_receipt(self, component_name: str) -> Optional[Receipt]:
        """Read component receipt from disk.

        Args:
            component_name: Name of component

        Returns:
            Receipt if exists, None otherwise
        """
        # Check cache first
        if component_name in self._receipt_cache:
            return self._receipt_cache[component_name]

        receipt_path = self.receipts_dir / f"{component_name}.json"

        if not receipt_path.exists():
            return None

        try:
            with receipt_path.open() as f:
                receipt_data = json.load(f)

            receipt = Receipt.from_dict(receipt_data)
            self._receipt_cache[component_name] = receipt
            return receipt

        except Exception as e:
            logger.warning(f"Failed to read receipt for {component_name}: {e}")
            return None

    def delete_receipt(self, component_name: str) -> None:
        """Delete component receipt.

        Args:
            component_name: Name of component
        """
        receipt_path = self.receipts_dir / f"{component_name}.json"

        try:
            if receipt_path.exists():
                receipt_path.unlink()

            # Remove from cache
            self._receipt_cache.pop(component_name, None)
            logger.debug(f"Deleted receipt for component: {component_name}")

        except Exception as e:
            logger.warning(f"Failed to delete receipt for {component_name}: {e}")

    def remove_receipt(self, component_name: str) -> None:
        """Remove component receipt (alias for delete_receipt).

        Args:
            component_name: Name of component
        """
        self.delete_receipt(component_name)

    def list_installed_components(self) -> List[str]:
        """List all components with receipts.

        Returns:
            List of component names
        """
        if not self.receipts_dir.exists():
            return []

        components = []

        try:
            for receipt_file in self.receipts_dir.glob("*.json"):
                component_name = receipt_file.stem
                components.append(component_name)

        except Exception as e:
            logger.warning(f"Failed to list installed components: {e}")

        return sorted(components)

    def is_current(self, component_name: str, relative_path: str = None) -> bool:
        """Check if component or specific file is current.

        Args:
            component_name: Name of component
            relative_path: Optional specific file path to check

        Returns:
            True if current, False otherwise
        """
        receipt = self.read_receipt(component_name)
        if not receipt:
            return False

        if relative_path:
            # Check specific file
            return self._is_file_current(receipt, relative_path)
        else:
            # Check all files in component
            for file_path in receipt.get_file_paths():
                if not self._is_file_current(receipt, file_path):
                    return False
            return True

    def _is_file_current(self, receipt: Receipt, relative_path: str) -> bool:
        """Check if a specific file is current."""
        if not receipt.has_file(relative_path):
            return False

        target_path = self.target_dir / relative_path
        if not target_path.exists():
            return False

        try:
            expected_hash = receipt.get_file_hash(relative_path)
            actual_hash = sha256_file(target_path)
            return expected_hash == actual_hash

        except Exception as e:
            logger.debug(f"Failed to check file currency for {relative_path}: {e}")
            return False

    def get_expected_hash(self, component_name: str, relative_path: str) -> Optional[str]:
        """Get expected hash for a file.

        Args:
            component_name: Name of component
            relative_path: Relative path to file

        Returns:
            Expected hash if known, None otherwise
        """
        receipt = self.read_receipt(component_name)
        if not receipt:
            return None

        return receipt.get_file_hash(relative_path)

    def detect_drift(self, component_name: str = None) -> Dict[str, List[str]]:
        """Detect configuration drift in installed components.

        Args:
            component_name: Optional specific component to check

        Returns:
            Dict mapping component names to lists of drifted files
        """
        drift_results = {}

        if component_name:
            components = [component_name]
        else:
            components = self.list_installed_components()

        for comp_name in components:
            drifted_files = []
            receipt = self.read_receipt(comp_name)

            if not receipt:
                continue

            for file_path in receipt.get_file_paths():
                if not self._is_file_current(receipt, file_path):
                    drifted_files.append(file_path)

            if drifted_files:
                drift_results[comp_name] = drifted_files

        return drift_results

    def validate_installation(self, component_name: str) -> List[str]:
        """Validate installation integrity for a component.

        Args:
            component_name: Name of component to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        receipt = self.read_receipt(component_name)

        if not receipt:
            errors.append(f"No receipt found for component: {component_name}")
            return errors

        # Check each tracked file
        for file_path in receipt.get_file_paths():
            target_path = self.target_dir / file_path

            if not target_path.exists():
                errors.append(f"Missing file: {file_path}")
                continue

            # Validate hash
            try:
                expected_hash = receipt.get_file_hash(file_path)
                actual_hash = sha256_file(target_path)

                if expected_hash != actual_hash:
                    errors.append(f"Hash mismatch for {file_path}")

            except Exception as e:
                errors.append(f"Cannot validate {file_path}: {e}")

        return errors

    def get_component_info(self, component_name: str) -> Optional[Dict]:
        """Get detailed information about an installed component.

        Args:
            component_name: Name of component

        Returns:
            Component information dict or None
        """
        receipt = self.read_receipt(component_name)
        if not receipt:
            return None

        file_count = len(receipt.files)
        total_size = sum(f.get("size", 0) for f in receipt.files.values())

        return {
            "name": receipt.component_id,  # Legacy format uses "name" 
            "plugin_id": receipt.plugin_id,
            "manifest_digest": receipt.manifest_digest,
            "installed_at": receipt.installed_at,
            "file_count": file_count,
            "total_size": total_size,
            "files": list(receipt.get_file_paths()),
        }

    def cleanup_orphaned_receipts(self, valid_components: Set[str]) -> List[str]:
        """Remove receipts for components that are no longer valid.

        Args:
            valid_components: Set of component names that should exist

        Returns:
            List of removed component names
        """
        installed = set(self.list_installed_components())
        orphaned = installed - valid_components

        removed = []
        for component_name in orphaned:
            self.delete_receipt(component_name)
            removed.append(component_name)

        if removed:
            logger.info(f"Cleaned up {len(removed)} orphaned receipts: {removed}")

        return removed
