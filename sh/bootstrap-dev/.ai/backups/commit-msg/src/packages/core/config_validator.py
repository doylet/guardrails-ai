"""
Configuration Validator for AI Guardrails Bootstrap System

This module provides JSON Schema validation for plugin configuration:
- Configuration merging and inheritance
- Default value application
- Environment-specific configuration support
- Configuration documentation generation
- IDE integration support (schema export)
- Comprehensive validation with helpful error messages

Features:
- JSON Schema Draft 7 support
- Custom validation rules
- Configuration inheritance and merging
- Environment variable substitution
- Type coercion and validation
- Error reporting with suggestions
"""

import json
import jsonschema
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from copy import deepcopy

from ..domain.plugin_models import ComponentDefinition


@dataclass
class ValidationError:
    """Configuration validation error."""
    path: str
    message: str
    suggestion: Optional[str] = None
    error_code: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of configuration validation."""
    valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)
    processed_config: Dict[str, Any] = field(default_factory=dict)


class ConfigValidator:
    """Configuration validation with JSON Schema support."""

    def __init__(self):
        self.validator_class = jsonschema.Draft7Validator
        self._schema_cache = {}

    def validate_component_config(self, config: Dict[str, Any],
                                component: ComponentDefinition,
                                environment: Optional[Dict[str, str]] = None) -> ValidationResult:
        """
        Validate component configuration against its schema.

        Args:
            config: Configuration to validate
            component: Component definition with schema
            environment: Environment variables for substitution

        Returns:
            Validation result with errors and processed config
        """
        if not component.config_schema:
            # No schema defined, accept any configuration
            return ValidationResult(
                valid=True,
                processed_config=config.copy()
            )

        # Process environment variable substitution
        processed_config = self._substitute_environment_variables(
            config, environment or {}
        )

        # Apply default values from schema
        processed_config = self._apply_defaults(
            processed_config, component.config_schema
        )

        # Validate against schema
        validation_result = self._validate_against_schema(
            processed_config, component.config_schema, f"component.{component.name}"
        )

        # Add component-specific validations
        validation_result.errors.extend(
            self._validate_component_specific(processed_config, component)
        )

        validation_result.processed_config = processed_config
        return validation_result

    def validate_plugin_config(self, config: Dict[str, Any],
                             components: Dict[str, ComponentDefinition],
                             environment: Optional[Dict[str, str]] = None) -> ValidationResult:
        """
        Validate plugin-level configuration.

        Args:
            config: Plugin configuration to validate
            components: Plugin components with schemas
            environment: Environment variables

        Returns:
            Validation result
        """
        overall_result = ValidationResult(valid=True, processed_config={})

        # Validate each component's configuration
        for component_name, component in components.items():
            component_config = config.get(component_name, {})

            result = self.validate_component_config(
                component_config, component, environment
            )

            # Merge results
            if not result.valid:
                overall_result.valid = False

            overall_result.errors.extend(result.errors)
            overall_result.warnings.extend(result.warnings)
            overall_result.processed_config[component_name] = result.processed_config

        return overall_result

    def merge_configurations(self, base_config: Dict[str, Any],
                           override_config: Dict[str, Any],
                           merge_strategy: str = "deep") -> Dict[str, Any]:
        """
        Merge two configuration dictionaries.

        Args:
            base_config: Base configuration
            override_config: Configuration to merge in
            merge_strategy: Merge strategy (deep, replace, append)

        Returns:
            Merged configuration
        """
        if merge_strategy == "replace":
            return override_config.copy()
        elif merge_strategy == "deep":
            return self._deep_merge(base_config, override_config)
        elif merge_strategy == "append":
            return self._append_merge(base_config, override_config)
        else:
            raise ValueError(f"Unknown merge strategy: {merge_strategy}")

    def generate_config_documentation(self, component: ComponentDefinition) -> str:
        """
        Generate documentation for component configuration.

        Args:
            component: Component definition with schema

        Returns:
            Markdown documentation
        """
        if not component.config_schema:
            return f"## {component.name}\n\nNo configuration options available."

        doc = f"## {component.name}\n\n"
        doc += f"{component.description}\n\n"
        doc += "### Configuration Options\n\n"

        doc += self._generate_schema_documentation(component.config_schema)

        return doc

    def export_json_schema(self, component: ComponentDefinition,
                          output_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Export component configuration schema as JSON Schema.

        Args:
            component: Component definition
            output_path: Optional path to write schema file

        Returns:
            JSON Schema dictionary
        """
        if not component.config_schema:
            schema = {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "title": f"{component.name} Configuration",
                "description": component.description,
                "type": "object",
                "properties": {},
                "additionalProperties": True
            }
        else:
            schema = {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "title": f"{component.name} Configuration",
                "description": component.description,
                **component.config_schema
            }

        if output_path:
            output_path.write_text(json.dumps(schema, indent=2))

        return schema

    def _validate_against_schema(self, config: Dict[str, Any],
                               schema: Dict[str, Any],
                               path_prefix: str = "") -> ValidationResult:
        """Validate configuration against JSON schema."""
        errors = []
        warnings = []

        try:
            # Create validator
            validator = self.validator_class(schema)

            # Validate and collect errors
            for error in validator.iter_errors(config):
                error_path = path_prefix
                if error.absolute_path:
                    error_path += "." + ".".join(str(p) for p in error.absolute_path)

                validation_error = ValidationError(
                    path=error_path,
                    message=error.message,
                    suggestion=self._get_error_suggestion(error)
                )
                errors.append(validation_error)

        except jsonschema.SchemaError as e:
            errors.append(ValidationError(
                path=path_prefix,
                message=f"Invalid schema: {e.message}",
                error_code="INVALID_SCHEMA"
            ))

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    def _substitute_environment_variables(self, config: Dict[str, Any],
                                        environment: Dict[str, str]) -> Dict[str, Any]:
        """Substitute environment variables in configuration."""
        def substitute_value(value):
            if isinstance(value, str):
                # Simple ${VAR} substitution
                import re
                pattern = r'\$\{([^}]+)\}'

                def replacer(match):
                    var_name = match.group(1)
                    default_value = None

                    # Handle ${VAR:default} syntax
                    if ':' in var_name:
                        var_name, default_value = var_name.split(':', 1)

                    return environment.get(var_name, default_value or match.group(0))

                return re.sub(pattern, replacer, value)
            elif isinstance(value, dict):
                return {k: substitute_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [substitute_value(item) for item in value]
            else:
                return value

        return substitute_value(config)

    def _apply_defaults(self, config: Dict[str, Any],
                       schema: Dict[str, Any]) -> Dict[str, Any]:
        """Apply default values from schema to configuration."""
        result = deepcopy(config)

        def apply_defaults_recursive(target: Dict[str, Any],
                                   schema_props: Dict[str, Any],
                                   required: List[str] = None):
            required = required or []

            for prop_name, prop_schema in schema_props.items():
                if prop_name not in target:
                    # Apply default if available
                    if "default" in prop_schema:
                        target[prop_name] = deepcopy(prop_schema["default"])
                    elif prop_name in required:
                        # Required property missing, will be caught by validation
                        pass
                elif isinstance(target[prop_name], dict) and prop_schema.get("type") == "object":
                    # Recursively apply defaults to nested objects
                    nested_props = prop_schema.get("properties", {})
                    nested_required = prop_schema.get("required", [])
                    apply_defaults_recursive(target[prop_name], nested_props, nested_required)

        if "properties" in schema:
            apply_defaults_recursive(result, schema["properties"], schema.get("required", []))

        return result

    def _validate_component_specific(self, config: Dict[str, Any],
                                   component: ComponentDefinition) -> List[ValidationError]:
        """Perform component-specific validation beyond JSON schema."""
        errors = []

        # Example: validate file paths exist
        if "file_paths" in config:
            for path_str in config["file_paths"]:
                try:
                    path = Path(path_str)
                    if not path.exists():
                        errors.append(ValidationError(
                            path=f"component.{component.name}.file_paths",
                            message=f"File path does not exist: {path_str}",
                            suggestion="Check that the file path is correct and the file exists"
                        ))
                except Exception:
                    errors.append(ValidationError(
                        path=f"component.{component.name}.file_paths",
                        message=f"Invalid file path: {path_str}",
                        suggestion="Use a valid file path format"
                    ))

        return errors

    def _get_error_suggestion(self, error: jsonschema.ValidationError) -> Optional[str]:
        """Generate helpful suggestions for validation errors."""
        suggestions = {
            "type": "Check the data type. Expected {expected}, got {actual}.",
            "required": "This field is required. Add the missing property.",
            "additionalProperties": "Remove unexpected properties or check for typos.",
            "enum": "Value must be one of: {allowed_values}",
            "minimum": "Value must be at least {minimum}.",
            "maximum": "Value must be at most {maximum}.",
            "minLength": "Value must be at least {min_length} characters long.",
            "maxLength": "Value must be at most {max_length} characters long.",
            "pattern": "Value must match the pattern: {pattern}",
        }

        validator = error.validator
        if validator in suggestions:
            suggestion = suggestions[validator]

            # Fill in template variables
            if hasattr(error, 'validator_value'):
                suggestion = suggestion.replace("{expected}", str(error.schema.get("type", "unknown")))
                suggestion = suggestion.replace("{minimum}", str(error.validator_value))
                suggestion = suggestion.replace("{maximum}", str(error.validator_value))
                suggestion = suggestion.replace("{min_length}", str(error.validator_value))
                suggestion = suggestion.replace("{max_length}", str(error.validator_value))
                suggestion = suggestion.replace("{pattern}", str(error.validator_value))

                if validator == "enum":
                    suggestion = suggestion.replace("{allowed_values}", ", ".join(map(str, error.validator_value)))

            if hasattr(error, 'instance'):
                actual_type = type(error.instance).__name__
                suggestion = suggestion.replace("{actual}", actual_type)

            return suggestion

        return None

    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries."""
        result = deepcopy(base)

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = deepcopy(value)

        return result

    def _append_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Append merge - concatenate lists and update dictionaries."""
        result = deepcopy(base)

        for key, value in override.items():
            if key in result:
                if isinstance(result[key], list) and isinstance(value, list):
                    result[key] = result[key] + value
                elif isinstance(result[key], dict) and isinstance(value, dict):
                    result[key].update(value)
                else:
                    result[key] = value
            else:
                result[key] = deepcopy(value)

        return result

    def _generate_schema_documentation(self, schema: Dict[str, Any],
                                     level: int = 3) -> str:
        """Generate markdown documentation from JSON schema."""
        doc = ""

        if "properties" not in schema:
            return "No configuration properties defined.\n\n"

        required = set(schema.get("required", []))

        for prop_name, prop_schema in schema["properties"].items():
            required_marker = " *(required)*" if prop_name in required else ""
            doc += f"{'#' * level} `{prop_name}`{required_marker}\n\n"

            # Type information
            prop_type = prop_schema.get("type", "any")
            doc += f"**Type:** `{prop_type}`\n\n"

            # Description
            if "description" in prop_schema:
                doc += f"{prop_schema['description']}\n\n"

            # Default value
            if "default" in prop_schema:
                default_val = json.dumps(prop_schema["default"]) if isinstance(prop_schema["default"], (dict, list)) else str(prop_schema["default"])
                doc += f"**Default:** `{default_val}`\n\n"

            # Constraints
            constraints = []
            if "minimum" in prop_schema:
                constraints.append(f"minimum: {prop_schema['minimum']}")
            if "maximum" in prop_schema:
                constraints.append(f"maximum: {prop_schema['maximum']}")
            if "minLength" in prop_schema:
                constraints.append(f"min length: {prop_schema['minLength']}")
            if "maxLength" in prop_schema:
                constraints.append(f"max length: {prop_schema['maxLength']}")
            if "enum" in prop_schema:
                constraints.append(f"allowed values: {', '.join(map(str, prop_schema['enum']))}")
            if "pattern" in prop_schema:
                constraints.append(f"pattern: `{prop_schema['pattern']}`")

            if constraints:
                doc += f"**Constraints:** {', '.join(constraints)}\n\n"

            # Example
            if "examples" in prop_schema:
                doc += "**Example:**\n```json\n"
                doc += json.dumps(prop_schema["examples"][0], indent=2)
                doc += "\n```\n\n"

        return doc


class ConfigValidatorError(Exception):
    """Exception raised during configuration validation."""
    pass
