"""YAML and JSON operations adapter for content transformation.

This module provides a single interface for all content transformations including
YAML merging, JSON operations, and template processing. All file content edits
go through this adapter to ensure consistency and safety.
"""

import json
import re
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..domain.constants import (
    YAML_EXTENSIONS,
    JSON_EXTENSIONS,
    TEMPLATE_EXTENSIONS,
)
from ..domain.errors import TransactionError
from ..adapters.logging import get_logger

logger = get_logger(__name__)


class YamlOpsAdapter:
    """Single interface for all content transformation operations."""

    def __init__(self, target_dir: Path):
        """Initialize YAML operations adapter.

        Args:
            target_dir: Target directory for operations
        """
        self.target_dir = Path(target_dir)

    def merge_yaml(
        self,
        base_content: str,
        overlay_content: str,
        merge_strategy: str = "deep",
    ) -> str:
        """Merge YAML content with specified strategy.

        Args:
            base_content: Base YAML content
            overlay_content: Overlay YAML content to merge
            merge_strategy: Merge strategy ('deep', 'shallow', 'replace')

        Returns:
            Merged YAML content as string

        Raises:
            TransactionError: If merge operation fails
        """
        try:
            base_data = yaml.safe_load(base_content) or {}
            overlay_data = yaml.safe_load(overlay_content) or {}

            if merge_strategy == "replace":
                merged_data = overlay_data
            elif merge_strategy == "shallow":
                merged_data = {**base_data, **overlay_data}
            else:  # deep merge
                merged_data = self._deep_merge(base_data, overlay_data)

            return yaml.dump(
                merged_data,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
            )

        except yaml.YAMLError as e:
            raise TransactionError(
                f"YAML merge failed: {e}",
                "yaml_ops",
                "merge_yaml",
            ) from e
        except Exception as e:
            raise TransactionError(
                f"Content merge failed: {e}",
                "yaml_ops",
                "merge_yaml",
            ) from e

    def merge_json(
        self,
        base_content: str,
        overlay_content: str,
        merge_strategy: str = "deep",
    ) -> str:
        """Merge JSON content with specified strategy.

        Args:
            base_content: Base JSON content
            overlay_content: Overlay JSON content to merge
            merge_strategy: Merge strategy ('deep', 'shallow', 'replace')

        Returns:
            Merged JSON content as string

        Raises:
            TransactionError: If merge operation fails
        """
        try:
            base_data = json.loads(base_content) if base_content.strip() else {}
            overlay_data = json.loads(overlay_content) if overlay_content.strip() else {}

            if merge_strategy == "replace":
                merged_data = overlay_data
            elif merge_strategy == "shallow":
                merged_data = {**base_data, **overlay_data}
            else:  # deep merge
                merged_data = self._deep_merge(base_data, overlay_data)

            return json.dumps(merged_data, indent=2, sort_keys=True, ensure_ascii=False)

        except json.JSONDecodeError as e:
            raise TransactionError(
                f"JSON merge failed: {e}",
                "yaml_ops",
                "merge_json",
            ) from e
        except Exception as e:
            raise TransactionError(
                f"Content merge failed: {e}",
                "yaml_ops",
                "merge_json",
            ) from e

    def process_template(
        self,
        template_content: str,
        variables: Dict[str, Any],
        template_engine: str = "simple",
    ) -> str:
        """Process template content with variable substitution.

        Args:
            template_content: Template content with placeholders
            variables: Variables for substitution
            template_engine: Template engine ('simple', 'jinja2')

        Returns:
            Processed content with variables substituted

        Raises:
            TransactionError: If template processing fails
        """
        try:
            if template_engine == "simple":
                return self._process_simple_template(template_content, variables)
            elif template_engine == "jinja2":
                return self._process_jinja2_template(template_content, variables)
            else:
                raise ValueError(f"Unknown template engine: {template_engine}")

        except Exception as e:
            raise TransactionError(
                f"Template processing failed: {e}",
                "yaml_ops",
                "process_template",
            ) from e

    def transform_content(
        self,
        source_path: Path,
        target_path: Path,
        action_kind: str,
        variables: Optional[Dict[str, Any]] = None,
        merge_strategy: str = "deep",
    ) -> str:
        """Transform content based on action kind and file types.

        Args:
            source_path: Source file path
            target_path: Target file path
            action_kind: Type of transformation (COPY, MERGE, TEMPLATE)
            variables: Variables for template processing
            merge_strategy: Strategy for merge operations

        Returns:
            Transformed content as string

        Raises:
            TransactionError: If transformation fails
        """
        try:
            # Read source content
            source_content = source_path.read_text(encoding="utf-8")

            if action_kind == "COPY":
                # Simple copy, no transformation
                return source_content

            elif action_kind == "TEMPLATE":
                # Process as template
                variables = variables or {}
                return self.process_template(source_content, variables)

            elif action_kind == "MERGE":
                # Merge with existing content
                if not target_path.exists():
                    # No existing content to merge with
                    return source_content

                target_content = target_path.read_text(encoding="utf-8")

                # Determine merge type based on file extensions
                source_ext = source_path.suffix.lower()
                target_ext = target_path.suffix.lower()

                if source_ext in YAML_EXTENSIONS and target_ext in YAML_EXTENSIONS:
                    return self.merge_yaml(target_content, source_content, merge_strategy)
                elif source_ext in JSON_EXTENSIONS and target_ext in JSON_EXTENSIONS:
                    return self.merge_json(target_content, source_content, merge_strategy)
                else:
                    # Fall back to simple replacement for other file types
                    logger.warning(f"Unsupported merge for {source_ext} -> {target_ext}, using replacement")
                    return source_content

            else:
                raise ValueError(f"Unknown action kind: {action_kind}")

        except Exception as e:
            raise TransactionError(
                f"Content transformation failed for {source_path}: {e}",
                "yaml_ops",
                "transform_content",
            ) from e

    def validate_yaml(self, content: str) -> List[str]:
        """Validate YAML content and return errors.

        Args:
            content: YAML content to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        try:
            yaml.safe_load(content)
        except yaml.YAMLError as e:
            errors.append(f"Invalid YAML: {e}")
        except Exception as e:
            errors.append(f"YAML validation error: {e}")

        return errors

    def validate_json(self, content: str) -> List[str]:
        """Validate JSON content and return errors.

        Args:
            content: JSON content to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        try:
            json.loads(content)
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON: {e}")
        except Exception as e:
            errors.append(f"JSON validation error: {e}")

        return errors

    def extract_variables(self, content: str, extract_format: str = "yaml") -> Dict[str, Any]:
        """Extract variables from content for template processing.

        Args:
            content: Content to extract variables from
            extract_format: Format of content ('yaml', 'json', 'env')

        Returns:
            Dictionary of extracted variables

        Raises:
            TransactionError: If extraction fails
        """
        try:
            if extract_format == "yaml":
                return yaml.safe_load(content) or {}
            elif extract_format == "json":
                return json.loads(content) if content.strip() else {}
            elif extract_format == "env":
                return self._parse_env_format(content)
            else:
                raise ValueError(f"Unknown extract format: {extract_format}")

        except Exception as e:
            raise TransactionError(
                f"Variable extraction failed: {e}",
                "yaml_ops",
                "extract_variables",
            ) from e

    def _deep_merge(self, base: Any, overlay: Any) -> Any:
        """Recursively merge two data structures."""
        if isinstance(base, dict) and isinstance(overlay, dict):
            result = base.copy()
            for key, value in overlay.items():
                if key in result:
                    result[key] = self._deep_merge(result[key], value)
                else:
                    result[key] = value
            return result
        elif isinstance(base, list) and isinstance(overlay, list):
            # For lists, append unique items
            result = base.copy()
            for item in overlay:
                if item not in result:
                    result.append(item)
            return result
        else:
            # For scalars, overlay wins
            return overlay

    def _process_simple_template(self, content: str, variables: Dict[str, Any]) -> str:
        """Process template using simple variable substitution."""
        result = content

        # Replace {{variable}} patterns
        for key, value in variables.items():
            pattern = r'\{\{\s*' + re.escape(key) + r'\s*\}\}'
            result = re.sub(pattern, str(value), result)

        return result

    def _process_jinja2_template(self, content: str, variables: Dict[str, Any]) -> str:
        """Process template using Jinja2 (if available)."""
        try:
            import jinja2

            template = jinja2.Template(content)
            return template.render(**variables)

        except ImportError:
            logger.warning("Jinja2 not available, falling back to simple template processing")
            return self._process_simple_template(content, variables)
        except Exception as e:
            raise TransactionError(
                f"Jinja2 template processing failed: {e}",
                "yaml_ops",
                "jinja2_template",
            ) from e

    def _parse_env_format(self, content: str) -> Dict[str, str]:
        """Parse environment variable format (KEY=value)."""
        variables = {}

        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"\'')  # Remove quotes
                variables[key] = value

        return variables

    def get_content_type(self, file_path: Path) -> str:
        """Determine content type from file extension.

        Args:
            file_path: Path to file

        Returns:
            Content type ('yaml', 'json', 'template', 'text')
        """
        suffix = file_path.suffix.lower()

        if suffix in YAML_EXTENSIONS:
            return "yaml"
        elif suffix in JSON_EXTENSIONS:
            return "json"
        elif suffix in TEMPLATE_EXTENSIONS:
            return "template"
        else:
            return "text"

    def is_mergeable(self, source_path: Path, target_path: Path) -> bool:
        """Check if two files can be merged.

        Args:
            source_path: Source file path
            target_path: Target file path

        Returns:
            True if files can be merged, False otherwise
        """
        source_type = self.get_content_type(source_path)
        target_type = self.get_content_type(target_path)

        # Both must be the same mergeable type
        return (source_type == target_type and
                source_type in ("yaml", "json"))

    def validate_receipt_format(self, receipt_data: Dict[str, Any]) -> List[str]:
        """Validate receipt format and return errors.

        Args:
            receipt_data: Receipt data dictionary to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Required fields
        required_fields = {
            'component_id': str,
            'installed_at': str,
            'manifest_hash': str,
            'files': list
        }

        for field, field_type in required_fields.items():
            if field not in receipt_data:
                errors.append(f"Missing required field: {field}")
            elif not isinstance(receipt_data[field], field_type):
                errors.append(f"Field '{field}' must be of type {field_type.__name__}")

        # Validate component_id is not empty
        if 'component_id' in receipt_data:
            if not receipt_data['component_id'].strip():
                errors.append("component_id cannot be empty")

        # Validate manifest_hash format (should be SHA256 hex)
        if 'manifest_hash' in receipt_data:
            manifest_hash = receipt_data['manifest_hash']
            if not isinstance(manifest_hash, str) or len(manifest_hash) != 64:
                errors.append("manifest_hash must be 64-character SHA256 hex string")
            elif not all(c in '0123456789abcdef' for c in manifest_hash.lower()):
                errors.append("manifest_hash contains invalid characters")

        # Validate installed_at timestamp format
        if 'installed_at' in receipt_data:
            try:
                from datetime import datetime
                datetime.fromisoformat(receipt_data['installed_at'].replace('Z', '+00:00'))
            except ValueError:
                errors.append("installed_at must be valid ISO timestamp")

        # Validate files array
        if 'files' in receipt_data and isinstance(receipt_data['files'], list):
            for i, file_action in enumerate(receipt_data['files']):
                if not isinstance(file_action, dict):
                    errors.append(f"files[{i}] must be an object")
                    continue

                # Check required file action fields
                required_file_fields = ['target_path', 'action_type', 'content_hash']
                for field in required_file_fields:
                    if field not in file_action:
                        errors.append(f"files[{i}] missing required field: {field}")

                # Validate action_type
                if 'action_type' in file_action:
                    valid_actions = {'copy', 'template', 'mkdir'}
                    if file_action['action_type'] not in valid_actions:
                        errors.append(f"files[{i}] invalid action_type: {file_action['action_type']}")

        # Validate metadata if present
        if 'metadata' in receipt_data and receipt_data['metadata'] is not None:
            if not isinstance(receipt_data['metadata'], dict):
                errors.append("metadata must be an object or null")

        return errors

    def render_template(self, template_path: str, variables: Dict[str, Any]) -> str:
        """Render template file with variables (adapter interface for backwards compatibility).

        Args:
            template_path: Path to template file
            variables: Variables for substitution

        Returns:
            Rendered content

        Raises:
            TransactionError: If template rendering fails
        """
        try:
            template_content = Path(template_path).read_text(encoding="utf-8")
            return self.process_template(template_content, variables)
        except Exception as e:
            raise TransactionError(
                f"Template rendering failed for {template_path}: {e}",
                "yaml_ops",
                "render_template",
            ) from e

    def merge_configuration(
        self,
        base_config_path: Path,
        overlay_configs: List[Path],
        output_format: str = "yaml",
        merge_strategy: str = "deep"
    ) -> str:
        """Merge multiple configuration files into a single output.

        Args:
            base_config_path: Base configuration file
            overlay_configs: List of overlay configuration files
            output_format: Output format ('yaml' or 'json')
            merge_strategy: Merge strategy ('deep', 'shallow', 'replace')

        Returns:
            Merged configuration content

        Raises:
            TransactionError: If merge operation fails
        """
        try:
            # Load base configuration
            if base_config_path.exists():
                base_content = base_config_path.read_text(encoding="utf-8")
                base_type = self.get_content_type(base_config_path)

                if base_type == "yaml":
                    merged_data = yaml.safe_load(base_content) or {}
                elif base_type == "json":
                    merged_data = json.loads(base_content) if base_content.strip() else {}
                else:
                    raise ValueError(f"Unsupported base config format: {base_type}")
            else:
                merged_data = {}

            # Apply overlay configurations
            for overlay_path in overlay_configs:
                if not overlay_path.exists():
                    logger.warning(f"Overlay config not found: {overlay_path}")
                    continue

                overlay_content = overlay_path.read_text(encoding="utf-8")
                overlay_type = self.get_content_type(overlay_path)

                if overlay_type == "yaml":
                    overlay_data = yaml.safe_load(overlay_content) or {}
                elif overlay_type == "json":
                    overlay_data = json.loads(overlay_content) if overlay_content.strip() else {}
                else:
                    logger.warning(f"Unsupported overlay format: {overlay_type} for {overlay_path}")
                    continue

                # Merge overlay into result
                if merge_strategy == "replace":
                    merged_data = overlay_data
                elif merge_strategy == "shallow":
                    merged_data = {**merged_data, **overlay_data}
                else:  # deep merge
                    merged_data = self._deep_merge(merged_data, overlay_data)

            # Format output
            if output_format == "json":
                return json.dumps(merged_data, indent=2, sort_keys=True, ensure_ascii=False)
            else:  # yaml
                return yaml.dump(
                    merged_data,
                    default_flow_style=False,
                    sort_keys=False,
                    allow_unicode=True,
                )

        except Exception as e:
            raise TransactionError(
                f"Configuration merge failed: {e}",
                "yaml_ops",
                "merge_configuration",
            ) from e

    def validate_envelope_format(self, envelope_data: Dict[str, Any]) -> List[str]:
        """Validate Copilot envelope format and return errors.

        Args:
            envelope_data: Envelope data dictionary to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Required envelope fields
        required_fields = ['discovery', 'plan', 'changes', 'validation']

        for field in required_fields:
            if field not in envelope_data:
                errors.append(f"Missing required envelope field: {field}")

        # Validate discovery section
        if 'discovery' in envelope_data:
            discovery = envelope_data['discovery']
            if not isinstance(discovery, list):
                errors.append("discovery must be an array")
            else:
                for i, item in enumerate(discovery):
                    if not isinstance(item, dict):
                        errors.append(f"discovery[{i}] must be an object")
                        continue
                    for req_field in ['path', 'evidence', 'why']:
                        if req_field not in item:
                            errors.append(f"discovery[{i}] missing field: {req_field}")

        # Validate plan section
        if 'plan' in envelope_data:
            plan = envelope_data['plan']
            if not isinstance(plan, list):
                errors.append("plan must be an array")

        # Validate changes section
        if 'changes' in envelope_data:
            changes = envelope_data['changes']
            if not isinstance(changes, list):
                errors.append("changes must be an array")
            else:
                for i, change in enumerate(changes):
                    if not isinstance(change, dict):
                        errors.append(f"changes[{i}] must be an object")
                        continue
                    if 'path' not in change:
                        errors.append(f"changes[{i}] missing required field: path")

        # Validate validation section
        if 'validation' in envelope_data:
            validation = envelope_data['validation']
            if not isinstance(validation, dict):
                errors.append("validation must be an object")

        return errors
        """Validate Copilot envelope format and return errors.

        Args:
            envelope_data: Envelope data dictionary to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Required envelope fields
        required_fields = ['discovery', 'plan', 'changes', 'validation']

        for field in required_fields:
            if field not in envelope_data:
                errors.append(f"Missing required envelope field: {field}")

        # Validate discovery section
        if 'discovery' in envelope_data:
            discovery = envelope_data['discovery']
            if not isinstance(discovery, list):
                errors.append("discovery must be an array")
            else:
                for i, item in enumerate(discovery):
                    if not isinstance(item, dict):
                        errors.append(f"discovery[{i}] must be an object")
                        continue
                    for req_field in ['path', 'evidence', 'why']:
                        if req_field not in item:
                            errors.append(f"discovery[{i}] missing field: {req_field}")

        # Validate plan section
        if 'plan' in envelope_data:
            plan = envelope_data['plan']
            if not isinstance(plan, list):
                errors.append("plan must be an array")

        # Validate changes section
        if 'changes' in envelope_data:
            changes = envelope_data['changes']
            if not isinstance(changes, list):
                errors.append("changes must be an array")
            else:
                for i, change in enumerate(changes):
                    if not isinstance(change, dict):
                        errors.append(f"changes[{i}] must be an object")
                        continue
                    if 'path' not in change:
                        errors.append(f"changes[{i}] missing required field: path")

        # Validate validation section
        if 'validation' in envelope_data:
            validation = envelope_data['validation']
            if not isinstance(validation, dict):
                errors.append("validation must be an object")

        return errors
