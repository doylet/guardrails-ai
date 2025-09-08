# Developer Documentation: AI Guardrails Bootstrap System

## Architecture Overview

The AI Guardrails Bootstrap System implements a modular, testable architecture following clean architecture principles. This document provides comprehensive guidance for developers working on the system.

## Package Architecture

### Core Principles

1. **Dependency Inversion**: Higher-level modules don't depend on lower-level modules
2. **Single Responsibility**: Each module has one reason to change
3. **Open/Closed**: Open for extension, closed for modification
4. **Interface Segregation**: Clients depend only on interfaces they use

### Package Structure

```
src/packages/
├── domain/          # Pure business logic (no dependencies)
├── core/            # Application services (orchestration)
├── adapters/        # External system interfaces
└── cli/             # User interface layer
```

#### Domain Layer (`packages.domain`)

**Purpose**: Pure business logic with no external dependencies

**Modules**:
- `models.py`: Core data structures and value objects
- `operations.py`: Business rule implementations
- `errors.py`: Domain-specific exception hierarchy

**Example**:
```python
# domain/models.py
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class InstallationPlan:
    """Represents a planned installation operation."""
    profile: str
    components: List[str]
    target_paths: Dict[str, str]
    conflicts: List[str]

    def has_conflicts(self) -> bool:
        """Check if plan has conflicts."""
        return len(self.conflicts) > 0
```

#### Core Layer (`packages.core`)

**Purpose**: Application services that orchestrate domain operations

**Modules**:
- `orchestrator.py`: High-level coordination and workflow management
- `planner.py`: Installation planning and conflict detection
- `installer.py`: Atomic installation operations with rollback

**Example**:
```python
# core/orchestrator.py
from typing import Optional
from ..domain.models import InstallationPlan
from ..domain.errors import ConflictError
from ..adapters.file_ops import FileOperations

class Orchestrator:
    """High-level coordination of installation workflows."""

    def __init__(self, file_ops: Optional[FileOperations] = None):
        self._file_ops = file_ops or FileOperations()
        self._planner = Planner(self._file_ops)
        self._installer = Installer(self._file_ops)

    def install(self, profile: str, force: bool = False) -> None:
        """Install a profile with conflict resolution."""
        plan = self._planner.create_plan(profile)

        if plan.has_conflicts() and not force:
            raise ConflictError(f"Conflicts detected: {plan.conflicts}")

        self._installer.execute_plan(plan)
```

#### Adapters Layer (`packages.adapters`)

**Purpose**: Interface with external systems (file system, YAML processing, etc.)

**Modules**:
- `file_ops.py`: File system operations with error handling
- `yaml_ops.py`: YAML/JSON processing and validation

**Example**:
```python
# adapters/yaml_ops.py
import yaml
from typing import Any, Dict, List
from ..domain.errors import ValidationError

class YAMLOperations:
    """Adapter for YAML/JSON operations."""

    def validate_receipt_format(self, data: Dict[str, Any]) -> None:
        """Validate receipt format according to schema."""
        required_fields = ['version', 'profile', 'components', 'timestamp']

        for field in required_fields:
            if field not in data:
                raise ValidationError(f"Missing required field: {field}")

        if not isinstance(data['components'], list):
            raise ValidationError("Components must be a list")
```

#### CLI Layer (`packages.cli`)

**Purpose**: User interface with enhanced error handling

**Modules**:
- `main.py`: Command-line interface with contextual error messages

**Example**:
```python
# cli/main.py
import argparse
from ..core.orchestrator import Orchestrator
from ..domain.errors import ConflictError, DepError

def display_enhanced_error(error: Exception) -> None:
    """Display contextual error messages with resolution suggestions."""
    if isinstance(error, ConflictError):
        print(f"ERROR: {error}")
        print("\nRESOLUTION SUGGESTIONS:")
        print("• Use --force to override existing files")
        print("• Check for dependency conflicts: ai-guardrails doctor")
    elif isinstance(error, DepError):
        print(f"ERROR: {error}")
        print("\nRESOLUTION SUGGESTIONS:")
        print("• Verify manifest syntax: ai-guardrails doctor")
        print("• Check available components: ai-guardrails list --components")
```

## Testing Strategy

### Test Structure

```
tests/
├── unit/           # Unit tests for individual modules
├── integration/    # Integration tests for component interaction
└── e2e/           # End-to-end tests for complete workflows
```

### Unit Testing

**Guidelines**:
- Test each module in isolation
- Mock external dependencies
- Focus on business logic correctness
- Achieve >90% code coverage

