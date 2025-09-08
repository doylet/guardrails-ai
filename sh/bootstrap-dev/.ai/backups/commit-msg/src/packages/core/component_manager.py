"""
Component Manager for AI Guardrails Bootstrap System

This module provides component lifecycle management with:
- Component dependency resolution with topological sorting
- Component installation with priority ordering
- Component validation and health checking
- Component rollback and cleanup
- Component status tracking and reporting
- Component-level configuration management

Features:
- Dependency graph resolution
- Installation ordering based on dependencies and priorities
- Atomic installation with rollback support
- Component health monitoring
- Configuration inheritance and validation
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import logging

from ..domain.plugin_models import ComponentDefinition, PluginManifest
from .config_validator import ConfigValidator, ValidationResult
from .plugin_lifecycle import PluginLifecycle, HookExecutionContext
from ..adapters.plugin_processor import PluginProcessor


class ComponentStatus(Enum):
    """Component installation status."""
    PENDING = "pending"
    INSTALLING = "installing"
    INSTALLED = "installed"
    FAILED = "failed"
    ROLLING_BACK = "rolling_back"
    REMOVED = "removed"


@dataclass
class ComponentState:
    """Current state of a component."""
    name: str
    status: ComponentStatus
    version: Optional[str] = None
    installation_path: Optional[Path] = None
    configuration: Dict[str, Any] = field(default_factory=dict)
    installed_files: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    installation_time: Optional[str] = None


@dataclass
class InstallationPlan:
    """Plan for component installation."""
    components: List[str]
    installation_order: List[str]
    dependency_graph: Dict[str, List[str]]
    conflicts: List[str] = field(default_factory=list)


class ComponentManager:
    """Component lifecycle management with dependency resolution."""

    def __init__(self, plugin_path: Path, target_path: Path):
        self.plugin_path = Path(plugin_path).resolve()
        self.target_path = Path(target_path).resolve()
        self.config_validator = ConfigValidator()
        self.plugin_processor = PluginProcessor(plugin_path, target_path)
        self.plugin_lifecycle = PluginLifecycle(plugin_path, target_path)
        self.component_states: Dict[str, ComponentState] = {}
        self.logger = logging.getLogger(__name__)

    def create_installation_plan(self, manifest: PluginManifest,
                                selected_components: Optional[List[str]] = None) -> InstallationPlan:
        """
        Create installation plan with dependency resolution.

        Args:
            manifest: Plugin manifest with components
            selected_components: Optional list of components to install

        Returns:
            Installation plan with resolved dependencies
        """
        # Determine components to install
        if selected_components:
            components_to_install = selected_components
        else:
            # Install all components
            components_to_install = list(manifest.components.keys())

        # Build dependency graph
        dependency_graph = self._build_dependency_graph(manifest, components_to_install)

        # Detect conflicts
        conflicts = self._detect_conflicts(manifest, components_to_install)

        # Resolve installation order
        try:
            installation_order = self._resolve_installation_order(
                dependency_graph, manifest.components
            )
        except ValueError as e:
            conflicts.append(str(e))
            installation_order = components_to_install  # Fallback order

        return InstallationPlan(
            components=components_to_install,
            installation_order=installation_order,
            dependency_graph=dependency_graph,
            conflicts=conflicts
        )

    def install_components(self, manifest: PluginManifest,
                         installation_plan: InstallationPlan,
                         configuration: Optional[Dict[str, Any]] = None,
                         dry_run: bool = False) -> Dict[str, ComponentState]:
        """
        Install components according to the installation plan.

        Args:
            manifest: Plugin manifest
            installation_plan: Installation plan with resolved dependencies
            configuration: Component configuration override
            dry_run: Whether to perform a dry run

        Returns:
            Dictionary of component states after installation
        """
        configuration = configuration or {}
        results = {}

        for component_name in installation_plan.installation_order:
            try:
                component = manifest.components[component_name]
                component_config = configuration.get(component_name, {})

                # Update component state
                self.component_states[component_name] = ComponentState(
                    name=component_name,
                    status=ComponentStatus.INSTALLING,
                    configuration=component_config
                )

                # Install component
                result = self._install_single_component(
                    component, manifest, component_config, dry_run
                )

                self.component_states[component_name] = result
                results[component_name] = result

                # Stop on failure unless continuing is explicitly requested
                if result.status == ComponentStatus.FAILED:
                    self.logger.error(f"Component {component_name} installation failed: {result.error_message}")
                    break

            except Exception as e:
                error_state = ComponentState(
                    name=component_name,
                    status=ComponentStatus.FAILED,
                    error_message=str(e)
                )
                self.component_states[component_name] = error_state
                results[component_name] = error_state
                self.logger.error(f"Component {component_name} installation error: {e}")
                break

        return results

    def validate_components(self, manifest: PluginManifest,
                          configuration: Optional[Dict[str, Any]] = None) -> Dict[str, ValidationResult]:
        """
        Validate component configurations.

        Args:
            manifest: Plugin manifest
            configuration: Component configurations to validate

        Returns:
            Validation results for each component
        """
        configuration = configuration or {}
        results = {}

        for component_name, component in manifest.components.items():
            component_config = configuration.get(component_name, {})

            validation_result = self.config_validator.validate_component_config(
                component_config, component
            )

            results[component_name] = validation_result

        return results

    def rollback_component(self, component_name: str) -> bool:
        """
        Rollback a component installation.

        Args:
            component_name: Name of component to rollback

        Returns:
            True if rollback successful
        """
        if component_name not in self.component_states:
            return False

        component_state = self.component_states[component_name]

        try:
            component_state.status = ComponentStatus.ROLLING_BACK

            # Remove installed files
            for file_path in component_state.installed_files:
                try:
                    Path(file_path).unlink(missing_ok=True)
                except Exception as e:
                    self.logger.warning(f"Failed to remove file during rollback: {file_path}: {e}")

            # Execute cleanup hooks if available
            # (This would require access to the component's hooks)

            component_state.status = ComponentStatus.REMOVED
            component_state.installed_files = []

            return True

        except Exception as e:
            self.logger.error(f"Rollback failed for component {component_name}: {e}")
            component_state.error_message = str(e)
            return False

    def get_component_status(self, component_name: str) -> Optional[ComponentState]:
        """Get current status of a component."""
        return self.component_states.get(component_name)

    def get_all_component_status(self) -> Dict[str, ComponentState]:
        """Get status of all components."""
        return self.component_states.copy()

    def _install_single_component(self, component: ComponentDefinition,
                                manifest: PluginManifest,
                                configuration: Dict[str, Any],
                                dry_run: bool) -> ComponentState:
        """Install a single component."""
        from datetime import datetime

        try:
            # Validate component configuration
            validation_result = self.config_validator.validate_component_config(
                configuration, component
            )

            if not validation_result.valid:
                error_msg = "; ".join([error.message for error in validation_result.errors])
                return ComponentState(
                    name=component.name,
                    status=ComponentStatus.FAILED,
                    configuration=configuration,
                    error_message=f"Configuration validation failed: {error_msg}"
                )

            # Prepare execution context
            context = HookExecutionContext(
                plugin_name=manifest.name,
                plugin_version=manifest.version,
                plugin_path=self.plugin_path,
                target_path=self.target_path,
                environment={},  # Would be populated with actual environment
                configuration=validation_result.processed_config,
                dry_run=dry_run
            )

            installed_files = []

            # Execute pre-install hooks
            if component.hooks and component.hooks.pre_install:
                hook_result = self.plugin_lifecycle.execute_component_hooks(
                    component.hooks, "pre_install", context
                )
                if not hook_result.success:
                    return ComponentState(
                        name=component.name,
                        status=ComponentStatus.FAILED,
                        configuration=configuration,
                        error_message=f"Pre-install hook failed: {hook_result.error_message}"
                    )

            # Process file operations
            for file_operation in component.files:
                try:
                    processed_files = self.plugin_processor.process_file_operation(
                        file_operation, context.configuration
                    )
                    installed_files.extend(processed_files)
                except Exception as e:
                    return ComponentState(
                        name=component.name,
                        status=ComponentStatus.FAILED,
                        configuration=configuration,
                        error_message=f"File operation failed: {e}"
                    )

            # Execute post-install hooks
            if component.hooks and component.hooks.post_install:
                hook_result = self.plugin_lifecycle.execute_component_hooks(
                    component.hooks, "post_install", context
                )
                if not hook_result.success:
                    # Rollback installed files
                    for file_path in installed_files:
                        try:
                            Path(file_path).unlink(missing_ok=True)
                        except Exception:
                            pass

                    return ComponentState(
                        name=component.name,
                        status=ComponentStatus.FAILED,
                        configuration=configuration,
                        error_message=f"Post-install hook failed: {hook_result.error_message}"
                    )

            # Execute validation hooks
            if component.hooks and component.hooks.validate:
                hook_result = self.plugin_lifecycle.execute_component_hooks(
                    component.hooks, "validate", context
                )
                if not hook_result.success:
                    self.logger.warning(f"Component {component.name} validation failed: {hook_result.error_message}")

            return ComponentState(
                name=component.name,
                status=ComponentStatus.INSTALLED,
                version=manifest.version,
                installation_path=self.target_path,
                configuration=validation_result.processed_config,
                installed_files=installed_files,
                installation_time=datetime.now().isoformat()
            )

        except Exception as e:
            return ComponentState(
                name=component.name,
                status=ComponentStatus.FAILED,
                configuration=configuration,
                error_message=f"Component installation failed: {e}"
            )

    def _build_dependency_graph(self, manifest: PluginManifest,
                              selected_components: List[str]) -> Dict[str, List[str]]:
        """Build dependency graph for components."""
        graph = {}

        # Add all selected components and their dependencies
        components_to_process = set(selected_components)
        processed = set()

        while components_to_process:
            component_name = components_to_process.pop()
            if component_name in processed:
                continue

            processed.add(component_name)

            if component_name not in manifest.components:
                continue

            component = manifest.components[component_name]
            dependencies = component.dependencies or []

            graph[component_name] = dependencies

            # Add dependencies to processing queue
            for dep in dependencies:
                if dep not in processed:
                    components_to_process.add(dep)

        return graph

    def _resolve_installation_order(self, dependency_graph: Dict[str, List[str]],
                                  components: Dict[str, ComponentDefinition]) -> List[str]:
        """Resolve installation order using topological sort with priorities."""
        # Topological sort with Kahn's algorithm
        in_degree = {node: 0 for node in dependency_graph}

        for node in dependency_graph:
            for dependency in dependency_graph[node]:
                if dependency in in_degree:
                    in_degree[dependency] += 1

        # Priority queue: higher priority components first
        import heapq
        queue = []

        for node in in_degree:
            if in_degree[node] == 0:
                priority = components.get(node, ComponentDefinition(name=node, description="")).priority
                heapq.heappush(queue, (-priority, node))  # Negative for max-heap behavior

        result = []

        while queue:
            _, node = heapq.heappop(queue)
            result.append(node)

            # Process dependents
            for dependent in dependency_graph:
                if node in dependency_graph[dependent]:
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        priority = components.get(dependent, ComponentDefinition(name=dependent, description="")).priority
                        heapq.heappush(queue, (-priority, dependent))

        # Check for cycles
        if len(result) != len(dependency_graph):
            remaining = set(dependency_graph.keys()) - set(result)
            raise ValueError(f"Circular dependency detected involving: {', '.join(remaining)}")

        return result

    def _detect_conflicts(self, manifest: PluginManifest,
                        selected_components: List[str]) -> List[str]:
        """Detect potential conflicts between components."""
        conflicts = []

        # Check for file target conflicts
        file_targets = {}

        for component_name in selected_components:
            if component_name not in manifest.components:
                conflicts.append(f"Component not found: {component_name}")
                continue

            component = manifest.components[component_name]

            for file_op in component.files:
                target = file_op.target
                if target in file_targets:
                    conflicts.append(
                        f"File conflict: components '{component_name}' and '{file_targets[target]}' "
                        f"both target '{target}'"
                    )
                else:
                    file_targets[target] = component_name

        return conflicts


class ComponentManagerError(Exception):
    """Exception raised during component management operations."""
    pass
