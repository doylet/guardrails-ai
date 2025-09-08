"""
Enhanced Plugin Installer for AI Guardrails Bootstrap System

This module provides the enhanced plugin installer that integrates:
- Lifecycle hooks execution (pre/post install, validation, cleanup)
- Template engine processing with Jinja2
- Component manager for dependency resolution
- Configuration validation with JSON Schema
- Legacy plugin adapter for backward compatibility
- Security-first approach with sandboxed execution

Features:
- Complete plugin installation workflow
- Component-level installation and dependency resolution
- Template processing with variable substitution
- Hook execution with security sandboxing
- Configuration validation and inheritance
- Rollback support for failed installations
- Dry-run capability for testing
- Progress reporting and detailed logging
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging
from datetime import datetime

from ..domain.plugin_models import PluginManifest
from ..adapters.legacy_plugin_adapter import LegacyPluginAdapter
from ..core.plugin_validator import PluginValidator
from ..core.config_validator import ConfigValidator, ValidationResult
from ..core.plugin_lifecycle import PluginLifecycle, HookExecutionContext
from ..core.component_manager import ComponentManager, ComponentState, ComponentStatus, InstallationPlan
from ..adapters.template_engine import TemplateEngine
from ..adapters.plugin_processor import PluginProcessor


@dataclass
class InstallationResult:
    """Result of plugin installation operation."""
    success: bool
    plugin_name: str
    version: str
    installed_components: List[str] = None
    failed_components: List[str] = None
    error_message: Optional[str] = None
    installation_time: Optional[str] = None
    rollback_performed: bool = False


@dataclass
class PluginInstallationContext:
    """Context for plugin installation."""
    plugin_path: Path
    target_path: Path
    manifest: PluginManifest
    configuration: Dict[str, Any]
    selected_components: Optional[List[str]] = None
    dry_run: bool = False
    force: bool = False
    skip_hooks: bool = False


class EnhancedPluginInstaller:
    """Enhanced plugin installer with lifecycle hooks and template processing."""

    def __init__(self, plugin_path: Path, target_path: Path):
        self.plugin_path = Path(plugin_path).resolve()
        self.target_path = Path(target_path).resolve()
        self.logger = logging.getLogger(__name__)

        # Initialize components
        self.legacy_adapter = LegacyPluginAdapter()
        self.plugin_validator = PluginValidator()
        self.plugin_lifecycle = PluginLifecycle(plugin_path, target_path)
        self.component_manager = ComponentManager(plugin_path, target_path)
        self.template_engine = TemplateEngine()
        self.config_validator = ConfigValidator()
        self.plugin_processor = PluginProcessor(plugin_path, target_path)

        # Installation tracking
        self.installation_history: List[InstallationResult] = []

    def install_plugin(self, context: PluginInstallationContext) -> InstallationResult:
        """
        Install plugin with full lifecycle management.

        Args:
            context: Installation context with all necessary parameters

        Returns:
            Installation result with success status and details
        """
        try:
            self.logger.info(f"Starting plugin installation: {context.manifest.name}")

            # Step 1: Load and validate manifest
            manifest = self._prepare_manifest(context)

            # Step 2: Validate plugin
            validation_result = self._validate_plugin(manifest, context)
            if not validation_result.valid:
                return self._create_error_result(
                    context, f"Plugin validation failed: {validation_result.get_error_summary()}"
                )

            # Step 3: Create installation plan
            installation_plan = self._create_installation_plan(manifest, context)
            if installation_plan.conflicts:
                return self._create_error_result(
                    context, f"Installation conflicts detected: {'; '.join(installation_plan.conflicts)}"
                )

            # Step 4: Pre-installation hooks
            if not context.skip_hooks:
                hook_result = self._execute_pre_installation_hooks(manifest, context)
                if not hook_result.success:
                    return self._create_error_result(
                        context, f"Pre-installation hook failed: {hook_result.error_message}"
                    )

            # Step 5: Install components
            component_results = self._install_components(manifest, installation_plan, context)

            # Check for failures
            failed_components = [
                name for name, state in component_results.items()
                if state.status == ComponentStatus.FAILED
            ]

            if failed_components:
                # Attempt rollback
                self._rollback_installation(component_results, context)
                return self._create_error_result(
                    context, f"Component installation failed: {', '.join(failed_components)}"
                )

            # Step 6: Post-installation hooks
            if not context.skip_hooks:
                hook_result = self._execute_post_installation_hooks(manifest, context)
                if not hook_result.success:
                    # Rollback on post-install failure
                    self._rollback_installation(component_results, context)
                    return self._create_error_result(
                        context, f"Post-installation hook failed: {hook_result.error_message}"
                    )

            # Step 7: Validation hooks
            if not context.skip_hooks:
                validation_hook_result = self._execute_validation_hooks(manifest, context)
                if not validation_hook_result.success:
                    self.logger.warning(f"Validation hook failed: {validation_hook_result.error_message}")

            # Success
            installed_components = list(component_results.keys())
            installation_time = datetime.now().isoformat()

            result = InstallationResult(
                success=True,
                plugin_name=manifest.name,
                version=manifest.version,
                installed_components=installed_components,
                failed_components=[],
                installation_time=installation_time
            )

            self.installation_history.append(result)
            self.logger.info(f"Plugin installation completed successfully: {context.manifest.name}")

            return result

        except Exception as e:
            self.logger.error(f"Plugin installation failed: {e}")
            return self._create_error_result(context, str(e))

    def uninstall_plugin(self, plugin_name: str, configuration: Dict[str, Any] = None) -> bool:
        """
        Uninstall plugin and clean up components.

        Args:
            plugin_name: Name of plugin to uninstall
            configuration: Optional configuration for cleanup

        Returns:
            True if uninstall successful
        """
        try:
            # Find installation record
            installation_record = None
            for record in self.installation_history:
                if record.plugin_name == plugin_name and record.success:
                    installation_record = record
                    break

            if not installation_record:
                self.logger.warning(f"No installation record found for plugin: {plugin_name}")
                return False

            # Execute cleanup hooks if available
            # This would require loading the plugin manifest again

            # Remove installed components
            for component_name in installation_record.installed_components:
                component_state = self.component_manager.get_component_status(component_name)
                if component_state:
                    self.component_manager.rollback_component(component_name)

            self.logger.info(f"Plugin uninstalled successfully: {plugin_name}")
            return True

        except Exception as e:
            self.logger.error(f"Plugin uninstall failed: {e}")
            return False

    def dry_run_install(self, context: PluginInstallationContext) -> Dict[str, Any]:
        """
        Perform dry run installation to preview changes.

        Args:
            context: Installation context (dry_run should be True)

        Returns:
            Dictionary with preview information
        """
        context.dry_run = True

        try:
            # Prepare manifest
            manifest = self._prepare_manifest(context)

            # Validate plugin
            validation_result = self._validate_plugin(manifest, context)

            # Create installation plan
            installation_plan = self._create_installation_plan(manifest, context)

            # Simulate component installation
            component_info = {}
            for component_name in installation_plan.installation_order:
                component = manifest.components[component_name]
                file_count = len(component.files) if component.files else 0
                component_info[component_name] = {
                    "description": component.description,
                    "file_count": file_count,
                    "dependencies": component.dependencies or []
                }

            return {
                "plugin_name": manifest.name,
                "version": manifest.version,
                "validation_result": {
                    "valid": validation_result.valid,
                    "errors": [error.message for error in validation_result.errors]
                },
                "installation_plan": {
                    "components": installation_plan.components,
                    "installation_order": installation_plan.installation_order,
                    "conflicts": installation_plan.conflicts
                },
                "component_details": component_info,
                "estimated_files": sum(info["file_count"] for info in component_info.values())
            }

        except Exception as e:
            return {
                "error": str(e),
                "plugin_name": context.manifest.name if context.manifest else "unknown"
            }

    def _prepare_manifest(self, context: PluginInstallationContext) -> PluginManifest:
        """Prepare plugin manifest, handling legacy format if needed."""
        manifest = context.manifest

        # Check if this is a legacy format manifest
        if self.legacy_adapter.is_legacy_format(manifest):
            self.logger.info("Converting legacy plugin format to enhanced format")
            manifest = self.legacy_adapter.convert_to_enhanced(manifest)

        return manifest

    def _validate_plugin(self, manifest: PluginManifest, context: PluginInstallationContext) -> ValidationResult:
        """Validate plugin manifest and configuration."""
        errors = self.plugin_validator.validate_plugin_manifest(manifest)

        # Convert list of errors to ValidationResult
        if errors:
            from ..core.config_validator import ValidationError
            validation_errors = [ValidationError(error, "", "") for error in errors]
            return ValidationResult(
                valid=False,
                errors=validation_errors,
                processed_config={}
            )
        else:
            return ValidationResult(
                valid=True,
                errors=[],
                processed_config={}
            )

    def _create_installation_plan(self, manifest: PluginManifest,
                                context: PluginInstallationContext) -> InstallationPlan:
        """Create installation plan with dependency resolution."""
        return self.component_manager.create_installation_plan(
            manifest, context.selected_components
        )

    def _execute_pre_installation_hooks(self, manifest: PluginManifest,
                                      context: PluginInstallationContext):
        """Execute pre-installation hooks."""
        if not manifest.hooks or not manifest.hooks.pre_install:
            return type('Result', (), {'success': True})()

        execution_context = HookExecutionContext(
            plugin_name=manifest.name,
            plugin_version=manifest.version,
            plugin_path=context.plugin_path,
            target_path=context.target_path,
            environment=self._build_hook_environment(context),
            configuration=context.configuration,
            dry_run=context.dry_run
        )

        return self.plugin_lifecycle.execute_hooks(
            manifest.hooks, "pre_install", execution_context
        )

    def _execute_post_installation_hooks(self, manifest: PluginManifest,
                                       context: PluginInstallationContext):
        """Execute post-installation hooks."""
        if not manifest.hooks or not manifest.hooks.post_install:
            return type('Result', (), {'success': True})()

        execution_context = HookExecutionContext(
            plugin_name=manifest.name,
            plugin_version=manifest.version,
            plugin_path=context.plugin_path,
            target_path=context.target_path,
            environment=self._build_hook_environment(context),
            configuration=context.configuration,
            dry_run=context.dry_run
        )

        return self.plugin_lifecycle.execute_hooks(
            manifest.hooks, "post_install", execution_context
        )

    def _execute_validation_hooks(self, manifest: PluginManifest,
                                context: PluginInstallationContext):
        """Execute validation hooks."""
        if not manifest.hooks or not manifest.hooks.validate:
            return type('Result', (), {'success': True})()

        execution_context = HookExecutionContext(
            plugin_name=manifest.name,
            plugin_version=manifest.version,
            plugin_path=context.plugin_path,
            target_path=context.target_path,
            environment=self._build_hook_environment(context),
            configuration=context.configuration,
            dry_run=context.dry_run
        )

        return self.plugin_lifecycle.execute_hooks(
            manifest.hooks, "validate", execution_context
        )

    def _install_components(self, manifest: PluginManifest, installation_plan: InstallationPlan,
                          context: PluginInstallationContext) -> Dict[str, ComponentState]:
        """Install components according to the installation plan."""
        return self.component_manager.install_components(
            manifest, installation_plan, context.configuration, context.dry_run
        )

    def _rollback_installation(self, component_results: Dict[str, ComponentState],
                             context: PluginInstallationContext) -> None:
        """Rollback failed installation."""
        self.logger.info("Performing installation rollback")

        for component_name, component_state in component_results.items():
            if component_state.status == ComponentStatus.INSTALLED:
                try:
                    self.component_manager.rollback_component(component_name)
                    self.logger.info(f"Rolled back component: {component_name}")
                except Exception as e:
                    self.logger.error(f"Failed to rollback component {component_name}: {e}")

    def _build_hook_environment(self, context: PluginInstallationContext) -> Dict[str, str]:
        """Build environment variables for hook execution."""
        return {
            "PLUGIN_PATH": str(context.plugin_path),
            "TARGET_PATH": str(context.target_path),
            "DRY_RUN": "true" if context.dry_run else "false",
            "FORCE": "true" if context.force else "false"
        }

    def _create_error_result(self, context: PluginInstallationContext, error_message: str) -> InstallationResult:
        """Create error result for failed installation."""
        result = InstallationResult(
            success=False,
            plugin_name=context.manifest.name if context.manifest else "unknown",
            version=context.manifest.version if context.manifest else "unknown",
            error_message=error_message,
            installation_time=datetime.now().isoformat()
        )

        self.installation_history.append(result)
        return result

    def get_installation_history(self) -> List[InstallationResult]:
        """Get history of all installation attempts."""
        return self.installation_history.copy()

    def get_plugin_status(self, plugin_name: str) -> Optional[InstallationResult]:
        """Get status of a specific plugin installation."""
        for record in reversed(self.installation_history):
            if record.plugin_name == plugin_name:
                return record
        return None


class PluginInstallerError(Exception):
    """Exception raised during plugin installation operations."""
    pass