**Example**:
```python
# tests/unit/test_yaml_ops.py
import pytest
from unittest.mock import patch, mock_open
from packages.adapters.yaml_ops import YAMLOperations
from packages.domain.errors import ValidationError

class TestYAMLOperations:

    def setup_method(self):
        self.yaml_ops = YAMLOperations()

    def test_validate_receipt_format_success(self):
        """Test successful receipt validation."""
        valid_receipt = {
            'version': '1.0',
            'profile': 'standard',
            'components': ['core-files', 'hooks'],
            'timestamp': '2024-01-01T00:00:00Z'
        }

        # Should not raise exception
        self.yaml_ops.validate_receipt_format(valid_receipt)

    def test_validate_receipt_format_missing_field(self):
        """Test receipt validation with missing field."""
        invalid_receipt = {
            'version': '1.0',
            'profile': 'standard'
            # Missing 'components' and 'timestamp'
        }

        with pytest.raises(ValidationError, match="Missing required field: components"):
            self.yaml_ops.validate_receipt_format(invalid_receipt)
```

### Integration Testing

**Guidelines**:
- Test component interactions
- Use test doubles for external systems
- Verify data flow between layers
- Test error propagation

**Example**:
```python
# tests/integration/test_installation_workflow.py
import tempfile
from pathlib import Path
from packages.core.orchestrator import Orchestrator
from packages.adapters.file_ops import FileOperations

class TestInstallationWorkflow:

    def test_complete_installation_workflow(self):
        """Test end-to-end installation workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            target_path = Path(temp_dir)

            # Setup orchestrator with real file operations
            file_ops = FileOperations(base_path=target_path)
            orchestrator = Orchestrator(file_ops)

            # Execute installation
            orchestrator.install(profile="standard")

            # Verify installation results
            assert (target_path / ".ai" / "config.yml").exists()
            assert (target_path / ".pre-commit-config.yaml").exists()
```

### End-to-End Testing

**Guidelines**:
- Test complete user workflows
- Use real CLI commands
- Verify actual file system changes
- Test error scenarios

**Example**:
```python
# tests/e2e/test_cli_workflows.py
import subprocess
import tempfile
from pathlib import Path

class TestCLIWorkflows:

    def test_plan_and_install_workflow(self):
        """Test planning and installation via CLI."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Change to test directory
            original_cwd = Path.cwd()
            test_dir = Path(temp_dir)

            try:
                test_dir.mkdir(exist_ok=True)
                test_dir.joinpath('.git').mkdir()  # Make it a git repo

                # Test planning
                result = subprocess.run([
                    'python', str(original_cwd / 'bin' / 'ai-guardrails-bootstrap'),
                    'plan', '--profile', 'standard'
                ], cwd=test_dir, capture_output=True, text=True)

                assert result.returncode == 0
                assert 'PLAN: Install profile' in result.stdout

                # Test installation
                result = subprocess.run([
                    'python', str(original_cwd / 'bin' / 'ai-guardrails-bootstrap'),
                    'install', '--profile', 'standard'
                ], cwd=test_dir, capture_output=True, text=True)

                assert result.returncode == 0
                assert test_dir.joinpath('.ai', 'config.yml').exists()

            finally:
                # Restore working directory
                Path.cwd().chdir(original_cwd)
```

## Error Handling

### Exception Hierarchy

```python
# domain/errors.py
class GuardrailsError(Exception):
    """Base exception for all guardrails errors."""
    pass

class ValidationError(GuardrailsError):
    """Raised when validation fails."""
    pass

class ConflictError(GuardrailsError):
    """Raised when file conflicts are detected."""
    pass

class DepError(GuardrailsError):
    """Raised when dependency issues occur."""
    pass

class DriftError(GuardrailsError):
    """Raised when state drift is detected."""
    pass

class InstallationError(GuardrailsError):
    """Raised when installation operations fail."""
    pass
```

### Error Context

Each error includes context for better debugging:

```python
# Example error with context
raise ConflictError(
    message="File conflict detected",
    file_path=".ai/config.yml",
    existing_hash="abc123",
    new_hash="def456",
    resolution_hint="Use --force to override"
)
```

## Performance Guidelines

### File Operations

**Best Practices**:
- Use atomic operations (staging/backup/promote)
- Implement efficient hashing for change detection
- Batch file operations where possible
- Use appropriate buffer sizes for large files

**Example**:
```python
# adapters/file_ops.py
def atomic_copy(self, source: Path, target: Path) -> None:
    """Copy file atomically using staging."""
    staging_path = target.with_suffix(target.suffix + '.staging')

    try:
        # Copy to staging area
        shutil.copy2(source, staging_path)

        # Atomic move to final location
        staging_path.rename(target)
    except Exception:
        # Cleanup staging file on error
        staging_path.unlink(missing_ok=True)
        raise
```

### Memory Management

