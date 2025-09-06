"""Typed exceptions for the AI Guardrails Bootstrap System.

This module defines domain-specific exceptions that provide clear error messages
and structured error information for different failure modes.
"""

from typing import List, Optional


class BootstrapError(Exception):
    """Base exception for all bootstrap system errors.

    Attributes:
        message: Human-readable error description
        error_code: Machine-readable error identifier
        details: Additional error context
    """

    def __init__(
        self,
        message: str,
        error_code: str = "BOOTSTRAP_ERROR",
        details: Optional[dict] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}

    def __str__(self) -> str:
        if self.details:
            detail_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} ({self.error_code}: {detail_str})"
        return f"{self.message} ({self.error_code})"


class ConflictError(BootstrapError):
    """Raised when components have conflicting file paths or capabilities.

    This error occurs during dependency resolution when multiple components
    attempt to manage the same file or provide conflicting capabilities.
    """

    def __init__(
        self,
        message: str,
        conflicting_components: List[str],
        conflicting_paths: Optional[List[str]] = None,
    ) -> None:
        details = {
            "components": conflicting_components,
            "paths": conflicting_paths or [],
        }
        super().__init__(message, "COMPONENT_CONFLICT", details)
        self.conflicting_components = conflicting_components
        self.conflicting_paths = conflicting_paths or []


class DepError(BootstrapError):
    """Raised when component dependencies cannot be satisfied.

    This error occurs during dependency resolution when required dependencies
    are missing, circular dependencies are detected, or version constraints
    cannot be satisfied.
    """

    def __init__(
        self,
        message: str,
        component: str,
        missing_deps: Optional[List[str]] = None,
        circular_deps: Optional[List[str]] = None,
    ) -> None:
        details = {
            "component": component,
            "missing_dependencies": missing_deps or [],
            "circular_dependencies": circular_deps or [],
        }
        super().__init__(message, "DEPENDENCY_ERROR", details)
        self.component = component
        self.missing_deps = missing_deps or []
        self.circular_deps = circular_deps or []


class DriftError(BootstrapError):
    """Raised when installed files differ from expected state.

    This error occurs during validation when files have been modified outside
    of the bootstrap system, creating drift from the expected configuration.
    """

    def __init__(
        self,
        message: str,
        component: str,
        drifted_files: List[str],
        repair_available: bool = True,
    ) -> None:
        details = {
            "component": component,
            "drifted_files": drifted_files,
            "repair_available": repair_available,
        }
        super().__init__(message, "STATE_DRIFT", details)
        self.component = component
        self.drifted_files = drifted_files
        self.repair_available = repair_available


class ValidationError(BootstrapError):
    """Raised when manifest or configuration validation fails.

    This error occurs when plugin manifests, installation manifests, or
    target structures fail JSON schema validation.
    """

    def __init__(
        self,
        message: str,
        file_path: str,
        validation_errors: List[str],
    ) -> None:
        details = {
            "file_path": file_path,
            "validation_errors": validation_errors,
        }
        super().__init__(message, "VALIDATION_ERROR", details)
        self.file_path = file_path
        self.validation_errors = validation_errors


class TransactionError(BootstrapError):
    """Raised when atomic file operations fail.

    This error occurs during installation when staging, backup, or promotion
    operations fail, requiring rollback to maintain system consistency.
    """

    def __init__(
        self,
        message: str,
        component: str,
        operation: str,
        rollback_available: bool = True,
    ) -> None:
        details = {
            "component": component,
            "operation": operation,
            "rollback_available": rollback_available,
        }
        super().__init__(message, "TRANSACTION_ERROR", details)
        self.component = component
        self.operation = operation
        self.rollback_available = rollback_available
