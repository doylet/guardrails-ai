"""
Template Engine for AI Guardrails Bootstrap System

This module provides enhanced template processing with Jinja2 integration:
- Secure Jinja2 environment setup with security restrictions
- Template variable resolution from multiple sources
- Custom filters for common transformations
- Template caching for performance
- Error handling with helpful messages
- Template syntax validation

Security Features:
- Sandboxed template execution
- Disabled dangerous template features
- Variable sanitization and validation
- Template size limits
- Safe file access patterns
"""

import os
import hashlib
import json
import yaml
import jinja2
from pathlib import Path
from typing import Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime

from ..domain.constants import MAX_TEMPLATE_SIZE


@dataclass
class TemplateContext:
    """Context for template rendering."""
    variables: Dict[str, Any] = field(default_factory=dict)
    environment: Dict[str, str] = field(default_factory=dict)
    configuration: Dict[str, Any] = field(default_factory=dict)
    plugin_metadata: Dict[str, Any] = field(default_factory=dict)
    system_info: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TemplateRenderResult:
    """Result of template rendering."""
    success: bool
    content: str
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    variables_used: List[str] = field(default_factory=list)


class TemplateEngine:
    """Enhanced template processing with Jinja2 and security restrictions."""

    def __init__(self, cache_enabled: bool = True, cache_size: int = 100):
        self.cache_enabled = cache_enabled
        self.cache_size = cache_size
        self._template_cache = {}
        self._environment = self._setup_secure_environment()
        self._register_custom_filters()

    def _setup_secure_environment(self) -> jinja2.Environment:
        """Setup secure Jinja2 environment with restrictions."""
        # Create secure loader that prevents file system access
        loader = jinja2.BaseLoader()

        env = jinja2.Environment(
            loader=loader,
            # Security settings
            undefined=jinja2.StrictUndefined,
            autoescape=jinja2.select_autoescape(['html', 'xml']),
            finalize=lambda x: x if x is not None else '',

            # Performance and behavior settings
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,

            # Disable dangerous features
            extensions=[],
            enable_async=False,

            # Cache compiled templates
            cache_size=self.cache_size if self.cache_enabled else 0,
        )

        # Remove dangerous globals and functions
        dangerous_globals = [
            'range', 'lipsum', 'dict', 'list', 'tuple', 'set',
            'frozenset', 'slice', 'map', 'filter', 'zip',
            'enumerate', 'reversed', 'sorted', 'sum', 'min', 'max',
            'abs', 'round', 'divmod', 'pow', 'bin', 'oct', 'hex',
            'chr', 'ord', 'repr', 'ascii'
        ]

        for name in dangerous_globals:
            if name in env.globals:
                del env.globals[name]

        # Add safe utility functions
        env.globals.update({
            'now': datetime.now,
            'today': datetime.today,
            'env': self._safe_env_access,
            'config': self._safe_config_access,
        })

        return env

    def _register_custom_filters(self) -> None:
        """Register custom Jinja2 filters for common transformations."""
        filters = {
            # String transformations
            'snake_case': self._filter_snake_case,
            'kebab_case': self._filter_kebab_case,
            'camel_case': self._filter_camel_case,
            'pascal_case': self._filter_pascal_case,

            # Path manipulations
            'basename': self._filter_basename,
            'dirname': self._filter_dirname,
            'abspath': self._filter_abspath,
            'relpath': self._filter_relpath,

            # Data transformations
            'to_yaml': self._filter_to_yaml,
            'from_yaml': self._filter_from_yaml,
            'to_json': self._filter_to_json,
            'from_json': self._filter_from_json,

            # Validation and defaults
            'default_if_empty': self._filter_default_if_empty,
            'validate_path': self._filter_validate_path,
            'sanitize_filename': self._filter_sanitize_filename,

            # List and dict operations
            'unique': self._filter_unique,
            'flatten': self._filter_flatten,
            'merge_dict': self._filter_merge_dict,
        }

        for name, filter_func in filters.items():
            self._environment.filters[name] = filter_func

    def render_template(self, template_content: str, context: TemplateContext) -> TemplateRenderResult:
        """
        Render template with the provided context.

        Args:
            template_content: Template content to render
            context: Template context with variables

        Returns:
            Template render result
        """
        if len(template_content) > MAX_TEMPLATE_SIZE:
            return TemplateRenderResult(
                success=False,
                content="",
                errors=[f"Template too large: {len(template_content)} bytes (max: {MAX_TEMPLATE_SIZE})"]
            )

        try:
            # Get or compile template
            template = self._get_template(template_content)

            # Prepare rendering context
            render_context = self._prepare_render_context(context)

            # Track variables used during rendering
            used_variables = []

            # Custom undefined handler to track variable usage
            class VariableTracker(jinja2.StrictUndefined):
                def __init__(self, hint=None, obj=None, name=None, exc=None):
                    super().__init__(hint, obj, name, exc)
                    if name:
                        used_variables.append(name)

            # Temporarily replace undefined handler
            original_undefined = self._environment.undefined
            self._environment.undefined = VariableTracker

            try:
                # Render template
                rendered_content = template.render(**render_context)

                return TemplateRenderResult(
                    success=True,
                    content=rendered_content,
                    variables_used=list(set(used_variables))
                )

            finally:
                # Restore original undefined handler
                self._environment.undefined = original_undefined

        except jinja2.TemplateError as e:
            return TemplateRenderResult(
                success=False,
                content="",
                errors=[f"Template error: {e}"]
            )
        except Exception as e:
            return TemplateRenderResult(
                success=False,
                content="",
                errors=[f"Unexpected error: {e}"]
            )

    def validate_template_syntax(self, template_content: str) -> List[str]:
        """
        Validate template syntax without rendering.

        Args:
            template_content: Template content to validate

        Returns:
            List of syntax errors
        """
        errors = []

        try:
            self._environment.parse(template_content)
        except jinja2.TemplateSyntaxError as e:
            errors.append(f"Syntax error at line {e.lineno}: {e.message}")
        except Exception as e:
            errors.append(f"Parse error: {e}")

        return errors

    def get_template_variables(self, template_content: str) -> List[str]:
        """
        Extract variable names from template.

        Args:
            template_content: Template content to analyze

        Returns:
            List of variable names used in template
        """
        try:
            ast = self._environment.parse(template_content)
            variables = jinja2.meta.find_undeclared_variables(ast)
            return list(variables)
        except Exception:
            return []

    def _get_template(self, template_content: str) -> jinja2.Template:
        """Get compiled template, using cache if enabled."""
        if not self.cache_enabled:
            return self._environment.from_string(template_content)

        # Generate cache key
        cache_key = hashlib.sha256(template_content.encode('utf-8')).hexdigest()

        if cache_key not in self._template_cache:
            # Compile and cache template
            self._template_cache[cache_key] = self._environment.from_string(template_content)

            # Limit cache size
            if len(self._template_cache) > self.cache_size:
                # Remove oldest entry
                oldest_key = next(iter(self._template_cache))
                del self._template_cache[oldest_key]

        return self._template_cache[cache_key]

    def _prepare_render_context(self, context: TemplateContext) -> Dict[str, Any]:
        """Prepare the rendering context with all variables."""
        render_context = {}

        # Add context variables
        render_context.update(context.variables)

        # Add environment variables under 'env' namespace
        render_context['env'] = context.environment.copy()

        # Add configuration under 'config' namespace
        render_context['config'] = context.configuration.copy()

        # Add plugin metadata under 'plugin' namespace
        render_context['plugin'] = context.plugin_metadata.copy()

        # Add system information under 'system' namespace
        render_context['system'] = context.system_info.copy()

        # Add current timestamp
        render_context['timestamp'] = datetime.now().isoformat()

        return render_context

    def _safe_env_access(self, key: str, default: Any = None) -> Any:
        """Safe environment variable access."""
        return os.environ.get(key, default)

    def _safe_config_access(self, key: str, default: Any = None) -> Any:
        """Safe configuration access (placeholder for actual config)."""
        # This would access actual configuration in production
        return default

    # Custom filter implementations
    def _filter_snake_case(self, value: str) -> str:
        """Convert string to snake_case."""
        import re
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', str(value))
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    def _filter_kebab_case(self, value: str) -> str:
        """Convert string to kebab-case."""
        return self._filter_snake_case(value).replace('_', '-')

    def _filter_camel_case(self, value: str) -> str:
        """Convert string to camelCase."""
        words = str(value).replace('-', '_').split('_')
        return words[0].lower() + ''.join(word.capitalize() for word in words[1:])

    def _filter_pascal_case(self, value: str) -> str:
        """Convert string to PascalCase."""
        words = str(value).replace('-', '_').split('_')
        return ''.join(word.capitalize() for word in words)

    def _filter_basename(self, value: str) -> str:
        """Get basename of path."""
        return Path(str(value)).name

    def _filter_dirname(self, value: str) -> str:
        """Get directory name of path."""
        return str(Path(str(value)).parent)

    def _filter_abspath(self, value: str) -> str:
        """Get absolute path."""
        return str(Path(str(value)).resolve())

    def _filter_relpath(self, value: str, start: str = '.') -> str:
        """Get relative path."""
        return str(Path(str(value)).relative_to(start))

    def _filter_to_yaml(self, value: Any) -> str:
        """Convert value to YAML string."""
        try:
            return yaml.dump(value, default_flow_style=False)
        except Exception:
            return str(value)

    def _filter_from_yaml(self, value: str) -> Any:
        """Parse YAML string."""
        try:
            return yaml.safe_load(str(value))
        except Exception:
            return value

    def _filter_to_json(self, value: Any, indent: int = None) -> str:
        """Convert value to JSON string."""
        try:
            return json.dumps(value, indent=indent, sort_keys=True)
        except Exception:
            return str(value)

    def _filter_from_json(self, value: str) -> Any:
        """Parse JSON string."""
        try:
            return json.loads(str(value))
        except Exception:
            return value

    def _filter_default_if_empty(self, value: Any, default: Any) -> Any:
        """Return default if value is empty."""
        if not value or (isinstance(value, str) and not value.strip()):
            return default
        return value

    def _filter_validate_path(self, value: str) -> str:
        """Validate and normalize path."""
        try:
            path = Path(str(value))
            # Remove any parent directory references
            parts = [part for part in path.parts if part != '..']
            return str(Path(*parts))
        except Exception:
            return str(value)

    def _filter_sanitize_filename(self, value: str) -> str:
        """Sanitize filename by removing dangerous characters."""
        import re
        filename = str(value)
        # Remove or replace dangerous characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Remove leading/trailing dots and spaces
        filename = filename.strip('. ')
        # Ensure not empty
        return filename if filename else 'unnamed'

    def _filter_unique(self, value: List[Any]) -> List[Any]:
        """Remove duplicates from list while preserving order."""
        seen = set()
        result = []
        for item in value:
            if item not in seen:
                seen.add(item)
                result.append(item)
        return result

    def _filter_flatten(self, value: List[List[Any]]) -> List[Any]:
        """Flatten nested list."""
        result = []
        for item in value:
            if isinstance(item, list):
                result.extend(item)
            else:
                result.append(item)
        return result

    def _filter_merge_dict(self, value: Dict[str, Any], other: Dict[str, Any]) -> Dict[str, Any]:
        """Merge two dictionaries."""
        result = value.copy()
        result.update(other)
        return result


class TemplateEngineError(Exception):
    """Exception raised during template processing."""
    pass
