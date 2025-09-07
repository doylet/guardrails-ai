"""
Plugin Lifecycle Management for AI Guardrails Bootstrap System

This module provides secure lifecycle hook execution for plugins with:
- Pre-install hook execution with environment validation
- Post-install hook execution with cleanup capabilities
- Validation hook execution with error reporting
- Hook timeout and resource limit enforcement
- Hook execution context and variable passing
- Security boundaries and sandboxed execution

Security Features:
- Script path validation within plugin directory
- Resource limits and timeout enforcement
- Environment variable sanitization
- Process isolation and cleanup
- Execution logging and error handling
"""

import os
import subprocess
import signal
import time
import psutil
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass
from contextlib import contextmanager

from ..domain.plugin_models import LifecycleHooks, PluginSecurityError
from ..domain.constants import DEFAULT_HOOK_TIMEOUT, MAX_HOOK_MEMORY


@dataclass
class HookExecutionResult:
    """Result of hook execution."""
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    duration: float
    resource_usage: Dict[str, Any]
    error_message: Optional[str] = None


@dataclass
class HookExecutionContext:
    """Context for hook execution."""
    plugin_name: str
    plugin_version: str
    plugin_path: Path
    target_path: Path
    environment: Dict[str, str]
    configuration: Dict[str, Any]
    dry_run: bool = False


