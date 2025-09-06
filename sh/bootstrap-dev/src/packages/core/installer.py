"""Safe installation engine with transaction safety.

This module implements the staging/backup/promote pattern for atomic component
installation. Each component is installed as an isolated transaction with
automatic rollback on failure.

Architecture:
- Takes InstallPlan from planner
- Executes each FileAction with transaction safety
- Uses staging/backup/promote for atomic operations
- Writes receipts for idempotency tracking
- Provides rollback on any failure
"""

from pathlib import Path
from typing import Dict, List
import shutil

from ..domain.model import InstallPlan, FileAction, Receipt
from ..domain.errors import InstallationError, TransactionError
from ..adapters.fs import staging, atomic_write, safe_mkdir
from ..adapters.receipts import ReceiptsAdapter
from ..adapters.yaml_ops import YamlOpsAdapter
from ..adapters.logging import get_logger


class Installer:
    """Safe installation engine with per-component transactions."""

    def __init__(
        self,
        target_dir: Path,
        receipts_adapter: ReceiptsAdapter,
        yaml_ops: YamlOpsAdapter,
    ):
        """Initialize installer with required adapters.

        Args:
            target_dir: Target directory for installation
            receipts_adapter: Adapter for receipt tracking
            yaml_ops: Adapter for YAML/JSON operations
        """
        self.target_dir = target_dir
        self.receipts_adapter = receipts_adapter
        self.yaml_ops = yaml_ops
        self.logger = get_logger(__name__)

    def install_plan(
        self,
        plan: InstallPlan,
        dry_run: bool = False,
        force: bool = False,
    ) -> Dict[str, bool]:
        """Install a complete plan with transaction safety.

        Args:
            plan: InstallPlan to execute
            dry_run: If True, simulate installation without changes
            force: If True, overwrite existing files

        Returns:
            Dict mapping component names to success status

        Raises:
            InstallationError: If installation fails
        """
        results = {}
        completed_components = []

        try:
            for component_plan in plan.components:
                component_name = component_plan.component_id

                if dry_run:
                    self.logger.info(f"DRY RUN: Would install component {component_name}")
                    results[component_name] = True
                    continue

                self.logger.info(f"Installing component: {component_name}")

                # Check if component is already current (unless forced)
                if not force and self.receipts_adapter.is_current(component_name):
                    self.logger.info(f"Component {component_name} is already current, skipping")
                    results[component_name] = True
                    continue

                # Install component with transaction safety
                success = self._install_component(component_plan)
                results[component_name] = success

                if success:
                    completed_components.append(component_name)
                else:
                    # Component installation failed, rollback all completed components
                    self.logger.error(f"Component {component_name} failed, rolling back")
                    self._rollback_components(completed_components)
                    raise InstallationError(
                        f"Installation failed at component {component_name}",
                        component=component_name,
                        completed_components=completed_components,
                    )

        except Exception as e:
            # Unexpected error, rollback everything
            self._rollback_components(completed_components)
            raise InstallationError(
                f"Installation failed with unexpected error: {e}",
                completed_components=completed_components,
            ) from e

        return results

    def _install_component(self, component_plan) -> bool:
        """Install a single component with transaction safety.

        Args:
            component_plan: ComponentPlan to install

        Returns:
            True if successful, False otherwise
        """
        component_name = component_plan.component_id

        try:
            # Use staging context for atomic installation
            with staging(component_name, self.target_dir) as staging_dir:

                # Execute all file actions in staging
                for file_action in component_plan.file_actions:
                    self._execute_file_action(file_action, staging_dir)

                # If we get here, all actions succeeded in staging
                # The staging context manager will promote to target

            # Write receipt after successful promotion
            receipt = Receipt(
                component_id=component_name,
                manifest_hash=component_plan.manifest_hash,
                files=component_plan.file_actions,
                metadata={
                    "installation_method": "transaction_safe",
                    "staging_used": True,
                }
            )
            self.receipts_adapter.write_receipt(receipt)

            self.logger.info(f"Component {component_name} installed successfully")
            return True

        except Exception as e:
            self.logger.error(f"Component {component_name} installation failed: {e}")
            return False

    def _execute_file_action(self, action: FileAction, staging_dir: Path) -> None:
        """Execute a single file action in staging directory.

        Args:
            action: FileAction to execute
            staging_dir: Staging directory for the action

        Raises:
            TransactionError: If action execution fails
        """
        try:
            target_path = staging_dir / action.target_path.relative_to(self.target_dir)

            # Ensure parent directory exists
            safe_mkdir(target_path.parent, create_sentinel=False)

            if action.action_type == "COPY":
                shutil.copy2(action.source_path, target_path)

            elif action.action_type == "MERGE":
                # Use YAML ops for content merging
                merged_content = self.yaml_ops.merge_content(
                    action.source_path,
                    target_path if target_path.exists() else None,
                    strategy="deep_merge"
                )
                atomic_write(merged_content, target_path)

            elif action.action_type == "TEMPLATE":
                # Use YAML ops for template processing
                processed_content = self.yaml_ops.process_template(
                    action.source_path,
                    action.metadata.get("variables", {})
                )
                atomic_write(processed_content, target_path)

            elif action.action_type == "SKIP":
                # No action needed for SKIP
                pass

            else:
                raise TransactionError(
                    f"Unknown action type: {action.action_type}",
                    operation="file_action",
                    details={"action_type": action.action_type}
                )

        except Exception as e:
            raise TransactionError(
                f"Failed to execute action {action.action_type} for {action.target_path}: {e}",
                operation="file_action",
                details={
                    "action_type": action.action_type,
                    "source_path": str(action.source_path),
                    "target_path": str(action.target_path),
                }
            ) from e

    def _rollback_components(self, component_names: List[str]) -> None:
        """Rollback installed components by removing their receipts and files.

        Args:
            component_names: List of component names to rollback
        """
        for component_name in reversed(component_names):  # Rollback in reverse order
            try:
                self.logger.info(f"Rolling back component: {component_name}")

                # Get receipt to know what files were installed
                receipt = self.receipts_adapter.read_receipt(component_name)
                if receipt:
                    # Remove installed files (in reverse order)
                    for file_action in reversed(receipt.files):
                        target_path = file_action.target_path
                        if target_path.exists():
                            if target_path.is_file():
                                target_path.unlink()
                            elif target_path.is_dir() and not any(target_path.iterdir()):
                                # Only remove empty directories
                                target_path.rmdir()

                # Remove receipt
                self.receipts_adapter.remove_receipt(component_name)

                self.logger.info(f"Component {component_name} rolled back successfully")

            except Exception as e:
                self.logger.error(f"Failed to rollback component {component_name}: {e}")
                # Continue with other rollbacks even if one fails

    def uninstall_component(self, component_name: str) -> bool:
        """Uninstall a single component.

        Args:
            component_name: Name of component to uninstall

        Returns:
            True if successful, False otherwise
        """
        try:
            receipt = self.receipts_adapter.read_receipt(component_name)
            if not receipt:
                self.logger.warning(f"No receipt found for component {component_name}")
                return False

            self.logger.info(f"Uninstalling component: {component_name}")

            # Remove files in reverse order
            for file_action in reversed(receipt.files):
                target_path = file_action.target_path
                if target_path.exists():
                    if target_path.is_file():
                        target_path.unlink()
                        self.logger.debug(f"Removed file: {target_path}")
                    elif target_path.is_dir() and not any(target_path.iterdir()):
                        # Only remove empty directories
                        target_path.rmdir()
                        self.logger.debug(f"Removed empty directory: {target_path}")

            # Remove receipt
            self.receipts_adapter.remove_receipt(component_name)

            self.logger.info(f"Component {component_name} uninstalled successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to uninstall component {component_name}: {e}")
            return False

    def list_installed_components(self) -> List[str]:
        """List all installed components.

        Returns:
            List of installed component names
        """
        return self.receipts_adapter.list_receipts()