**Guidelines**:
- Stream large files instead of loading entirely into memory
- Use generators for processing large datasets
- Implement proper resource cleanup with context managers
- Profile memory usage for performance-critical paths

### Caching Strategy

**Implementation**:
- Cache file hashes to avoid redundant calculations
- Cache manifest parsing results
- Use LRU cache for frequently accessed data
- Implement cache invalidation for changed files

## Debugging and Logging

### Logging Configuration

```python
# Configure structured logging
import logging
import json
from datetime import datetime

class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'module': record.module,
            'message': record.getMessage(),
            'function': record.funcName,
            'line': record.lineno
        }

        if hasattr(record, 'operation'):
            log_entry['operation'] = record.operation

        if hasattr(record, 'file_path'):
            log_entry['file_path'] = record.file_path

        return json.dumps(log_entry)
```

### Debug Mode

Enable comprehensive debugging:

```bash
# Enable debug logging
export AI_GUARDRAILS_DEBUG=1
ai-guardrails install --profile standard --verbose

# Check debug logs
tail -f .ai/guardrails/logs/debug.log
```

## Development Workflow

### Setting Up Development Environment

```bash
# Clone repository
git clone <repository-url>
cd bootstrap-dev

# Install development dependencies
pip install -e .[dev]

# Install pre-commit hooks
pre-commit install

# Run tests
python -m pytest tests/ -v

# Run linting
ruff check src/ tests/
mypy src/
```

### Making Changes

1. **Create Feature Branch**: `git checkout -b feature/description`
2. **Write Tests First**: Follow TDD approach
3. **Implement Feature**: Keep changes small and focused
4. **Run Test Suite**: Ensure all tests pass
5. **Update Documentation**: Keep docs current
6. **Submit Pull Request**: Include tests and documentation

### Code Review Checklist

- [ ] All tests pass
- [ ] Code coverage >90%
- [ ] Follows typing annotations
- [ ] Includes appropriate error handling
- [ ] Documentation updated
- [ ] Backwards compatibility maintained
- [ ] Performance implications considered

## Deployment and Release

### Release Process

1. **Version Bump**: Update version in `pyproject.toml`
2. **Changelog Update**: Document changes in `CHANGELOG.md`
3. **Tag Release**: Create annotated git tag
4. **Run Full Test Suite**: Including integration and e2e tests
5. **Deploy**: Update distribution packages
6. **Monitor**: Check for issues post-deployment

### Compatibility Matrix

| Version | Python | OS Support | Dependencies |
|---------|--------|------------|--------------|
| 1.x | 3.8+ | Linux, macOS, Windows | PyYAML, click |
| 2.x | 3.9+ | Linux, macOS, Windows | PyYAML, click, pydantic |

### Rollback Procedures

If critical issues are discovered post-release:

1. **Immediate**: Revert to previous stable version
2. **Communication**: Notify users via appropriate channels
3. **Investigation**: Identify root cause
4. **Hotfix**: Prepare and test fix
5. **Re-release**: Deploy hotfix with incremented version

## Contributing Guidelines

### Code Style

- Follow PEP 8 with line length of 88 characters
- Use type hints throughout
- Prefer composition over inheritance
- Write descriptive variable and function names
- Include docstrings for all public interfaces

### Testing Requirements

- Write tests for all new functionality
- Maintain >90% code coverage
- Include both positive and negative test cases
- Use descriptive test names that explain behavior
- Mock external dependencies appropriately

### Documentation Standards

- Update this developer documentation for architectural changes
- Include inline code comments for complex logic
- Write clear commit messages following conventional commit format
- Update API documentation for public interface changes

## Troubleshooting Common Issues

### Import Errors

**Problem**: Module import failures in development
**Solution**: Verify PYTHONPATH and package structure:

```bash
export PYTHONPATH="${PWD}/src:${PYTHONPATH}"
python -c "from packages.cli.main import main"
```

### Test Failures

**Problem**: Tests fail in CI but pass locally
**Solution**: Check for platform-specific assumptions:

```python
# Bad: Assumes Unix path separators
expected_path = "src/packages/cli"

# Good: Uses platform-appropriate separators
expected_path = Path("src") / "packages" / "cli"
```

### Performance Issues

**Problem**: Slow installation performance
**Solution**: Profile and optimize bottlenecks:

```bash
# Profile installation
python -m cProfile -o install.prof bin/ai-guardrails-bootstrap install --profile standard

# Analyze results
python -c "
import pstats
stats = pstats.Stats('install.prof')
stats.sort_stats('cumulative').print_stats(20)
"
```

This developer documentation provides comprehensive guidance for working with the AI Guardrails Bootstrap System. Keep it updated as the system evolves.
