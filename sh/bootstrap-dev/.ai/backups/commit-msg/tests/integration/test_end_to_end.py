"""Integration tests for the complete installation workflow.

Tests the end-to-end process from planning to installation with
transaction safety validation.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch

from src.packages.core import Orchestrator
from src.packages.domain.errors import InstallationError


class TestEndToEndWorkflow:
    """Test complete installation workflows."""

    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def sample_template_repo(self, temp_workspace):
        """Create a sample template repository."""
        template_repo = temp_workspace / "templates"
        template_repo.mkdir()

        # Create sample files
        (template_repo / "basic.txt").write_text("Basic file content")
        (template_repo / "config.yml").write_text("config:\n  key: value")
        (template_repo / "template.j2").write_text("Hello {{ name }}!")

        return template_repo

    @pytest.fixture
    def sample_manifest(self, temp_workspace, sample_template_repo):
        """Create a sample installation manifest."""
        manifest_content = """
version: "1.0"
profiles:
  basic:
    description: "Basic installation"
    components:
      - core-files

components:
  core-files:
    description: "Core configuration files"
    file_patterns:
      - "basic.txt"
      - "config.yml"
    target_paths:
      basic.txt: ".ai/basic.txt"
      config.yml: ".ai/config.yml"
"""
        manifest_path = temp_workspace / "installation-manifest.yaml"
        manifest_path.write_text(manifest_content)
        return manifest_path

    @pytest.fixture
    def orchestrator(self, temp_workspace):
        """Create orchestrator for testing."""
        return Orchestrator(target_dir=temp_workspace / "target")

    def test_complete_installation_workflow(
        self,
        orchestrator,
        temp_workspace,
        sample_template_repo,
        sample_manifest
    ):
        """Test complete installation from plan to execution."""
        target_dir = temp_workspace / "target"
        target_dir.mkdir()

        # Mock the resolver to return our test data
        with patch.object(orchestrator.resolver, 'resolve') as mock_resolve:
            # Create mock resolved spec
            from src.packages.core.resolver import ResolvedSpec, ComponentSpec

            component_spec = ComponentSpec(
                component_id="core-files",
                files={
                    "basic.txt": str(sample_template_repo / "basic.txt"),
                    "config.yml": str(sample_template_repo / "config.yml"),
                },
                manifest_hash="a" * 64,
            )

            mock_resolve.return_value = ResolvedSpec(
                profile="basic",
                components=[component_spec],
                target_dir=target_dir,
            )

            # Step 1: Generate plan
            plan = orchestrator.plan(profile="basic")

            assert plan.profile == "basic"
            assert len(plan.components) == 1
            assert plan.components[0].component_id == "core-files"

            # Step 2: Execute installation
            results = orchestrator.install(profile="basic")

            assert all(results.values()), f"Installation failed: {results}"

            # Step 3: Verify files were created
            assert (target_dir / ".ai" / "basic.txt").exists()
            assert (target_dir / ".ai" / "config.yml").exists()

            # Step 4: Verify file contents
            basic_content = (target_dir / ".ai" / "basic.txt").read_text()
            assert basic_content == "Basic file content"

            config_content = (target_dir / ".ai" / "config.yml").read_text()
            assert "config:" in config_content

            # Step 5: Verify receipts were created
            installed = orchestrator.list_installed()
            assert "core-files" in installed

    def test_dry_run_does_not_modify_filesystem(
        self,
        orchestrator,
        temp_workspace,
        sample_template_repo
    ):
        """Test that dry run doesn't modify the filesystem."""
        target_dir = temp_workspace / "target"
        target_dir.mkdir()

        with patch.object(orchestrator.resolver, 'resolve') as mock_resolve:
            from src.packages.core.resolver import ResolvedSpec, ComponentSpec

            component_spec = ComponentSpec(
                component_id="test-component",
                files={"test.txt": str(sample_template_repo / "basic.txt")},
                manifest_hash="a" * 64,
            )

            mock_resolve.return_value = ResolvedSpec(
                profile="test",
                components=[component_spec],
                target_dir=target_dir,
            )

            # Perform dry run
            results = orchestrator.install(profile="test", dry_run=True)

            assert all(results.values()), "Dry run should succeed"

            # Verify no files were created
            assert not (target_dir / "test.txt").exists()
            assert not any(target_dir.glob("**/*"))

            # Verify no receipts were created
            installed = orchestrator.list_installed()
            assert "test-component" not in installed

    def test_force_installation_overwrites_existing(
        self,
        orchestrator,
        temp_workspace,
        sample_template_repo
    ):
        """Test that force installation overwrites existing files."""
        target_dir = temp_workspace / "target"
        target_dir.mkdir()

        # Create existing file with different content
        existing_file = target_dir / "test.txt"
        existing_file.write_text("Original content")

        with patch.object(orchestrator.resolver, 'resolve') as mock_resolve:
            from src.packages.core.resolver import ResolvedSpec, ComponentSpec

            component_spec = ComponentSpec(
                component_id="test-component",
                files={"test.txt": str(sample_template_repo / "basic.txt")},
                manifest_hash="a" * 64,
            )

            mock_resolve.return_value = ResolvedSpec(
                profile="test",
                components=[component_spec],
                target_dir=target_dir,
            )

            # Install with force
            results = orchestrator.install(profile="test", force=True)

            assert all(results.values()), "Force installation should succeed"

            # Verify file was overwritten
            new_content = existing_file.read_text()
            assert new_content == "Basic file content"
            assert new_content != "Original content"

    def test_idempotent_installation(
        self,
        orchestrator,
        temp_workspace,
        sample_template_repo
    ):
        """Test that repeated installations are idempotent."""
        target_dir = temp_workspace / "target"
        target_dir.mkdir()

        with patch.object(orchestrator.resolver, 'resolve') as mock_resolve:
            from src.packages.core.resolver import ResolvedSpec, ComponentSpec

            component_spec = ComponentSpec(
                component_id="test-component",
                files={"test.txt": str(sample_template_repo / "basic.txt")},
                manifest_hash="a" * 64,
            )

            mock_resolve.return_value = ResolvedSpec(
                profile="test",
                components=[component_spec],
                target_dir=target_dir,
            )

            # First installation
            results1 = orchestrator.install(profile="test")
            assert all(results1.values())

            original_mtime = (target_dir / "test.txt").stat().st_mtime

            # Second installation (should be no-op)
            results2 = orchestrator.install(profile="test")
            assert all(results2.values())

            # File should not have been modified
            new_mtime = (target_dir / "test.txt").stat().st_mtime
            assert new_mtime == original_mtime

    def test_rollback_on_failure(self, orchestrator, temp_workspace):
        """Test that failed installations are rolled back."""
        target_dir = temp_workspace / "target"
        target_dir.mkdir()

        # Create a scenario where second component will fail
        with patch.object(orchestrator.resolver, 'resolve') as mock_resolve:
            from src.packages.core.resolver import ResolvedSpec, ComponentSpec

            # Component 1: will succeed
            good_file = temp_workspace / "good.txt"
            good_file.write_text("Good content")

            component1 = ComponentSpec(
                component_id="good-component",
                files={"good.txt": str(good_file)},
                manifest_hash="a" * 64,
            )

            # Component 2: will fail (missing source file)
            component2 = ComponentSpec(
                component_id="bad-component",
                files={"bad.txt": "/nonexistent/file.txt"},
                manifest_hash="b" * 64,
            )

            mock_resolve.return_value = ResolvedSpec(
                profile="test",
                components=[component1, component2],
                target_dir=target_dir,
            )

            # Installation should fail
            with pytest.raises(InstallationError):
                orchestrator.install(profile="test")

            # Verify rollback: no files should exist
            assert not (target_dir / "good.txt").exists()

            # Verify no components are marked as installed
            installed = orchestrator.list_installed()
            assert "good-component" not in installed
            assert "bad-component" not in installed

    def test_doctor_health_checks(
        self,
        orchestrator,
        temp_workspace,
        sample_template_repo
    ):
        """Test doctor health check functionality."""
        target_dir = temp_workspace / "target"
        target_dir.mkdir()

        # Install a component first
        with patch.object(orchestrator.resolver, 'resolve') as mock_resolve:
            from src.packages.core.resolver import ResolvedSpec, ComponentSpec

            component_spec = ComponentSpec(
                component_id="health-test",
                files={"health.txt": str(sample_template_repo / "basic.txt")},
                manifest_hash="a" * 64,
            )

            mock_resolve.return_value = ResolvedSpec(
                profile="test",
                components=[component_spec],
                target_dir=target_dir,
            )

            # Install component
            orchestrator.install(profile="test")

            # Run health check - should be healthy
            diagnostics = orchestrator.doctor()

            errors = [d for d in diagnostics if d.severity == "error"]
            assert len(errors) == 0, f"Unexpected errors: {errors}"

            # Introduce drift by modifying file
            (target_dir / "health.txt").write_text("Modified content")

            # Run health check again - should detect drift
            diagnostics = orchestrator.doctor()

            warnings = [d for d in diagnostics if d.severity == "warning"]
            drift_warnings = [w for w in warnings if "drift" in w.message.lower()]
            assert len(drift_warnings) > 0, "Should detect file content drift"

    def test_uninstall_removes_components(
        self,
        orchestrator,
        temp_workspace,
        sample_template_repo
    ):
        """Test that uninstall properly removes components."""
        target_dir = temp_workspace / "target"
        target_dir.mkdir()

        # Install a component
        with patch.object(orchestrator.resolver, 'resolve') as mock_resolve:
            from src.packages.core.resolver import ResolvedSpec, ComponentSpec

            component_spec = ComponentSpec(
                component_id="uninstall-test",
                files={"uninstall.txt": str(sample_template_repo / "basic.txt")},
                manifest_hash="a" * 64,
            )

            mock_resolve.return_value = ResolvedSpec(
                profile="test",
                components=[component_spec],
                target_dir=target_dir,
            )

            # Install
            orchestrator.install(profile="test")

            # Verify installation
            assert (target_dir / "uninstall.txt").exists()
            assert "uninstall-test" in orchestrator.list_installed()

            # Uninstall
            result = orchestrator.uninstall("uninstall-test")
            assert result, "Uninstall should succeed"

            # Verify removal
            assert not (target_dir / "uninstall.txt").exists()
            assert "uninstall-test" not in orchestrator.list_installed()

    def test_component_status_reporting(
        self,
        orchestrator,
        temp_workspace,
        sample_template_repo
    ):
        """Test component status reporting functionality."""
        target_dir = temp_workspace / "target"
        target_dir.mkdir()

        # Check status of non-installed component
        status = orchestrator.get_component_status("nonexistent")
        assert not status["installed"]
        assert not status["has_receipt"]

        # Install a component
        with patch.object(orchestrator.resolver, 'resolve') as mock_resolve:
            from src.packages.core.resolver import ResolvedSpec, ComponentSpec

            component_spec = ComponentSpec(
                component_id="status-test",
                files={"status.txt": str(sample_template_repo / "basic.txt")},
                manifest_hash="a" * 64,
            )

            mock_resolve.return_value = ResolvedSpec(
                profile="test",
                components=[component_spec],
                target_dir=target_dir,
            )

            orchestrator.install(profile="test")

            # Check status of installed component
            status = orchestrator.get_component_status("status-test")
            assert status["installed"]
            assert status["has_receipt"]
            assert status["current"]
            assert status["receipt_valid"]

    def test_environment_validation(self, orchestrator, temp_workspace):
        """Test environment validation functionality."""
        validation = orchestrator.validate_environment()

        # Should validate basic environment
        assert "target_directory_writable" in validation
        assert "python_version_ok" in validation

        # Most validations should pass in test environment
        assert validation["python_version_ok"]
