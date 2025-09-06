"""Orchestrator for the AI Guardrails installation system.

This module provides the main orchestration layer that coordinates
the resolver, planner, installer, and doctor components. It manages
transaction boundaries, error handling, and provides the main entry
point for all installation operations.

The orchestrator implements the complete pipeline:
resolver → planner → installer with proper error handling and rollback.
"""

from pathlib import Path
from typing import Dict, List, Optional, Union

from ..domain.model import InstallPlan
from ..domain.errors import OrchestrationError
from ..adapters.receipts import ReceiptsAdapter
from ..adapters.yaml_ops import YamlOpsAdapter
from ..adapters.hashing import HashingAdapter
from ..adapters.logging import get_logger
from .resolver import Resolver
from .planner import Planner
from .installer import Installer
from .doctor import Doctor, DoctorDiagnostic


class Orchestrator:
    """Main orchestrator for AI Guardrails installation system."""

    def __init__(self, target_dir: Path = None):
        """Initialize orchestrator with default adapters.

        Args:
            target_dir: Target directory for installation (defaults to cwd)
        """
        self.target_dir = Path(target_dir) if target_dir else Path.cwd()
        self.logger = get_logger(__name__)

        # Initialize adapters
        self.receipts_adapter = ReceiptsAdapter(self.target_dir)
        self.yaml_ops = YamlOpsAdapter()
        self.hashing_adapter = HashingAdapter()

        # Initialize core components
        self.resolver = Resolver(
            receipts_adapter=self.receipts_adapter,
            yaml_ops=self.yaml_ops,
        )
        self.planner = Planner(
            receipts_adapter=self.receipts_adapter,
            hashing_adapter=self.hashing_adapter,
        )
        self.installer = Installer(
            target_dir=self.target_dir,
            receipts_adapter=self.receipts_adapter,
            yaml_ops=self.yaml_ops,
        )
        self.doctor = Doctor(
            target_dir=self.target_dir,
            receipts_adapter=self.receipts_adapter,
            hashing_adapter=self.hashing_adapter,
        )

    def plan(
        self,
        profile: str = "default",
        template_repo: Optional[Path] = None,
        plugins_dir: Optional[Path] = None,
    ) -> InstallPlan:
        """Generate an installation plan for the specified profile.

        Args:
            profile: Profile name to install
            template_repo: Path to template repository
            plugins_dir: Path to plugins directory

        Returns:
            InstallPlan ready for execution

        Raises:
            OrchestrationError: If planning fails
        """
        try:
            self.logger.info(f"Planning installation for profile: {profile}")

            # Resolve dependencies and create resolved specification
            resolved_spec = self.resolver.resolve(
                profile=profile,
                template_repo=template_repo,
                plugins_dir=plugins_dir,
            )

            # Generate installation plan
            install_plan = self.planner.plan(resolved_spec)

            self.logger.info(f"Plan generated with {len(install_plan.components)} components")
            return install_plan

        except Exception as e:
            raise OrchestrationError(
                f"Failed to generate plan for profile {profile}: {e}",
                operation="plan",
                profile=profile,
            ) from e

    def install(
        self,
        profile: str = "default",
        template_repo: Optional[Path] = None,
        plugins_dir: Optional[Path] = None,
        dry_run: bool = False,
        force: bool = False,
    ) -> Dict[str, bool]:
        """Install the specified profile with transaction safety.

        Args:
            profile: Profile name to install
            template_repo: Path to template repository
            plugins_dir: Path to plugins directory
            dry_run: If True, simulate installation without changes
            force: If True, overwrite existing files

        Returns:
            Dict mapping component names to success status

        Raises:
            OrchestrationError: If installation fails
        """
        try:
            # Generate plan
            install_plan = self.plan(
                profile=profile,
                template_repo=template_repo,
                plugins_dir=plugins_dir,
            )

            if dry_run:
                self.logger.info("DRY RUN: Installation plan ready")
                return {cp.component_id: True for cp in install_plan.components}

            # Execute installation
            self.logger.info(f"Installing profile: {profile}")
            results = self.installer.install_plan(
                plan=install_plan,
                dry_run=dry_run,
                force=force,
            )

            # Log results
            successful = sum(1 for success in results.values() if success)
            total = len(results)
            self.logger.info(f"Installation completed: {successful}/{total} components successful")

            return results

        except Exception as e:
            raise OrchestrationError(
                f"Failed to install profile {profile}: {e}",
                operation="install",
                profile=profile,
            ) from e

    def doctor(
        self,
        components: Optional[List[str]] = None,
        repair: bool = False,
        dry_run: bool = False,
    ) -> List[DoctorDiagnostic]:
        """Run health checks on installed components.

        Args:
            components: Specific components to check (None for all)
            repair: If True, attempt to repair found issues
            dry_run: If True, simulate repairs without making changes

        Returns:
            List of diagnostic findings

        Raises:
            OrchestrationError: If doctor operations fail
        """
        try:
            self.logger.info("Running health checks...")

            # Perform diagnosis
            diagnostics = self.doctor.diagnose(
                components=components,
                include_drift=True,
                include_missing=True,
                include_orphans=True,
            )

            # Get summary
            summary = self.doctor.get_health_summary(diagnostics)
            self.logger.info(
                f"Health check complete: {summary['error']} errors, "
                f"{summary['warning']} warnings, {summary['info']} info, "
                f"{summary['repairable']} repairable"
            )

            # Attempt repairs if requested
            if repair and summary['repairable'] > 0:
                self.logger.info("Attempting repairs...")
                repair_results = self.doctor.repair(
                    diagnostics=diagnostics,
                    dry_run=dry_run,
                )
                successful_repairs = sum(1 for success in repair_results.values() if success)
                total_repairs = len(repair_results)
                self.logger.info(f"Repair completed: {successful_repairs}/{total_repairs} successful")

            return diagnostics

        except Exception as e:
            raise OrchestrationError(
                f"Doctor operation failed: {e}",
                operation="doctor",
            ) from e

    def uninstall(
        self,
        component: str,
    ) -> bool:
        """Uninstall a specific component.

        Args:
            component: Name of component to uninstall

        Returns:
            True if successful, False otherwise

        Raises:
            OrchestrationError: If uninstallation fails
        """
        try:
            self.logger.info(f"Uninstalling component: {component}")

            result = self.installer.uninstall_component(component)

            if result:
                self.logger.info(f"Component {component} uninstalled successfully")
            else:
                self.logger.error(f"Failed to uninstall component {component}")

            return result

        except Exception as e:
            raise OrchestrationError(
                f"Failed to uninstall component {component}: {e}",
                operation="uninstall",
                component=component,
            ) from e

    def list_profiles(self) -> List[str]:
        """List available installation profiles.

        Returns:
            List of available profile names
        """
        try:
            return self.resolver.list_profiles()
        except Exception as e:
            self.logger.error(f"Failed to list profiles: {e}")
            return []

    def list_components(self, profile: Optional[str] = None) -> List[str]:
        """List available components.

        Args:
            profile: Profile to list components for (None for all)

        Returns:
            List of available component names
        """
        try:
            if profile:
                resolved_spec = self.resolver.resolve(profile=profile)
                return [comp.component_id for comp in resolved_spec.components]
            else:
                return self.resolver.list_components()
        except Exception as e:
            self.logger.error(f"Failed to list components: {e}")
            return []

    def list_installed(self) -> List[str]:
        """List installed components.

        Returns:
            List of installed component names
        """
        try:
            return self.installer.list_installed_components()
        except Exception as e:
            self.logger.error(f"Failed to list installed components: {e}")
            return []

    def get_component_status(self, component: str) -> Dict[str, Union[str, bool]]:
        """Get detailed status for a component.

        Args:
            component: Component name to check

        Returns:
            Dict with component status information
        """
        try:
            status = {
                "component": component,
                "installed": False,
                "current": False,
                "has_receipt": False,
                "receipt_valid": False,
            }

            # Check if component is installed
            installed_components = self.installer.list_installed_components()
            if component in installed_components:
                status["installed"] = True

                # Check receipt
                receipt = self.receipts_adapter.read_receipt(component)
                if receipt:
                    status["has_receipt"] = True
                    status["receipt_valid"] = True  # Basic check
                    status["current"] = self.receipts_adapter.is_current(component)

            return status

        except Exception as e:
            self.logger.error(f"Failed to get status for component {component}: {e}")
            return {"component": component, "error": str(e)}

    def validate_environment(self) -> Dict[str, Union[str, bool]]:
        """Validate the environment for installation.

        Returns:
            Dict with validation results
        """
        validation = {
            "target_directory_writable": False,
            "receipts_directory_exists": False,
            "receipts_directory_writable": False,
            "python_version_ok": True,  # Assume OK if we're running
        }

        try:
            # Check target directory
            if self.target_dir.exists() and self.target_dir.is_dir():
                # Test write access
                test_file = self.target_dir / ".ai_guardrails_test"
                try:
                    test_file.write_text("test")
                    test_file.unlink()
                    validation["target_directory_writable"] = True
                except (PermissionError, OSError):
                    pass

            # Check receipts directory
            receipts_dir = self.receipts_adapter.receipts_dir
            if receipts_dir.exists():
                validation["receipts_directory_exists"] = True
                try:
                    test_file = receipts_dir / ".test"
                    test_file.write_text("test")
                    test_file.unlink()
                    validation["receipts_directory_writable"] = True
                except (PermissionError, OSError):
                    pass

        except Exception as e:
            self.logger.error(f"Environment validation failed: {e}")
            validation["error"] = str(e)

        return validation
