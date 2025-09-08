"""Unit tests for the Planner component.

Tests the pure planning logic to ensure deterministic behavior
and correct file action generation.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from src.packages.core.planner import Planner
from src.packages.core.resolver import ResolvedSpec, ComponentSpec
from src.packages.domain.model import InstallPlan


class TestPlanner:
    """Test Planner component."""

    @pytest.fixture
    def mock_receipts_adapter(self):
        """Mock receipts adapter."""
        mock = Mock()
        mock.is_current.return_value = False
        return mock

    @pytest.fixture
    def mock_hashing_adapter(self):
        """Mock hashing adapter."""
        mock = Mock()
        mock.hash_file.return_value = "abc123hash"
        return mock

    @pytest.fixture
    def planner(self, mock_receipts_adapter, mock_hashing_adapter):
        """Create planner instance with mocked dependencies."""
        return Planner(
            receipts_adapter=mock_receipts_adapter,
            hashing_adapter=mock_hashing_adapter,
        )

    def test_plan_single_component(self, planner, tmp_path):
        """Test planning a single component."""
        # Create test files
        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        test_file = template_dir / "test.txt"
        test_file.write_text("test content")

        # Create component spec
        component_spec = ComponentSpec(
            component_id="test-component",
            files={"test.txt": str(test_file)},
            manifest_hash="a" * 64,
        )

        # Create resolved spec
        resolved_spec = ResolvedSpec(
            profile="test",
            components=[component_spec],
            target_dir=tmp_path / "target",
        )

        # Plan installation
        result = planner.plan(resolved_spec)

        assert isinstance(result, InstallPlan)
        assert result.profile == "test"
        assert len(result.components) == 1

        component_plan = result.components[0]
        assert component_plan.component_id == "test-component"
        assert len(component_plan.file_actions) == 1

        action = component_plan.file_actions[0]
        assert action.action_type == "COPY"
        assert action.source_path == test_file
        assert action.reason == "new"

    def test_plan_determines_correct_action_types(self, planner, tmp_path):
        """Test that planner determines correct action types."""
        # Setup template files
        template_dir = tmp_path / "templates"
        template_dir.mkdir()

        copy_file = template_dir / "copy.txt"
        copy_file.write_text("copy content")

        merge_file = template_dir / "merge.yml"
        merge_file.write_text("key: value")

        template_file = template_dir / "template.j2"
        template_file.write_text("Hello {{ name }}")

        # Setup target files (some exist, some don't)
        target_dir = tmp_path / "target"
        target_dir.mkdir()

        existing_merge = target_dir / "merge.yml"
        existing_merge.write_text("existing: content")

        # Create component spec
        component_spec = ComponentSpec(
            component_id="test",
            files={
                "copy.txt": str(copy_file),
                "merge.yml": str(merge_file),
                "template.j2": str(template_file),
            },
            manifest_hash="a" * 64,
        )

        resolved_spec = ResolvedSpec(
            profile="test",
            components=[component_spec],
            target_dir=target_dir,
        )

        # Mock file type detection
        with patch.object(planner, '_determine_action_type') as mock_determine:
            mock_determine.side_effect = ["COPY", "MERGE", "TEMPLATE"]

            result = planner.plan(resolved_spec)

        actions = result.components[0].file_actions
        assert len(actions) == 3

        action_types = [action.action_type for action in actions]
        assert "COPY" in action_types
        assert "MERGE" in action_types
        assert "TEMPLATE" in action_types

    def test_plan_skips_current_components(self, planner, tmp_path):
        """Test that planner skips components that are current."""
        # Mock receipts adapter to say component is current
        planner.receipts_adapter.is_current.return_value = True

        component_spec = ComponentSpec(
            component_id="current-component",
            files={"test.txt": "path"},
            manifest_hash="a" * 64,
        )

        resolved_spec = ResolvedSpec(
            profile="test",
            components=[component_spec],
            target_dir=tmp_path,
        )

        result = planner.plan(resolved_spec)

        # Should still include component but with SKIP actions
        assert len(result.components) == 1
        component_plan = result.components[0]

        # All actions should be SKIP with "unchanged" reason
        for action in component_plan.file_actions:
            assert action.action_type == "SKIP"
            assert action.reason == "unchanged"

    def test_plan_with_force_overwrites_current(self, planner, tmp_path):
        """Test that force flag overwrites current components."""
        # Setup
        planner.receipts_adapter.is_current.return_value = True

        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        test_file = template_dir / "test.txt"
        test_file.write_text("content")

        component_spec = ComponentSpec(
            component_id="current-component",
            files={"test.txt": str(test_file)},
            manifest_hash="a" * 64,
        )

        resolved_spec = ResolvedSpec(
            profile="test",
            components=[component_spec],
            target_dir=tmp_path / "target",
        )

        # Plan with force=True
        result = planner.plan(resolved_spec, force=True)

        # Should include component with actual actions
        component_plan = result.components[0]
        actions = [a for a in component_plan.file_actions if a.action_type != "SKIP"]
        assert len(actions) > 0

    def test_plan_calculates_totals_correctly(self, planner, tmp_path):
        """Test that plan calculates file counts and size correctly."""
        # Create multiple components with files
        template_dir = tmp_path / "templates"
        template_dir.mkdir()

        # Component 1: 2 files
        comp1_files = {
            "file1.txt": str(template_dir / "file1.txt"),
            "file2.txt": str(template_dir / "file2.txt"),
        }
        for path in comp1_files.values():
            Path(path).write_text("content")

        # Component 2: 1 file
        comp2_files = {
            "file3.txt": str(template_dir / "file3.txt"),
        }
        for path in comp2_files.values():
            Path(path).write_text("content")

        component_specs = [
            ComponentSpec("comp1", comp1_files, "a" * 64),
            ComponentSpec("comp2", comp2_files, "b" * 64),
        ]

        resolved_spec = ResolvedSpec(
            profile="test",
            components=component_specs,
            target_dir=tmp_path / "target",
        )

        result = planner.plan(resolved_spec)

        assert result.total_files == 3
        assert result.component_count == 2
        assert result.estimated_size > 0

    def test_deterministic_planning(self, planner, tmp_path):
        """Test that planning is deterministic for same inputs."""
        # Setup identical specs
        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        test_file = template_dir / "test.txt"
        test_file.write_text("content")

        component_spec = ComponentSpec(
            component_id="test",
            files={"test.txt": str(test_file)},
            manifest_hash="a" * 64,
        )

        resolved_spec = ResolvedSpec(
            profile="test",
            components=[component_spec],
            target_dir=tmp_path / "target",
        )

        # Plan twice
        result1 = planner.plan(resolved_spec)
        result2 = planner.plan(resolved_spec)

        # Results should be identical
        assert result1.profile == result2.profile
        assert result1.total_files == result2.total_files
        assert len(result1.components) == len(result2.components)

        # Component plans should be identical
        comp1, comp2 = result1.components[0], result2.components[0]
        assert comp1.component_id == comp2.component_id
        assert comp1.manifest_hash == comp2.manifest_hash
        assert len(comp1.file_actions) == len(comp2.file_actions)

    def test_error_handling(self, planner):
        """Test error handling in planning."""
        # Test with invalid resolved spec
        with pytest.raises(Exception):  # Specific error type depends on implementation
            planner.plan(None)

        # Test with missing source files
        component_spec = ComponentSpec(
            component_id="test",
            files={"nonexistent.txt": "/does/not/exist"},
            manifest_hash="a" * 64,
        )

        resolved_spec = ResolvedSpec(
            profile="test",
            components=[component_spec],
            target_dir=Path("/tmp/target"),
        )

        with pytest.raises(Exception):  # Should fail when trying to access missing file
            planner.plan(resolved_spec)

    def test_action_type_determination(self, planner):
        """Test the _determine_action_type method."""
        # Test file extension-based detection
        assert planner._determine_action_type(Path("file.yml"), Path("target")) == "MERGE"
        assert planner._determine_action_type(Path("file.yaml"), Path("target")) == "MERGE"
        assert planner._determine_action_type(Path("file.json"), Path("target")) == "MERGE"
        assert planner._determine_action_type(Path("file.j2"), Path("target")) == "TEMPLATE"
        assert planner._determine_action_type(Path("file.template"), Path("target")) == "TEMPLATE"
        assert planner._determine_action_type(Path("file.txt"), Path("target")) == "COPY"

    def test_drift_detection(self, planner, tmp_path):
        """Test drift detection in planning."""
        # Setup files with different hashes
        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        source_file = template_dir / "test.txt"
        source_file.write_text("new content")

        target_dir = tmp_path / "target"
        target_dir.mkdir()
        target_file = target_dir / "test.txt"
        target_file.write_text("old content")

        # Mock different hashes for source and target
        planner.hashing_adapter.hash_file.side_effect = lambda path: (
            "new_hash" if "templates" in str(path) else "old_hash"
        )

        component_spec = ComponentSpec(
            component_id="test",
            files={"test.txt": str(source_file)},
            manifest_hash="a" * 64,
        )

        resolved_spec = ResolvedSpec(
            profile="test",
            components=[component_spec],
            target_dir=target_dir,
        )

        result = planner.plan(resolved_spec)
        action = result.components[0].file_actions[0]

        # Should detect drift and plan to update
        assert action.reason == "hash-diff"
