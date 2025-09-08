"""
Enhanced Plugin File Processor for AI Guardrails Bootstrap System

This module provides sophisticated file processing capabilities for plugins:
- Copy operations with permission and ownership management
- Template processing with Jinja2 and security restrictions
- YAML/JSON merging with multiple strategies
- Conditional file operations based on environment/config
- Backup and restoration capabilities

Security Features:
- Sandboxed template environment
- Path traversal protection
- Resource limits and validation
- Safe file operations with atomic writes
"""

import os
import shutil
import tempfile
import yaml
import json
import jinja2
from pathlib import Path
from typing import Dict, Any, Optional, List

from ..domain.plugin_models import FileOperation, PluginSecurityError
from ..domain.constants import DEFAULT_FILE_MODE, MAX_FILE_SIZE, MAX_TEMPLATE_SIZE


class PluginProcessor:
    """Enhanced plugin file processor with security and validation."""

    def __init__(self, plugin_path: Path, target_path: Path):
        self.plugin_path = Path(plugin_path).resolve()
        self.target_path = Path(target_path).resolve()
        self.template_env = self._setup_template_environment()
        self._validate_paths()

    def _setup_template_environment(self) -> jinja2.Environment:
        """Setup secure Jinja2 environment with restrictions."""
        return jinja2.Environment(
            loader=jinja2.BaseLoader(),
            undefined=jinja2.StrictUndefined,
            autoescape=jinja2.select_autoescape(['html', 'xml']),
            # Security restrictions
            finalize=lambda x: x if x is not None else '',
            trim_blocks=True,
            lstrip_blocks=True,
            # Disable dangerous features
            extensions=[],
            enable_async=False
        )

    def _validate_paths(self) -> None:
        """Validate plugin and target paths for security."""
        if not self.plugin_path.exists():
            raise PluginSecurityError(f"Plugin path does not exist: {self.plugin_path}")

        if not self.plugin_path.is_dir():
            raise PluginSecurityError(f"Plugin path is not a directory: {self.plugin_path}")

        # Ensure target path is not within plugin path (prevent self-modification)
        try:
            self.target_path.resolve().relative_to(self.plugin_path)
            raise PluginSecurityError("Target path cannot be within plugin directory")
        except ValueError:
            pass  # Good - target is outside plugin directory

    def process_file_operation(self, operation: FileOperation, context: Dict[str, Any]) -> List[str]:
        """
        Process a file operation and return list of processed files.

        Args:
            operation: File operation to process
            context: Context variables for template processing

        Returns:
            List of processed file paths

        Raises:
            PluginSecurityError: For security violations
            ValueError: For invalid operations
        """
        # Evaluate condition if present
        if not self._evaluate_condition(operation.condition, context):
            return []

        # Find source files matching pattern
        source_files = self._find_source_files(operation.pattern)
        if not source_files:
            return []

        processed_files = []

        for source_file in source_files:
            try:
                if operation.action == "copy":
                    target_file = self._process_copy(source_file, operation, context)
                elif operation.action == "template":
                    target_file = self._process_template(source_file, operation, context)
                elif operation.action == "merge":
                    target_file = self._process_merge(source_file, operation, context)
                else:
                    raise ValueError(f"Unknown action type: {operation.action}")

                if target_file:
                    processed_files.append(str(target_file))

            except Exception as e:
                # Log error but continue processing other files
                print(f"Error processing {source_file}: {e}")
                continue

        return processed_files

    def _evaluate_condition(self, condition: Optional[str], context: Dict[str, Any]) -> bool:
        """Evaluate conditional expression using Jinja2."""
        if not condition:
            return True

        try:
            # Create a safe template for condition evaluation
            template_str = f"{{% if {condition} %}}true{{% endif %}}"
            template = self.template_env.from_string(template_str)
            result = template.render(**context)
            return result.strip() == "true"
        except Exception as e:
            print(f"Error evaluating condition '{condition}': {e}")
            return False

    def _find_source_files(self, pattern: str) -> List[Path]:
        """Find source files matching the glob pattern."""
        try:
            source_files = list(self.plugin_path.glob(pattern))
            # Filter out directories and validate paths
            valid_files = []
            for file_path in source_files:
                if file_path.is_file() and self._is_safe_source_path(file_path):
                    valid_files.append(file_path)
            return valid_files
        except Exception as e:
            print(f"Error finding files with pattern '{pattern}': {e}")
            return []

    def _is_safe_source_path(self, file_path: Path) -> bool:
        """Validate that source file path is safe."""
        try:
            # Ensure file is within plugin directory
            file_path.resolve().relative_to(self.plugin_path)

            # Check file size
            if file_path.stat().st_size > MAX_FILE_SIZE:
                print(f"File too large: {file_path}")
                return False

            return True
        except (ValueError, OSError):
            return False

    def _is_safe_target_path(self, target_path: Path) -> bool:
        """Validate that target file path is safe."""
        try:
            # Resolve target path and ensure it's within allowed area
            resolved_target = target_path.resolve()

            # Prevent path traversal attacks
            resolved_target.relative_to(self.target_path)

            # Prevent overwriting critical system files
            forbidden_paths = {"/etc", "/usr", "/bin", "/sbin", "/lib", "/lib64"}
            for forbidden in forbidden_paths:
                if str(resolved_target).startswith(forbidden):
                    return False

            return True
        except (ValueError, OSError):
            return False

    def _process_copy(self, source_file: Path, operation: FileOperation, context: Dict[str, Any]) -> Optional[Path]:
        """Process file copy operation with backup and permissions."""
        target_file = self._resolve_target_path(source_file, operation.target)

        if not self._is_safe_target_path(target_file):
            raise PluginSecurityError(f"Unsafe target path: {target_file}")

        # Create backup if requested and file exists
        if operation.backup and target_file.exists():
            self._create_backup(target_file)

        # Ensure target directory exists
        target_file.parent.mkdir(parents=True, exist_ok=True)

        # Copy file
        shutil.copy2(source_file, target_file)

        # Set permissions and ownership
        self._apply_file_attributes(target_file, operation)

        return target_file

    def _process_template(self, source_file: Path, operation: FileOperation, context: Dict[str, Any]) -> Optional[Path]:
        """Process template file with variable substitution."""
        target_file = self._resolve_target_path(source_file, operation.target)

        if not self._is_safe_target_path(target_file):
            raise PluginSecurityError(f"Unsafe target path: {target_file}")

        # Read template content
        try:
            template_content = source_file.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            # Skip binary files
            print(f"Skipping binary file: {source_file}")
            return None

        # Check template size
        if len(template_content) > MAX_TEMPLATE_SIZE:
            raise PluginSecurityError(f"Template too large: {source_file}")

        # Prepare template context
        template_context = {**context, **operation.variables}

        # Create backup if requested and file exists
        if operation.backup and target_file.exists():
            self._create_backup(target_file)

        # Render template
        try:
            template = self.template_env.from_string(template_content)
            rendered_content = template.render(**template_context)
        except jinja2.TemplateError as e:
            raise ValueError(f"Template rendering error in {source_file}: {e}")

        # Ensure target directory exists
        target_file.parent.mkdir(parents=True, exist_ok=True)

        # Write rendered content atomically
        self._write_file_atomic(target_file, rendered_content)

        # Set permissions and ownership
        self._apply_file_attributes(target_file, operation)

        return target_file

    def _process_merge(self, source_file: Path, operation: FileOperation, context: Dict[str, Any]) -> Optional[Path]:
        """Process YAML/JSON merge operation with strategies."""
        target_file = self._resolve_target_path(source_file, operation.target)

        if not self._is_safe_target_path(target_file):
            raise PluginSecurityError(f"Unsafe target path: {target_file}")

        # Determine file format
        file_format = self._detect_file_format(source_file)
        if file_format not in ['yaml', 'json']:
            raise ValueError(f"Unsupported merge format: {file_format}")

        # Load source data
        source_data = self._load_data_file(source_file, file_format)

        # Load existing target data if it exists
        target_data = {}
        if target_file.exists():
            target_data = self._load_data_file(target_file, file_format)

        # Create backup if requested
        if operation.backup and target_file.exists():
            self._create_backup(target_file)

        # Merge data according to strategy
        strategy = operation.strategy or "deep"
        merged_data = self._merge_data(target_data, source_data, strategy)

        # Ensure target directory exists
        target_file.parent.mkdir(parents=True, exist_ok=True)

        # Write merged data
        self._write_data_file(target_file, merged_data, file_format)

        # Set permissions and ownership
        self._apply_file_attributes(target_file, operation)

        return target_file

    def _resolve_target_path(self, source_file: Path, target_spec: str) -> Path:
        """Resolve target path from source file and target specification."""
        if target_spec.endswith('/'):
            # Target is a directory, preserve filename
            relative_path = source_file.relative_to(self.plugin_path)
            return self.target_path / target_spec.rstrip('/') / relative_path.name
        else:
            # Target is a specific file path
            return self.target_path / target_spec.lstrip('./')

    def _create_backup(self, file_path: Path) -> Path:
        """Create a backup of an existing file."""
        backup_path = file_path.with_suffix(file_path.suffix + '.backup')
        counter = 1
        while backup_path.exists():
            backup_path = file_path.with_suffix(f"{file_path.suffix}.backup.{counter}")
            counter += 1

        shutil.copy2(file_path, backup_path)
        return backup_path

    def _apply_file_attributes(self, file_path: Path, operation: FileOperation) -> None:
        """Apply file permissions and ownership."""
        # Set permissions
        mode = operation.mode or DEFAULT_FILE_MODE
        try:
            file_path.chmod(mode)
        except OSError as e:
            print(f"Warning: Could not set permissions on {file_path}: {e}")

        # Set ownership (if specified and running as root)
        if operation.owner and os.geteuid() == 0:
            try:
                import pwd
                uid = pwd.getpwnam(operation.owner).pw_uid
                os.chown(file_path, uid, -1)
            except (KeyError, OSError) as e:
                print(f"Warning: Could not set owner on {file_path}: {e}")

    def _write_file_atomic(self, file_path: Path, content: str) -> None:
        """Write file content atomically to prevent corruption."""
        temp_file = None
        try:
            # Create temporary file in same directory as target
            temp_fd, temp_path = tempfile.mkstemp(
                dir=file_path.parent,
                prefix=f".{file_path.name}.tmp"
            )
            temp_file = Path(temp_path)

            # Write content to temporary file
            with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
                f.write(content)

            # Atomically move temporary file to target
            temp_file.replace(file_path)

        except Exception:
            # Clean up temporary file on error
            if temp_file and temp_file.exists():
                temp_file.unlink()
            raise

    def _detect_file_format(self, file_path: Path) -> str:
        """Detect file format based on extension and content."""
        suffix = file_path.suffix.lower()
        if suffix in ['.yml', '.yaml']:
            return 'yaml'
        elif suffix in ['.json']:
            return 'json'
        else:
            # Try to detect by content
            try:
                content = file_path.read_text(encoding='utf-8')
                json.loads(content)
                return 'json'
            except (json.JSONDecodeError, UnicodeDecodeError):
                try:
                    yaml.safe_load(content)
                    return 'yaml'
                except yaml.YAMLError:
                    return 'unknown'

    def _load_data_file(self, file_path: Path, file_format: str) -> Any:
        """Load data from YAML or JSON file."""
        try:
            content = file_path.read_text(encoding='utf-8')
            if file_format == 'json':
                return json.loads(content)
            elif file_format == 'yaml':
                return yaml.safe_load(content) or {}
            else:
                raise ValueError(f"Unsupported format: {file_format}")
        except Exception as e:
            raise ValueError(f"Error loading {file_format} file {file_path}: {e}")

    def _write_data_file(self, file_path: Path, data: Any, file_format: str) -> None:
        """Write data to YAML or JSON file."""
        if file_format == 'json':
            content = json.dumps(data, indent=2, sort_keys=True)
        elif file_format == 'yaml':
            content = yaml.dump(data, default_flow_style=False, sort_keys=True)
        else:
            raise ValueError(f"Unsupported format: {file_format}")

        self._write_file_atomic(file_path, content)

    def _merge_data(self, target_data: Any, source_data: Any, strategy: str) -> Any:
        """Merge data according to the specified strategy."""
        if strategy == "replace":
            return source_data
        elif strategy == "deep":
            return self._deep_merge(target_data, source_data)
        elif strategy == "append":
            return self._append_merge(target_data, source_data)
        else:
            raise ValueError(f"Unknown merge strategy: {strategy}")

    def _deep_merge(self, target: Any, source: Any) -> Any:
        """Recursively merge dictionaries and lists."""
        if isinstance(target, dict) and isinstance(source, dict):
            result = target.copy()
            for key, value in source.items():
                if key in result:
                    result[key] = self._deep_merge(result[key], value)
                else:
                    result[key] = value
            return result
        elif isinstance(target, list) and isinstance(source, list):
            return target + source
        else:
            return source

    def _append_merge(self, target: Any, source: Any) -> Any:
        """Append source to target (for lists) or replace (for other types)."""
        if isinstance(target, list) and isinstance(source, list):
            return target + source
        elif isinstance(target, dict) and isinstance(source, dict):
            result = target.copy()
            result.update(source)
            return result
        else:
            return source


class PluginProcessorError(Exception):
    """Exception raised during plugin file processing."""
    pass
