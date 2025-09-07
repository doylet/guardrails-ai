"""Pure planning logic for the AI Guardrails Bootstrap System.

This module provides deterministic planning that converts a resolved specification
into a concrete installation plan. All operations are side-effect free and
produce the same output given the same inputs.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from glob import glob

from ..domain.constants import (
    TEMPLATE_EXTENSIONS,
    MERGEABLE_EXTENSIONS,
)
from ..domain.model import (
    InstallPlan,
    ComponentPlan,
    FileAction,
    ActionKind,
    Reason,
)
from ..adapters.hashing import sha256_file, sha256_content
from ..adapters.logging import get_logger
from ..utils.path_utils import apply_target_prefix_stripping, apply_destination_mappings
from .resolver import ResolvedSpec

logger = get_logger(__name__)


class Planner:
    """Pure planning logic for component installation."""

    def __init__(self, template_repo: Path, target_dir: Path):
        """Initialize planner with source and target locations.

        Args:
            template_repo: Path to template repository
            target_dir: Target directory for installation
        """
        self.template_repo = Path(template_repo)
        self.target_dir = Path(target_dir)

    def create_plan(
        self,
        resolved_spec: ResolvedSpec,
        profile: str = "unknown",
        force: bool = False,
        receipts_adapter: Optional[object] = None,
    ) -> InstallPlan:
        """Create installation plan from resolved specification.

        Args:
            resolved_spec: Resolved components and dependencies
            profile: Profile name this plan is for
            force: Force installation even if files are current
            receipts_adapter: Optional receipts adapter for current state

        Returns:
            Complete installation plan

        Raises:
            ValidationError: If file patterns or configurations are invalid
        """
        logger.info(f"Creating installation plan for {len(resolved_spec.components)} components")

        component_plans = []
        total_files = 0
        estimated_size = 0

        for component_config in resolved_spec.components:
            component_plan = self._plan_component(
                component_config,
                resolved_spec,
                force,
                receipts_adapter,
            )

            component_plans.append(component_plan)
            total_files += component_plan.total_files
            estimated_size += self._estimate_component_size(component_plan)

        plan = InstallPlan(
            profile=profile,
            components=component_plans,
            total_files=total_files,
            estimated_size=estimated_size,
        )

        logger.info(f"Created plan: {len(component_plans)} components, {total_files} files, ~{estimated_size} bytes")
        return plan

    def _plan_component(
        self,
        component_config: Dict,
        resolved_spec: ResolvedSpec,
        force: bool,
        receipts_adapter: Optional[object],
    ) -> ComponentPlan:
        """Plan installation for a single component."""
        comp_name = component_config["name"]
        logger.debug(f"Planning component: {comp_name}")

        # Discover source files
        source_files = self._discover_component_files(component_config, resolved_spec)

        # Plan actions for each file
        file_actions = []
        for src_path in source_files:
            action = self._plan_file_action(
                src_path,
                component_config,
                force,
                receipts_adapter,
            )
            if action:
                file_actions.append(action)

        # Calculate manifest digest for this component
        manifest_digest = self._calculate_component_digest(component_config)

        return ComponentPlan(
            component_id=comp_name,
            file_actions=file_actions,
            manifest_hash=manifest_digest,
            plugin_id=component_config.get("_plugin_id"),
        )

    def _discover_component_files(
        self,
        component_config: Dict,
        resolved_spec: ResolvedSpec,
    ) -> List[Path]:
        """Discover source files for a component based on file patterns."""
        patterns = component_config.get("file_patterns", [])
        if not patterns:
            return []

        # Determine source base directory
        if "_plugin_path" in component_config:
            base_dir = Path(component_config["_plugin_path"]) / "files"
        else:
            base_dir = self.template_repo

        discovered_files = []

        for pattern in patterns:
            # Resolve glob pattern relative to base directory
            search_pattern = str(base_dir / pattern)
            matched_files = glob(search_pattern, recursive=True)

            for matched_file in matched_files:
                file_path = Path(matched_file)
                if file_path.is_file():
                    discovered_files.append(file_path)

        # Remove duplicates and sort for deterministic output
        unique_files = list(set(discovered_files))
        unique_files.sort()

        logger.debug(f"Discovered {len(unique_files)} files for component {component_config['name']}")
        return unique_files

    def _plan_file_action(
        self,
        src_path: Path,
        component_config: Dict,
        force: bool,
        receipts_adapter: Optional[object],
    ) -> Optional[FileAction]:
        """Plan action for a single file."""
        # Calculate destination path
        dst_path = self._calculate_destination_path(src_path, component_config)

        # Determine action kind
        action_kind = self._determine_action_kind(src_path, dst_path)

        # Determine reason for action
        reason = self._determine_action_reason(
            src_path,
            dst_path,
            component_config["name"],
            force,
            receipts_adapter,
        )

        # Skip if no action needed
        if reason == "unchanged" and not force:
            action_kind = "SKIP"

        # Get file mode
        file_mode = self._get_file_mode(src_path, component_config)

        # Make paths relative for storage in plan
        relative_src = self._make_relative_to_base(src_path, component_config)
        relative_dst = dst_path.relative_to(self.target_dir)

        return FileAction(
            action_type=action_kind,
            source_path=relative_src,
            target_path=relative_dst,
            mode=file_mode,
            reason=reason,
        )

    def _calculate_destination_path(self, src_path: Path, component_config: Dict) -> Path:
        """Calculate destination path for a source file."""
        # Determine base source directory
        if "_plugin_path" in component_config:
            base_dir = Path(component_config["_plugin_path"]) / "files"
        else:
            base_dir = self.template_repo

        # Calculate relative path from base
        try:
            relative_path = src_path.relative_to(base_dir)
        except ValueError:
            # File is outside base directory, use filename only
            relative_path = src_path.name

        # Apply target_prefix stripping using shared utility
        component_name = component_config["name"]
        manifest = {"components": {component_name: component_config}}
        stripped_path = apply_target_prefix_stripping(component_name, str(relative_path), manifest)
        
        # Apply destination mappings using shared utility
        dst_mappings = component_config.get("destination_mappings", {})
        mapped_path = apply_destination_mappings(Path(stripped_path), dst_mappings)

        return self.target_dir / mapped_path

    def _determine_action_kind(self, src_path: Path, dst_path: Path) -> ActionKind:
        """Determine what kind of action to take for a file."""
        src_suffix = src_path.suffix.lower()
        dst_suffix = dst_path.suffix.lower()

        # Template files need processing
        if src_suffix in TEMPLATE_EXTENSIONS:
            return "TEMPLATE"

        # YAML/JSON files can be merged
        if (src_suffix in MERGEABLE_EXTENSIONS and
            dst_suffix in MERGEABLE_EXTENSIONS and
            dst_path.exists()):
            return "MERGE"

        # Default to copy
        return "COPY"

    def _determine_action_reason(
        self,
        src_path: Path,
        dst_path: Path,
        component_name: str,
        force: bool,
        receipts_adapter: Optional[object],
    ) -> Reason:
        """Determine why an action is needed."""
        if force:
            return "hash-diff"  # Force implies we want to update

        if not dst_path.exists():
            return "new"

        # Check if we have receipt information
        if receipts_adapter and hasattr(receipts_adapter, 'is_current'):
            try:
                if receipts_adapter.is_current(component_name, str(dst_path.relative_to(self.target_dir))):
                    return "unchanged"
            except Exception as e:
                logger.debug(f"Receipt check failed for {dst_path}: {e}")

        # Compare file hashes
        try:
            src_hash = sha256_file(src_path)
            dst_hash = sha256_file(dst_path)

            if src_hash == dst_hash:
                return "unchanged"
            else:
                # Check if this might be drift vs intentional change
                if receipts_adapter and hasattr(receipts_adapter, 'get_expected_hash'):
                    try:
                        expected_hash = receipts_adapter.get_expected_hash(
                            component_name,
                            str(dst_path.relative_to(self.target_dir))
                        )
                        if expected_hash and expected_hash != dst_hash:
                            return "drift"
                    except Exception:
                        pass

                return "hash-diff"

        except Exception as e:
            logger.debug(f"Hash comparison failed for {dst_path}: {e}")
            return "hash-diff"  # Assume change when we can't compare

    def _get_file_mode(self, src_path: Path, component_config: Dict) -> Optional[int]:
        """Get file mode for destination file."""
        # Check component-specific mode mappings
        mode_mappings = component_config.get("file_modes", {})

        for pattern, mode in mode_mappings.items():
            if str(src_path).endswith(pattern):
                return mode

        # Check if source file is executable
        try:
            src_stat = src_path.stat()
            if src_stat.st_mode & 0o111:  # Any execute bit set
                return 0o755
        except Exception:
            pass

        # Use default
        return None  # Let installer use default

    def _make_relative_to_base(self, src_path: Path, component_config: Dict) -> Path:
        """Make source path relative to component base directory."""
        if "_plugin_path" in component_config:
            base_dir = Path(component_config["_plugin_path"]) / "files"
        else:
            base_dir = self.template_repo

        try:
            return src_path.relative_to(base_dir)
        except ValueError:
            # File is outside base, use absolute path
            return src_path

    def _calculate_component_digest(self, component_config: Dict) -> str:
        """Calculate digest for component configuration."""
        # Create stable representation of component config
        config_copy = component_config.copy()

        # Remove internal fields that shouldn't affect digest
        for key in ["_plugin_id", "_plugin_path"]:
            config_copy.pop(key, None)

        config_json = json.dumps(config_copy, sort_keys=True, separators=(',', ':'))
        return sha256_content(config_json)

    def _estimate_component_size(self, component_plan: ComponentPlan) -> int:
        """Estimate disk space needed for component."""
        total_size = 0

        for action in component_plan.actions:
            if action.kind == "SKIP":
                continue

            # Estimate based on action type
            if action.kind in ("COPY", "TEMPLATE"):
                # Assume average file size (rough estimate)
                total_size += 4096  # 4KB default
            elif action.kind == "MERGE":
                # Merges typically don't add much
                total_size += 1024  # 1KB default

        return total_size

    def preview_plan(self, plan: InstallPlan, show_unchanged: bool = False) -> str:
        """Generate human-readable preview of installation plan.

        Args:
            plan: Installation plan to preview
            show_unchanged: Whether to show unchanged files

        Returns:
            Formatted preview string
        """
        lines = []
        lines.append(f"Installation Plan ({plan.component_count} components, {plan.actionable_files} actionable files)")
        lines.append("=" * 80)

        for component in plan.components:
            lines.append(f"\nComponent: {component.name}")
            if component.plugin_id:
                lines.append(f"  Plugin: {component.plugin_id}")

            actionable_actions = [a for a in component.actions if a.kind != "SKIP"]
            if actionable_actions or show_unchanged:
                for action in component.actions:
                    if action.kind == "SKIP" and not show_unchanged:
                        continue

                    symbol = self._get_action_symbol(action.kind)
                    lines.append(f"  {symbol} {action.dst} ({action.reason})")

            if not actionable_actions and not show_unchanged:
                lines.append("  (no changes needed)")

        return "\n".join(lines)

    def _get_action_symbol(self, action_kind: ActionKind) -> str:
        """Get symbol for action type in preview."""
        symbols = {
            "COPY": "+",
            "MERGE": "~",
            "TEMPLATE": "*",
            "SKIP": "-",
        }
        return symbols.get(action_kind, "?")

    def plan_summary(self, plan: InstallPlan) -> Dict:
        """Generate summary statistics for a plan.

        Args:
            plan: Installation plan to summarize

        Returns:
            Dictionary with summary statistics
        """
        action_counts = {"COPY": 0, "MERGE": 0, "TEMPLATE": 0, "SKIP": 0}
        reason_counts = {"new": 0, "hash-diff": 0, "unchanged": 0, "drift": 0}

        for component in plan.components:
            for action in component.actions:
                action_counts[action.kind] += 1
                reason_counts[action.reason] += 1

        return {
            "components": plan.component_count,
            "total_files": plan.total_files,
            "actionable_files": plan.actionable_files,
            "estimated_size": plan.estimated_size,
            "actions": action_counts,
            "reasons": reason_counts,
        }
