"""Enhanced doctor system for state validation and repair.

This module provides comprehensive health checks for installed components,
including receipt validation, drift detection, manifest verification,
and optional repair capabilities.

The doctor system can:
- Validate receipts against actual disk state
- Detect file drift and missing components
- Check manifest integrity and dependencies
- Repair corrupted or missing installations
"""

from pathlib import Path
from typing import Dict, List, Optional, Set

from ..domain.model import Receipt, ComponentPlan
from ..adapters.receipts import ReceiptsAdapter
from ..adapters.hashing import HashingAdapter
from ..adapters.logging import get_logger


class DoctorDiagnostic:
    """Represents a single diagnostic finding."""

    def __init__(
        self,
        severity: str,  # "info", "warning", "error"
        component: str,
        message: str,
        details: Optional[Dict] = None,
        repairable: bool = False,
    ):
        self.severity = severity
        self.component = component
        self.message = message
        self.details = details or {}
        self.repairable = repairable

    def __str__(self) -> str:
        icon = {"info": "ℹ️", "warning": "⚠️", "error": "❌"}[self.severity]
        repair_note = " (repairable)" if self.repairable else ""
        return f"{icon} {self.component}: {self.message}{repair_note}"


class Doctor:
    """Enhanced doctor system for state validation and repair."""

    def __init__(
        self,
        target_dir: Path,
        receipts_adapter: ReceiptsAdapter,
        hashing_adapter: HashingAdapter,
        resolver=None,
        template_repo=None,
    ):
        """Initialize doctor with required adapters.

        Args:
            target_dir: Target directory to validate
            receipts_adapter: Adapter for receipt operations
            hashing_adapter: Adapter for file hashing
            resolver: Optional resolver for manifest operations
            template_repo: Template repository path for base components
        """
        self.target_dir = target_dir
        self.receipts_adapter = receipts_adapter
        self.hashing_adapter = hashing_adapter
        self.resolver = resolver
        self.template_repo = template_repo
        self.logger = get_logger(__name__)

    def diagnose(
        self,
        components: Optional[List[str]] = None,
        include_drift: bool = True,
        include_missing: bool = True,
        include_orphans: bool = True,
    ) -> List[DoctorDiagnostic]:
        """Perform comprehensive health check on installed components.

        Args:
            components: Specific components to check, or None for all
            include_drift: Check for file content drift
            include_missing: Check for missing files
            include_orphans: Check for orphaned files

        Returns:
            List of diagnostic findings
        """
        diagnostics = []

        # Get installed components
        installed_components = self.receipts_adapter.list_installed_components()

        if components:
            # Filter to requested components
            check_components = [c for c in components if c in installed_components]
            missing_components = [c for c in components if c not in installed_components]

            # Report missing components
            for component in missing_components:
                diagnostics.append(DoctorDiagnostic(
                    severity="error",
                    component=component,
                    message="Component not installed",
                    repairable=False,
                ))
        else:
            check_components = installed_components

        # Check each installed component
        for component in check_components:
            component_diagnostics = self._diagnose_component(
                component,
                include_drift=include_drift,
                include_missing=include_missing,
            )
            diagnostics.extend(component_diagnostics)

        # Check for orphaned files if requested
        if include_orphans:
            orphan_diagnostics = self._diagnose_orphaned_files(installed_components)
            diagnostics.extend(orphan_diagnostics)

        return diagnostics

    def _diagnose_component(
        self,
        component_name: str,
        include_drift: bool = True,
        include_missing: bool = True,
    ) -> List[DoctorDiagnostic]:
        """Diagnose a single component.

        Args:
            component_name: Name of component to diagnose
            include_drift: Check for file content drift
            include_missing: Check for missing files

        Returns:
            List of diagnostic findings for this component
        """
        diagnostics = []

        try:
            # Get receipt
            receipt = self.receipts_adapter.read_receipt(component_name)
            if not receipt:
                diagnostics.append(DoctorDiagnostic(
                    severity="error",
                    component=component_name,
                    message="Receipt file missing or corrupted",
                    repairable=False,
                ))
                return diagnostics

            # Validate receipt structure
            if not self._validate_receipt_structure(receipt):
                diagnostics.append(DoctorDiagnostic(
                    severity="error",
                    component=component_name,
                    message="Receipt has invalid structure",
                    repairable=False,
                ))
                return diagnostics

            # Check each file in the receipt
            for file_action in receipt.files:
                target_path = file_action.target_path

                # Check if file exists
                if not target_path.exists():
                    if include_missing:
                        diagnostics.append(DoctorDiagnostic(
                            severity="error",
                            component=component_name,
                            message=f"Missing file: {target_path}",
                            details={"path": str(target_path)},
                            repairable=True,
                        ))
                    continue

                # Check file content drift
                if include_drift and file_action.target_hash:
                    current_hash = self.hashing_adapter.hash_file(target_path)
                    if current_hash != file_action.target_hash:
                        diagnostics.append(DoctorDiagnostic(
                            severity="warning",
                            component=component_name,
                            message=f"File content drift: {target_path}",
                            details={
                                "path": str(target_path),
                                "expected_hash": file_action.target_hash,
                                "actual_hash": current_hash,
                            },
                            repairable=True,
                        ))

        except Exception as e:
            diagnostics.append(DoctorDiagnostic(
                severity="error",
                component=component_name,
                message=f"Failed to diagnose component: {e}",
                details={"exception": str(e)},
                repairable=False,
            ))

        return diagnostics

    def _diagnose_orphaned_files(self, installed_components: List[str]) -> List[DoctorDiagnostic]:
        """Find files that exist but aren't tracked by any component.

        Args:
            installed_components: List of installed component names

        Returns:
            List of diagnostics for orphaned files
        """
        diagnostics = []

        try:
            # Collect tracked files from both receipts AND manifest definitions
            tracked_files = set()
            
            # Add files from receipts (already installed)
            for component in installed_components:
                receipt = self.receipts_adapter.read_receipt(component)
                if receipt:
                    for file_action in receipt.files:
                        tracked_files.add(file_action.target_path)

            # Add files that SHOULD be tracked by manifest/plugin components
            if self.resolver:
                tracked_files.update(self._get_manifest_tracked_files())

            # Check common AI guardrails directories for orphaned files
            check_dirs = [
                self.target_dir / ".ai",
                self.target_dir / "ai",
                self.target_dir / ".github" / "workflows",
            ]

            for check_dir in check_dirs:
                if check_dir.exists():
                    orphaned = self._find_orphaned_in_directory(check_dir, tracked_files)
                    for orphan_path in orphaned:
                        diagnostics.append(DoctorDiagnostic(
                            severity="warning",
                            component="<orphaned>",
                            message=f"Orphaned file not tracked by any component: {orphan_path}",
                            details={"path": str(orphan_path)},
                            repairable=False,  # We don't auto-remove orphaned files
                        ))

        except Exception as e:
            diagnostics.append(DoctorDiagnostic(
                severity="error",
                component="<system>",
                message=f"Failed to check for orphaned files: {e}",
                details={"exception": str(e)},
                repairable=False,
            ))

        return diagnostics

    def _get_manifest_tracked_files(self) -> Set[Path]:
        """Get all files that should be tracked by manifest/plugin components.
        
        Returns:
            Set of target file paths that are managed by components
        """
        tracked_files = set()
        
        try:
            # Load base manifest and plugins
            manifest = self.resolver._load_manifest()
            plugins = self.resolver._load_plugins()
            
            # Process base manifest components
            if 'components' in manifest:
                tracked_files.update(self._expand_component_files(manifest['components'], None))
            
            # Process plugin components
            for plugin_name, plugin_data in plugins.items():
                plugin_manifest = plugin_data['manifest']
                if 'components' in plugin_manifest:
                    tracked_files.update(self._expand_component_files(
                        plugin_manifest['components'], 
                        plugin_data['path']
                    ))
                    
        except Exception as e:
            self.logger.warning(f"Failed to load manifest tracked files: {e}")
            
        return tracked_files
    
    def _expand_component_files(self, components: Dict, plugin_path: Optional[Path]) -> Set[Path]:
        """Expand component file patterns to target paths.
        
        Args:
            components: Dictionary of component definitions
            plugin_path: Path to plugin directory (None for base components)
            
        Returns:
            Set of target file paths for these components
        """
        from glob import glob
        tracked_files = set()
        
        for comp_name, comp_config in components.items():
            if 'file_patterns' not in comp_config:
                continue
                
            # Determine source directory
            if plugin_path:
                source_dir = plugin_path
            else:
                # Base components use template repo (actual templates, not manifest location)
                source_dir = self.template_repo if self.template_repo else self.resolver.template_repo
                
            # Get target prefix for path transformation
            target_prefix = comp_config.get('target_prefix', '')
            
            # Expand each file pattern
            for pattern in comp_config['file_patterns']:
                # Find source files matching pattern
                search_pattern = str(source_dir / pattern)
                matching_files = glob(search_pattern, recursive=True)
                
                # For plugins, also try with templates/ prefix if no files found
                if plugin_path and not matching_files:
                    template_pattern = str(source_dir / "templates" / pattern)
                    matching_files = glob(template_pattern, recursive=True)
                
                # Transform to target paths
                for source_file in matching_files:
                    source_path = Path(source_file)
                    if source_path.is_file():
                        # Calculate relative path from source directory
                        try:
                            relative_path = source_path.relative_to(source_dir)
                            
                            # Apply target_prefix transformation
                            if target_prefix:
                                # Remove target_prefix from the beginning if present
                                path_str = str(relative_path)
                                if path_str.startswith(target_prefix):
                                    relative_path = Path(path_str[len(target_prefix):].lstrip('/'))
                            
                            # For plugins with templates/ structure, remove templates/ prefix
                            if plugin_path and str(relative_path).startswith('templates/'):
                                relative_path = Path(str(relative_path)[len('templates/'):])
                            
                            # Target path is relative to target_dir
                            target_path = self.target_dir / relative_path
                            tracked_files.add(target_path)
                            
                        except ValueError:
                            # Skip files outside source directory
                            continue
                            
        return tracked_files

    def _find_orphaned_in_directory(self, directory: Path, tracked_files: Set[Path]) -> List[Path]:
        """Find orphaned files in a specific directory.

        Args:
            directory: Directory to search
            tracked_files: Set of files tracked by receipts

        Returns:
            List of orphaned file paths
        """
        orphaned = []

        try:
            for file_path in directory.rglob("*"):
                if file_path.is_file() and file_path not in tracked_files:
                    # Skip certain system files
                    if not self._is_system_file(file_path):
                        orphaned.append(file_path)

        except Exception:
            # Skip directories we can't read
            pass

        return orphaned

    def _is_system_file(self, file_path: Path) -> bool:
        """Check if a file is a system file that should be ignored.

        Args:
            file_path: Path to check

        Returns:
            True if file should be ignored
        """
        ignored_patterns = [
            ".DS_Store",
            "Thumbs.db",
            "*.tmp",
            "*.temp",
            ".git",
        ]

        file_name = file_path.name
        for pattern in ignored_patterns:
            if pattern.startswith("*") and file_name.endswith(pattern[1:]):
                return True
            elif file_name == pattern:
                return True

        return False

    def _validate_receipt_structure(self, receipt: Receipt) -> bool:
        """Validate that a receipt has the expected structure.

        Args:
            receipt: Receipt to validate

        Returns:
            True if receipt is valid
        """
        try:
            # Check required fields
            if not receipt.component_id:
                return False
            if not receipt.installed_at:
                return False
            if not hasattr(receipt, 'files'):
                return False

            # Validate file actions
            for file_action in receipt.files:
                if not hasattr(file_action, 'target_path'):
                    return False
                if not hasattr(file_action, 'action_type'):
                    return False

            return True

        except Exception:
            return False

    def repair(
        self,
        diagnostics: List[DoctorDiagnostic],
        component_plans: Optional[Dict[str, ComponentPlan]] = None,
        dry_run: bool = False,
    ) -> Dict[str, bool]:
        """Attempt to repair issues found during diagnosis.

        Args:
            diagnostics: List of diagnostic findings to repair
            component_plans: ComponentPlan objects for reinstallation
            dry_run: If True, simulate repairs without making changes

        Returns:
            Dict mapping diagnostic messages to repair success status

        Raises:
            RepairError: If repair operations fail
        """
        results = {}

        # Filter to repairable diagnostics
        repairable = [d for d in diagnostics if d.repairable]

        if not repairable:
            self.logger.info("No repairable issues found")
            return results

        # Group by component for efficient repair
        by_component = {}
        for diagnostic in repairable:
            if diagnostic.component not in by_component:
                by_component[diagnostic.component] = []
            by_component[diagnostic.component].append(diagnostic)

        # Repair each component
        for component_name, component_diagnostics in by_component.items():
            try:
                if dry_run:
                    self.logger.info(f"DRY RUN: Would repair {len(component_diagnostics)} issues in {component_name}")
                    for diagnostic in component_diagnostics:
                        results[str(diagnostic)] = True
                else:
                    self.logger.info(f"Repairing {len(component_diagnostics)} issues in {component_name}")
                    component_results = self._repair_component(
                        component_name,
                        component_diagnostics,
                        component_plans.get(component_name) if component_plans else None,
                    )
                    results.update(component_results)

            except Exception as e:
                error_msg = f"Failed to repair component {component_name}: {e}"
                self.logger.error(error_msg)
                for diagnostic in component_diagnostics:
                    results[str(diagnostic)] = False

        return results

    def _repair_component(
        self,
        component_name: str,
        diagnostics: List[DoctorDiagnostic],
        component_plan: Optional[ComponentPlan] = None,
    ) -> Dict[str, bool]:
        """Repair issues for a single component.

        Args:
            component_name: Name of component to repair
            diagnostics: List of diagnostics for this component
            component_plan: ComponentPlan for reinstallation

        Returns:
            Dict mapping diagnostic messages to repair success status
        """
        results = {}

        # For now, implement basic file restoration
        # More sophisticated repair logic can be added later

        for diagnostic in diagnostics:
            try:
                if "Missing file" in diagnostic.message:
                    # TODO: Restore missing file from source
                    # This would require access to the original source files
                    # For now, mark as not repaired
                    results[str(diagnostic)] = False
                    self.logger.warning(f"Cannot repair missing file without source: {diagnostic.details.get('path')}")

                elif "File content drift" in diagnostic.message:
                    # TODO: Restore file from source if available
                    # For now, just log the drift
                    results[str(diagnostic)] = False
                    self.logger.warning(f"Cannot repair drift without source: {diagnostic.details.get('path')}")

                else:
                    # Unknown diagnostic type
                    results[str(diagnostic)] = False
                    self.logger.warning(f"Unknown diagnostic type, cannot repair: {diagnostic.message}")

            except Exception as e:
                results[str(diagnostic)] = False
                self.logger.error(f"Failed to repair diagnostic '{diagnostic.message}': {e}")

        return results

    def get_health_summary(self, diagnostics: List[DoctorDiagnostic]) -> Dict[str, int]:
        """Get a summary of health check results.

        Args:
            diagnostics: List of diagnostic findings

        Returns:
            Dict with counts of each severity level
        """
        summary = {"info": 0, "warning": 0, "error": 0, "repairable": 0}

        for diagnostic in diagnostics:
            summary[diagnostic.severity] += 1
            if diagnostic.repairable:
                summary["repairable"] += 1

        return summary
