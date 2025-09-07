"""Unit tests for the orchestrator component.

Tests coordination of core components and adapter layer integration.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock

from src.packages.core.orchestrator import Orchestrator
from src.packages.domain.model import InstallPlan, ComponentPlan, FileAction, Receipt
from src.packages.domain.errors import ValidationError, InstallationError


class TestOrchestrator:
    """Test orchestrator coordination and integration."""

    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def mock_components(self):
        """Create mock core components."""
        resolver = Mock()
        planner = Mock()
        installer = Mock()
        doctor = Mock()

        return {
            'resolver': resolver,
            'planner': planner,
            'installer': installer,
            'doctor': doctor
        }

    @pytest.fixture
    def mock_adapters(self):
        """Create mock adapters."""
        receipts_adapter = Mock()
        return {'receipts': receipts_adapter}

    @pytest.fixture
    def orchestrator(self, temp_workspace, mock_components, mock_adapters):
        """Create orchestrator with mocked dependencies."""
        orch = Orchestrator(target_dir=temp_workspace)

        # Replace components with mocks
        orch.resolver = mock_components['resolver']
        orch.planner = mock_components['planner']
        orch.installer = mock_components['installer']
        orch.doctor = mock_components['doctor']
        orch.receipts_adapter = mock_adapters['receipts']

        return orch

    @pytest.fixture
    def sample_plan(self, temp_workspace):
        """Create a sample installation plan."""
        file_action = FileAction(
            source_path="/templates/test.txt",
            target_path="output/test.txt",
            action_type="copy",
            content_hash="a" * 64
        )

        component = ComponentPlan(
            component_id="test-component",
            file_actions=[file_action],
            manifest_hash="b" * 64
        )

        return InstallPlan(
            profile="test",
            components=[component],
            target_dir=temp_workspace
        )

    def test_plan_generation_workflow(self, orchestrator, mock_components, sample_plan):
        """Test the complete planning workflow."""
        from src.packages.core.resolver import ResolvedSpec

        # Mock resolver output
        resolved_spec = Mock(spec=ResolvedSpec)
        mock_components['resolver'].resolve.return_value = resolved_spec

        # Mock planner output
        mock_components['planner'].create_plan.return_value = sample_plan

        # Execute planning
        result_plan = orchestrator.plan(profile="test")

        # Verify workflow
        mock_components['resolver'].resolve.assert_called_once_with("test")
        mock_components['planner'].create_plan.assert_called_once_with(resolved_spec)

        # Verify result
        assert result_plan == sample_plan

    def test_installation_workflow(self, orchestrator, mock_components, sample_plan):
        """Test the complete installation workflow."""
        from src.packages.core.resolver import ResolvedSpec

        # Mock the complete workflow
        resolved_spec = Mock(spec=ResolvedSpec)
        mock_components['resolver'].resolve.return_value = resolved_spec
        mock_components['planner'].create_plan.return_value = sample_plan
        mock_components['installer'].install_plan.return_value = {"test-component": True}

        # Execute installation
        results = orchestrator.install(profile="test")

        # Verify workflow
        mock_components['resolver'].resolve.assert_called_once_with("test")
        mock_components['planner'].create_plan.assert_called_once_with(resolved_spec)
        mock_components['installer'].install_plan.assert_called_once_with(
            sample_plan,
            dry_run=False,
            force=False
        )

        # Verify result
        assert results == {"test-component": True}

    def test_installation_with_options(self, orchestrator, mock_components, sample_plan):
        """Test installation with dry_run and force options."""
        from src.packages.core.resolver import ResolvedSpec

        # Mock workflow
        resolved_spec = Mock(spec=ResolvedSpec)
        mock_components['resolver'].resolve.return_value = resolved_spec
        mock_components['planner'].create_plan.return_value = sample_plan
        mock_components['installer'].install_plan.return_value = {"test-component": True}

        # Execute with options
        orchestrator.install(profile="test", dry_run=True, force=True)

        # Verify options were passed through
        mock_components['installer'].install_plan.assert_called_once_with(
            sample_plan,
            dry_run=True,
            force=True
        )

    def test_doctor_health_checks(self, orchestrator, mock_components):
        """Test health check delegation to doctor."""
        from src.packages.domain.model import Diagnostic

        # Mock doctor output
        diagnostics = [
            Diagnostic(
                component_id="test-component",
                severity="info",
                message="Component healthy",
                details={}
            )
        ]
        mock_components['doctor'].diagnose.return_value = diagnostics

        # Execute health check
        result = orchestrator.doctor()

        # Verify delegation
        mock_components['doctor'].diagnose.assert_called_once()
        assert result == diagnostics

    def test_list_installed_components(self, orchestrator, mock_adapters):
        """Test listing of installed components."""
        # Mock receipts
        receipts = [
            Receipt(
                component_id="component-1",
                installed_files=["file1.txt"],
                manifest_hash="a" * 64,
                install_timestamp="2024-01-01T12:00:00Z"
            ),
            Receipt(
                component_id="component-2",
                installed_files=["file2.txt"],
                manifest_hash="b" * 64,
                install_timestamp="2024-01-01T12:01:00Z"
            )
        ]
        mock_adapters['receipts'].list_receipts.return_value = receipts

        # Execute listing
        installed = orchestrator.list_installed()

        # Verify result
        assert "component-1" in installed
        assert "component-2" in installed
        assert len(installed) == 2

    def test_uninstall_component(self, orchestrator, mock_adapters, temp_workspace):
        """Test component uninstallation."""
        # Setup: Create files to uninstall
        (temp_workspace / "file1.txt").write_text("content")
        (temp_workspace / "file2.txt").write_text("content")

        # Mock receipt
        receipt = Receipt(
            component_id="test-component",
            installed_files=["file1.txt", "file2.txt"],
            manifest_hash="a" * 64,
            install_timestamp="2024-01-01T12:00:00Z"
        )
        mock_adapters['receipts'].get_receipt.return_value = receipt

        # Execute uninstall
        result = orchestrator.uninstall("test-component")

        # Verify result
        assert result is True

        # Verify files were removed
        assert not (temp_workspace / "file1.txt").exists()
        assert not (temp_workspace / "file2.txt").exists()

        # Verify receipt was removed
        mock_adapters['receipts'].remove_receipt.assert_called_once_with("test-component")

    def test_uninstall_nonexistent_component(self, orchestrator, mock_adapters):
        """Test uninstalling a component that doesn't exist."""
        # Mock missing receipt
        mock_adapters['receipts'].get_receipt.return_value = None

        # Execute uninstall
        result = orchestrator.uninstall("nonexistent-component")

        # Should return False for missing component
        assert result is False

        # Should not attempt to remove anything
        mock_adapters['receipts'].remove_receipt.assert_not_called()

    def test_get_component_status(self, orchestrator, mock_adapters, temp_workspace):
        """Test component status reporting."""
        # Setup: Create component file
        (temp_workspace / "status_file.txt").write_text("content")

        # Mock receipt
        receipt = Receipt(
            component_id="status-component",
            installed_files=["status_file.txt"],
            manifest_hash="a" * 64,
            install_timestamp="2024-01-01T12:00:00Z"
        )
        mock_adapters['receipts'].get_receipt.return_value = receipt

        # Execute status check
        status = orchestrator.get_component_status("status-component")

        # Verify status information
        assert status["installed"] is True
        assert status["has_receipt"] is True
        assert "status_file.txt" in status["files"]

    def test_get_status_missing_component(self, orchestrator, mock_adapters):
        """Test status of missing component."""
        # Mock missing receipt
        mock_adapters['receipts'].get_receipt.return_value = None

        # Execute status check
        status = orchestrator.get_component_status("missing-component")

        # Verify status for missing component
        assert status["installed"] is False
        assert status["has_receipt"] is False
        assert status["files"] == []

    def test_validate_environment(self, orchestrator, temp_workspace):
        """Test environment validation."""
        # Execute validation
        validation = orchestrator.validate_environment()

        # Should include basic validations
        assert "target_directory_writable" in validation
        assert "python_version_ok" in validation

        # Target directory should be writable in test
        assert validation["target_directory_writable"] is True

    def test_error_handling_in_workflow(self, orchestrator, mock_components):
        """Test error handling during workflow execution."""
        # Mock resolver to raise error
        mock_components['resolver'].resolve.side_effect = ValidationError("Invalid profile")

        # Should propagate validation errors
        with pytest.raises(ValidationError, match="Invalid profile"):
            orchestrator.plan(profile="invalid")

    def test_installation_error_handling(self, orchestrator, mock_components, sample_plan):
        """Test error handling during installation."""
        from src.packages.core.resolver import ResolvedSpec

        # Mock successful planning but failed installation
        resolved_spec = Mock(spec=ResolvedSpec)
        mock_components['resolver'].resolve.return_value = resolved_spec
        mock_components['planner'].create_plan.return_value = sample_plan
        mock_components['installer'].install_plan.side_effect = InstallationError("Installation failed")

        # Should propagate installation errors
        with pytest.raises(InstallationError, match="Installation failed"):
            orchestrator.install(profile="test")

    def test_transaction_boundary_management(self, orchestrator, mock_components, sample_plan):
        """Test that operations maintain proper transaction boundaries."""
        from src.packages.core.resolver import ResolvedSpec

        # Mock workflow that fails in installer
        resolved_spec = Mock(spec=ResolvedSpec)
        mock_components['resolver'].resolve.return_value = resolved_spec
        mock_components['planner'].create_plan.return_value = sample_plan
        mock_components['installer'].install_plan.side_effect = InstallationError("Transaction failed")

        # Installation should fail cleanly
        with pytest.raises(InstallationError):
            orchestrator.install(profile="test")

        # Planning should have succeeded (called once)
        mock_components['planner'].create_plan.assert_called_once()

        # Installer should have been called but failed
        mock_components['installer'].install_plan.assert_called_once()

    def test_dry_run_isolation(self, orchestrator, mock_components, sample_plan):
        """Test that dry runs don't affect system state."""
        from src.packages.core.resolver import ResolvedSpec

        # Mock successful dry run
        resolved_spec = Mock(spec=ResolvedSpec)
        mock_components['resolver'].resolve.return_value = resolved_spec
        mock_components['planner'].create_plan.return_value = sample_plan
        mock_components['installer'].install_plan.return_value = {"test-component": True}

        # Execute dry run
        results = orchestrator.install(profile="test", dry_run=True)

        # Should pass dry_run flag to installer
        mock_components['installer'].install_plan.assert_called_once_with(
            sample_plan,
            dry_run=True,
            force=False
        )

        # Should still return results
        assert results == {"test-component": True}

    def test_concurrent_operation_safety(self, orchestrator, mock_components, sample_plan):
        """Test safety of concurrent operations."""
        import threading
        import time

        from src.packages.core.resolver import ResolvedSpec

        # Mock workflow
        resolved_spec = Mock(spec=ResolvedSpec)
        mock_components['resolver'].resolve.return_value = resolved_spec
        mock_components['planner'].create_plan.return_value = sample_plan

        # Mock installer with delay to simulate concurrent access
        def delayed_install(*args, **kwargs):
            time.sleep(0.1)
            return {"test-component": True}

        mock_components['installer'].install_plan.side_effect = delayed_install

        # Execute concurrent installations
        results = []
        threads = []

        def install_worker():
            try:
                result = orchestrator.install(profile="test")
                results.append(result)
            except Exception as e:
                results.append(str(e))

        # Start multiple threads
        for _ in range(3):
            thread = threading.Thread(target=install_worker)
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # All operations should complete successfully
        assert len(results) == 3
        assert all(isinstance(r, dict) for r in results), f"Some operations failed: {results}"

    def test_resource_cleanup_on_failure(self, orchestrator, mock_components, sample_plan):
        """Test that resources are cleaned up on operation failure."""
        from src.packages.core.resolver import ResolvedSpec

        # Mock workflow that fails after partial execution
        resolved_spec = Mock(spec=ResolvedSpec)
        mock_components['resolver'].resolve.return_value = resolved_spec
        mock_components['planner'].create_plan.return_value = sample_plan

        # Mock installer that raises exception
        mock_components['installer'].install_plan.side_effect = Exception("Unexpected error")

        # Should handle unexpected errors gracefully
        with pytest.raises(Exception, match="Unexpected error"):
            orchestrator.install(profile="test")

        # Verify components were called appropriately
        mock_components['resolver'].resolve.assert_called_once()
        mock_components['planner'].create_plan.assert_called_once()
        mock_components['installer'].install_plan.assert_called_once()

    def test_adapter_layer_integration(self, orchestrator, mock_adapters):
        """Test integration with adapter layer."""
        # Test that orchestrator properly uses adapters

        # List installed should use receipts adapter
        mock_adapters['receipts'].list_receipts.return_value = []

        installed = orchestrator.list_installed()

        # Verify adapter was called
        mock_adapters['receipts'].list_receipts.assert_called_once()
        assert installed == []
