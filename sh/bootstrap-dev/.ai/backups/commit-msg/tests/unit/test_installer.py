"""Unit tests for the installer component.

Tests transaction safety, rollback behavior, and atomic operations.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

from src.packages.core.installer import Installer
from src.packages.domain.model import InstallPlan, ComponentPlan, FileAction
from src.packages.domain.errors import InstallationError


class TestInstaller:
    """Test installer transaction safety and operations."""

    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def mock_adapters(self):
        """Create mock adapters for testing."""
        fs_adapter = Mock()
        receipts_adapter = Mock()
        yaml_ops = Mock()

        return {
            'fs': fs_adapter,
            'receipts': receipts_adapter,
            'yaml_ops': yaml_ops
        }

    @pytest.fixture
    def installer(self, temp_workspace, mock_adapters):
        """Create installer with mocked adapters."""
        return Installer(
            target_dir=temp_workspace,
            receipts_adapter=mock_adapters['receipts'],
            yaml_ops=mock_adapters['yaml_ops']
        )

    @pytest.fixture
    def sample_plan(self):
        """Create a sample installation plan."""
        file_actions = [
            FileAction(
                action_type="COPY",
                source_path=Path("templates/file1.txt"),
                target_path=Path("output/file1.txt"),
                target_hash="a" * 64,
                component_source="template"
            ),
            FileAction(
                action_type="TEMPLATE",
                source_path=Path("templates/file2.j2"),
                target_path=Path("output/file2.txt"),
                target_hash="b" * 64,
                metadata={"variables": {"name": "test"}},
                component_source="template"
            )
        ]

        component = ComponentPlan(
            component_id="test-component",
            file_actions=file_actions,
            manifest_hash="c" * 64
        )

        return InstallPlan(
            profile="test",
            components=[component],
            target_dir=Path("/target")
        )

    def test_successful_installation(self, installer, sample_plan, mock_adapters):
        """Test successful installation with all components."""
        # Mock successful operations
        mock_adapters['fs'].create_staging_context.return_value.__enter__ = Mock()
        mock_adapters['fs'].create_staging_context.return_value.__exit__ = Mock(return_value=None)

        # Execute installation
        results = installer.install_plan(sample_plan, dry_run=False)

        # Verify results
        assert "test-component" in results
        assert results["test-component"] is True

        # Verify staging context was used
        mock_adapters['fs'].create_staging_context.assert_called_once()

        # Verify receipt was saved
        mock_adapters['receipts'].save_receipt.assert_called()

    def test_dry_run_installation(self, installer, sample_plan, mock_adapters):
        """Test dry run doesn't modify filesystem."""
        # Execute dry run
        results = installer.install_plan(sample_plan, dry_run=True)

        # Verify results
        assert "test-component" in results
        assert results["test-component"] is True

        # Verify no staging context was created for dry run
        mock_adapters['fs'].create_staging_context.assert_not_called()

        # Verify no receipt was saved
        mock_adapters['receipts'].save_receipt.assert_not_called()

    def test_force_installation_overwrites(self, installer, sample_plan, mock_adapters):
        """Test force installation overwrites existing files."""
        # Mock file existence check
        def mock_exists(path):
            return str(path).endswith("file1.txt")

        with patch('pathlib.Path.exists', side_effect=mock_exists):
            # Execute force installation
            results = installer.install_plan(sample_plan, force=True)

            # Should succeed even with existing files
            assert results["test-component"] is True

    def test_rollback_on_component_failure(self, installer, sample_plan, mock_adapters):
        """Test rollback when a component fails."""
        # Mock first component success, second component failure
        def mock_execute_file_action(action, staging_dir):
            if "file2" in action.target_path:
                raise InstallationError("Template rendering failed")
            return True

        with patch.object(installer, '_execute_file_action', side_effect=mock_execute_file_action):
            # Should raise exception due to failure
            with pytest.raises(InstallationError):
                installer.install_plan(sample_plan)

        # Verify no receipt was saved due to rollback
        mock_adapters['receipts'].save_receipt.assert_not_called()

    def test_file_action_copy_operation(self, installer, temp_workspace, mock_adapters):
        """Test copy file action execution."""
        # Create source file
        source_file = temp_workspace / "source.txt"
        source_file.write_text("Test content")

        action = FileAction(
            source_path=str(source_file),
            target_path="output/target.txt",
            action_type="copy",
            content_hash="test"
        )

        staging_dir = temp_workspace / "staging"
        staging_dir.mkdir()

        # Execute file action
        result = installer._execute_file_action(action, staging_dir)

        # Verify success
        assert result is True

        # Verify file was copied to staging
        staged_file = staging_dir / "output" / "target.txt"
        assert staged_file.exists()
        assert staged_file.read_text() == "Test content"

    def test_file_action_template_operation(self, installer, temp_workspace, mock_adapters):
        """Test template file action execution."""
        # Create template source file
        source_file = temp_workspace / "template.j2"
        source_file.write_text("Hello {{ name }}!")

        action = FileAction(
            source_path=str(source_file),
            target_path="output/rendered.txt",
            action_type="template",
            content_hash="test",
            template_vars={"name": "World"}
        )

        staging_dir = temp_workspace / "staging"
        staging_dir.mkdir()

        # Mock yaml_ops template rendering
        mock_adapters['yaml_ops'].render_template.return_value = "Hello World!"

        # Execute file action
        result = installer._execute_file_action(action, staging_dir)

        # Verify success
        assert result is True

        # Verify template was rendered correctly
        mock_adapters['yaml_ops'].render_template.assert_called_once_with(
            str(source_file),
            {"name": "World"}
        )

        # Verify rendered content was written to staging
        staged_file = staging_dir / "output" / "rendered.txt"
        assert staged_file.exists()
        assert staged_file.read_text() == "Hello World!"

    def test_file_action_mkdir_operation(self, installer, temp_workspace, mock_adapters):
        """Test mkdir file action execution."""
        action = FileAction(
            source_path="",
            target_path="new/directory/",
            action_type="mkdir",
            content_hash=""
        )

        staging_dir = temp_workspace / "staging"
        staging_dir.mkdir()

        # Execute file action
        result = installer._execute_file_action(action, staging_dir)

        # Verify success
        assert result is True

        # Verify directory was created in staging
        staged_dir = staging_dir / "new" / "directory"
        assert staged_dir.exists()
        assert staged_dir.is_dir()

    def test_invalid_action_type_raises_error(self, installer, temp_workspace, mock_adapters):
        """Test that invalid action types raise appropriate errors."""
        action = FileAction(
            source_path="/some/path",
            target_path="output/file.txt",
            action_type="invalid_action",
            content_hash="test"
        )

        staging_dir = temp_workspace / "staging"
        staging_dir.mkdir()

        # Should raise error for invalid action type
        with pytest.raises(InstallationError, match="Unknown action type"):
            installer._execute_file_action(action, staging_dir)

    def test_missing_source_file_raises_error(self, installer, temp_workspace, mock_adapters):
        """Test that missing source files raise appropriate errors."""
        action = FileAction(
            source_path="/nonexistent/file.txt",
            target_path="output/file.txt",
            action_type="copy",
            content_hash="test"
        )

        staging_dir = temp_workspace / "staging"
        staging_dir.mkdir()

        # Should raise error for missing source file
        with pytest.raises(InstallationError, match="Source file not found"):
            installer._execute_file_action(action, staging_dir)

    def test_template_rendering_error_handling(self, installer, temp_workspace, mock_adapters):
        """Test that template rendering errors are handled properly."""
        # Create template source file
        source_file = temp_workspace / "template.j2"
        source_file.write_text("Hello {{ invalid_var }}!")

        action = FileAction(
            source_path=str(source_file),
            target_path="output/rendered.txt",
            action_type="template",
            content_hash="test",
            template_vars={"name": "World"}  # Missing invalid_var
        )

        staging_dir = temp_workspace / "staging"
        staging_dir.mkdir()

        # Mock yaml_ops to raise template error
        mock_adapters['yaml_ops'].render_template.side_effect = Exception("Template variable not found")

        # Should raise installation error
        with pytest.raises(InstallationError, match="Template rendering failed"):
            installer._execute_file_action(action, staging_dir)

    def test_component_receipt_creation(self, installer, sample_plan, mock_adapters):
        """Test that component receipts are created correctly."""
        # Mock successful operations
        mock_adapters['fs'].create_staging_context.return_value.__enter__ = Mock()
        mock_adapters['fs'].create_staging_context.return_value.__exit__ = Mock(return_value=None)

        # Execute installation
        installer.install_plan(sample_plan)

        # Verify receipt was saved with correct component info
        mock_adapters['receipts'].save_receipt.assert_called()

        # Get the call arguments
        call_args = mock_adapters['receipts'].save_receipt.call_args
        component_id = call_args[0][0]
        receipt = call_args[0][1]

        assert component_id == "test-component"
        assert receipt.component_id == "test-component"
        assert receipt.manifest_hash == "c" * 64

    def test_staging_directory_cleanup(self, installer, sample_plan, mock_adapters):
        """Test that staging directories are properly cleaned up."""
        # Mock context manager to verify cleanup behavior
        staging_context = Mock()
        mock_adapters['fs'].create_staging_context.return_value = staging_context

        # Execute installation
        installer.install_plan(sample_plan)

        # Verify context manager was used (ensures cleanup)
        staging_context.__enter__.assert_called_once()
        staging_context.__exit__.assert_called_once()

    def test_parallel_component_installation(self, installer, mock_adapters):
        """Test installation of multiple components."""
        # Create plan with multiple components
        components = []
        for i in range(3):
            file_action = FileAction(
                source_path=f"/templates/file{i}.txt",
                target_path=f"output/file{i}.txt",
                action_type="copy",
                content_hash=f"{i}" * 64
            )

            component = ComponentPlan(
                component_id=f"component-{i}",
                file_actions=[file_action],
                manifest_hash=f"{i}" * 64
            )
            components.append(component)

        plan = InstallPlan(
            profile="multi-component",
            components=components,
            target_dir=Path("/target")
        )

        # Mock successful operations
        mock_adapters['fs'].create_staging_context.return_value.__enter__ = Mock()
        mock_adapters['fs'].create_staging_context.return_value.__exit__ = Mock(return_value=None)

        # Execute installation
        results = installer.install_plan(plan)

        # Verify all components were installed
        assert len(results) == 3
        for i in range(3):
            assert f"component-{i}" in results
            assert results[f"component-{i}"] is True

        # Verify receipts were saved for all components
        assert mock_adapters['receipts'].save_receipt.call_count == 3