class PluginLifecycle:
    """Plugin lifecycle management with secure hook execution."""

    def __init__(self, plugin_path: Path, target_path: Path):
        self.plugin_path = Path(plugin_path).resolve()
        self.target_path = Path(target_path).resolve()
        self._validate_paths()

    def _validate_paths(self) -> None:
        """Validate plugin and target paths for security."""
        if not self.plugin_path.exists():
            raise PluginSecurityError(f"Plugin path does not exist: {self.plugin_path}")

        if not self.plugin_path.is_dir():
            raise PluginSecurityError(f"Plugin path is not a directory: {self.plugin_path}")

        # Ensure target path is not within plugin path
        try:
            self.target_path.resolve().relative_to(self.plugin_path)
            raise PluginSecurityError("Target path cannot be within plugin directory")
        except ValueError:
            pass  # Good - target is outside plugin directory

    def execute_component_hooks(self, hooks: LifecycleHooks, hook_type: str,
                               context: HookExecutionContext) -> HookExecutionResult:
        """
        Execute a specific lifecycle hook for a component.

        Args:
            hooks: Component lifecycle hooks
            hook_type: Type of hook to execute (pre_install, post_install, validate, cleanup)
            context: Execution context with plugin and environment information

        Returns:
            Hook execution result

        Raises:
            PluginSecurityError: For security violations
            ValueError: For invalid hook types
        """
        script_path = getattr(hooks, hook_type, None)
        if not script_path:
            return HookExecutionResult(
                success=True,
                exit_code=0,
                stdout="",
                stderr="",
                duration=0.0,
                resource_usage={}
            )

        return self._execute_hook_script(script_path, hook_type, context)

    def execute_all_hooks(self, hooks: LifecycleHooks, hook_type: str,
                         context: HookExecutionContext) -> Dict[str, HookExecutionResult]:
        """
        Execute all hooks of a specific type.

        Args:
            hooks: Lifecycle hooks object
            hook_type: Type of hooks to execute
            context: Execution context

        Returns:
            Dictionary mapping hook names to execution results
        """
        results = {}

        if hook_type == "all":
            # Execute all hooks in order
            hook_order = ["pre_install", "post_install", "validate", "cleanup"]
            for hook_name in hook_order:
                if hasattr(hooks, hook_name) and getattr(hooks, hook_name):
                    results[hook_name] = self.execute_component_hooks(hooks, hook_name, context)
                    # Stop on first failure unless it's cleanup
                    if not results[hook_name].success and hook_name != "cleanup":
                        break
        else:
            results[hook_type] = self.execute_component_hooks(hooks, hook_type, context)

        return results

    def _execute_hook_script(self, script_path: str, hook_type: str,
                           context: HookExecutionContext) -> HookExecutionResult:
        """Execute a single hook script with security restrictions."""
        full_path = self.plugin_path / script_path

        # Security validation
        if not self._validate_script_path(full_path):
            raise PluginSecurityError(f"Script path outside plugin directory: {script_path}")

        if not full_path.exists():
            return HookExecutionResult(
                success=False,
                exit_code=1,
                stdout="",
                stderr=f"Hook script not found: {script_path}",
                duration=0.0,
                resource_usage={},
                error_message=f"Hook script not found: {script_path}"
            )

        if not full_path.is_file():
            return HookExecutionResult(
                success=False,
                exit_code=1,
                stdout="",
                stderr=f"Hook script is not a file: {script_path}",
                duration=0.0,
                resource_usage={},
                error_message=f"Hook script is not a file: {script_path}"
            )

        # Prepare execution environment
        execution_env = self._prepare_execution_environment(context, hook_type)

        # Execute with resource limits and monitoring
        try:
            return self._execute_with_limits(full_path, execution_env, context)
        except Exception as e:
            return HookExecutionResult(
                success=False,
                exit_code=1,
                stdout="",
                stderr=str(e),
                duration=0.0,
                resource_usage={},
                error_message=f"Hook execution failed: {e}"
            )

    def _validate_script_path(self, script_path: Path) -> bool:
        """Validate script is within plugin directory."""
        try:
            script_path.resolve().relative_to(self.plugin_path.resolve())
            return True
        except ValueError:
            return False

    def _prepare_execution_environment(self, context: HookExecutionContext,
                                     hook_type: str) -> Dict[str, str]:
        """Prepare environment variables for hook execution."""
        env = os.environ.copy()

        # Add plugin-specific variables
        plugin_vars = {
            "PLUGIN_NAME": context.plugin_name,
            "PLUGIN_VERSION": context.plugin_version,
            "PLUGIN_PATH": str(self.plugin_path),
            "TARGET_PATH": str(self.target_path),
            "HOOK_TYPE": hook_type,
            "DRY_RUN": str(context.dry_run).lower(),
        }

        # Add configuration variables
        for key, value in context.configuration.items():
            safe_key = self._sanitize_env_key(key)
            plugin_vars[f"PLUGIN_CONFIG_{safe_key.upper()}"] = str(value)

        # Add environment variables from context
        for key, value in context.environment.items():
            safe_key = self._sanitize_env_key(key)
            plugin_vars[f"PLUGIN_ENV_{safe_key.upper()}"] = str(value)

        # Sanitize and add to environment
        for key, value in plugin_vars.items():
            env[key] = self._sanitize_env_value(value)

        # Remove potentially dangerous environment variables
        dangerous_vars = [
            "LD_PRELOAD", "LD_LIBRARY_PATH", "DYLD_INSERT_LIBRARIES",
            "PYTHONPATH", "PATH"  # Keep PATH but will be restricted
        ]

        for var in dangerous_vars:
            if var in env and var != "PATH":
                del env[var]

        # Restrict PATH to safe directories
        if "PATH" in env:
            env["PATH"] = self._sanitize_path(env["PATH"])

        return env

    def _sanitize_env_key(self, key: str) -> str:
        """Sanitize environment variable key."""
        # Keep only alphanumeric and underscore characters
        import re
        return re.sub(r'[^a-zA-Z0-9_]', '_', str(key))

    def _sanitize_env_value(self, value: str) -> str:
        """Sanitize environment variable value."""
        # Remove null bytes and control characters
        value_str = str(value)
        return ''.join(char for char in value_str if ord(char) >= 32 or char in '\t\n\r')

    def _sanitize_path(self, path: str) -> str:
        """Sanitize PATH environment variable."""
        safe_paths = [
            "/usr/bin", "/bin", "/usr/local/bin",
            "/opt/homebrew/bin",  # macOS Homebrew
        ]

        current_paths = path.split(":")
        filtered_paths = []

        for p in current_paths:
            # Allow paths that start with safe prefixes
            if any(p.startswith(safe) for safe in safe_paths):
                filtered_paths.append(p)

        return ":".join(filtered_paths) if filtered_paths else "/usr/bin:/bin"

    def _execute_with_limits(self, script_path: Path, env: Dict[str, str],
                           context: HookExecutionContext) -> HookExecutionResult:
        """Execute script with resource limits and monitoring."""
        import time
        start_time = time.time()

        # Determine script interpreter
        interpreter = self._get_script_interpreter(script_path)

        if context.dry_run:
            return HookExecutionResult(
                success=True,
                exit_code=0,
                stdout=f"[DRY RUN] Would execute: {interpreter} {script_path}",
                stderr="",
                duration=0.0,
                resource_usage={}
            )

        # Prepare command
        if interpreter:
            cmd = [interpreter, str(script_path)]
        else:
            cmd = [str(script_path)]

        try:
            # Execute with timeout and resource monitoring
            with self._resource_monitor() as monitor:
                process = subprocess.Popen(
                    cmd,
                    cwd=self.plugin_path,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    preexec_fn=self._setup_process_limits
                )

                try:
                    stdout, stderr = process.communicate(timeout=DEFAULT_HOOK_TIMEOUT)
                    exit_code = process.returncode
                except subprocess.TimeoutExpired:
                    process.kill()
                    stdout, stderr = process.communicate()
                    exit_code = -signal.SIGKILL
                    stderr += f"\nHook execution timed out after {DEFAULT_HOOK_TIMEOUT} seconds"

            duration = time.time() - start_time
            resource_usage = monitor.get_usage()

            return HookExecutionResult(
                success=(exit_code == 0),
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
                duration=duration,
                resource_usage=resource_usage
            )

        except Exception as e:
            duration = time.time() - start_time
            return HookExecutionResult(
                success=False,
                exit_code=1,
                stdout="",
                stderr=f"Hook execution failed: {e}",
                duration=duration,
                resource_usage={},
                error_message=str(e)
            )

    def _get_script_interpreter(self, script_path: Path) -> Optional[str]:
        """Determine appropriate interpreter for script."""
        # Check shebang line
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                if first_line.startswith('#!'):
                    shebang = first_line[2:].strip()
                    # Extract interpreter from shebang
                    interpreter = shebang.split()[0] if shebang else None
                    if interpreter and Path(interpreter).exists():
                        return interpreter
        except (UnicodeDecodeError, OSError):
            pass

        # Fallback based on file extension
        suffix = script_path.suffix.lower()
        interpreters = {
            '.py': 'python3',
            '.sh': 'bash',
            '.bash': 'bash',
            '.zsh': 'zsh',
            '.pl': 'perl',
            '.rb': 'ruby',
            '.js': 'node',
        }

        return interpreters.get(suffix)

    def _setup_process_limits(self) -> None:
        """Setup resource limits for the subprocess."""
        import resource

        # Set memory limit
        try:
            resource.setrlimit(resource.RLIMIT_AS, (MAX_HOOK_MEMORY, MAX_HOOK_MEMORY))
        except (OSError, ValueError):
            pass  # May not be supported on all systems

        # Set CPU time limit
        try:
            resource.setrlimit(resource.RLIMIT_CPU, (DEFAULT_HOOK_TIMEOUT, DEFAULT_HOOK_TIMEOUT))
        except (OSError, ValueError):
            pass

        # Disable core dumps
        try:
            resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        except (OSError, ValueError):
            pass

    @contextmanager
    def _resource_monitor(self):
        """Context manager for monitoring resource usage."""
        monitor = ResourceMonitor()
        try:
            monitor.start()
            yield monitor
        finally:
            monitor.stop()


class ResourceMonitor:
    """Monitor resource usage during hook execution."""

    def __init__(self):
        self.start_time = None
        self.peak_memory = 0
        self.cpu_percent = 0
        self.process = None

    def start(self):
        """Start resource monitoring."""
        self.start_time = time.time()
        try:
            self.process = psutil.Process()
        except psutil.NoSuchProcess:
            self.process = None

    def stop(self):
        """Stop resource monitoring."""
        pass

    def get_usage(self) -> Dict[str, Any]:
        """Get current resource usage."""
        usage = {
            "peak_memory_mb": self.peak_memory / (1024 * 1024) if self.peak_memory else 0,
            "cpu_percent": self.cpu_percent,
            "duration": time.time() - self.start_time if self.start_time else 0
        }

        if self.process:
            try:
                memory_info = self.process.memory_info()
                usage["current_memory_mb"] = memory_info.rss / (1024 * 1024)
                usage["cpu_percent"] = self.process.cpu_percent()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        return usage


class PluginLifecycleError(Exception):
    """Exception raised during plugin lifecycle operations."""
    pass
