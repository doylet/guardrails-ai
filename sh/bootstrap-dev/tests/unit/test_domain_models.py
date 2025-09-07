"""Unit tests for domain models.

Tests the core data structures to ensure they behave correctly
with validation, immutability, and edge cases.
"""

import pytest
from pathlib import Path
from datetime import datetime

from src.packages.domain.model import (
    FileAction,
    ComponentPlan,
    InstallPlan,
    Receipt,
)


class TestFileAction:
    """Test FileAction domain model."""

    def test_valid_file_action(self):
        """Test creating a valid FileAction."""
        action = FileAction(
            action_type="COPY",
            source_path=Path("templates/file.txt"),
            target_path=Path(".ai/file.txt"),
            target_hash="abc123",
            reason="new",
        )

        assert action.action_type == "COPY"
        assert action.source_path == Path("templates/file.txt")
        assert action.target_path == Path(".ai/file.txt")
        assert action.target_hash == "abc123"
        assert action.reason == "new"

        # Test legacy aliases
        assert action.kind == "COPY"
        assert action.src == Path("templates/file.txt")
        assert action.dst == Path(".ai/file.txt")

    def test_absolute_source_path_raises_error(self):
        """Test that absolute source paths are rejected."""
        with pytest.raises(ValueError, match="Source path must be relative"):
            FileAction(
                action_type="COPY",
                source_path=Path("/absolute/path"),
                target_path=Path("relative/path"),
            )

    def test_absolute_target_path_raises_error(self):
        """Test that absolute target paths are rejected."""
        with pytest.raises(ValueError, match="Target path must be relative"):
            FileAction(
                action_type="COPY",
                source_path=Path("relative/path"),
                target_path=Path("/absolute/path"),
            )

    def test_metadata_initialization(self):
        """Test that metadata is properly initialized."""
        action = FileAction(
            action_type="TEMPLATE",
            source_path=Path("template.yml"),
            target_path=Path("config.yml"),
        )

        assert action.metadata == {}

    def test_immutability(self):
        """Test that FileAction is immutable."""
        action = FileAction(
            action_type="COPY",
            source_path=Path("src"),
            target_path=Path("dst"),
        )

        with pytest.raises(AttributeError):
            action.action_type = "MERGE"


class TestComponentPlan:
    """Test ComponentPlan domain model."""

    def test_valid_component_plan(self):
        """Test creating a valid ComponentPlan."""
        actions = [
            FileAction(
                action_type="COPY",
                source_path=Path("file1.txt"),
                target_path=Path("file1.txt"),
            ),
            FileAction(
                action_type="MERGE",
                source_path=Path("file2.yml"),
                target_path=Path("file2.yml"),
            ),
        ]

        plan = ComponentPlan(
            component_id="test-component",
            file_actions=actions,
            manifest_hash="a" * 64,  # Valid SHA256 length
        )

        assert plan.component_id == "test-component"
        assert plan.file_actions == actions
        assert plan.manifest_hash == "a" * 64
        assert plan.plugin_id is None

        # Test legacy aliases
        assert plan.name == "test-component"
        assert plan.actions == actions
        assert plan.manifest_digest == "a" * 64

    def test_invalid_component_id_raises_error(self):
        """Test that invalid component IDs are rejected."""
        with pytest.raises(ValueError, match="Invalid component name"):
            ComponentPlan(
                component_id="invalid name with spaces",
                file_actions=[],
                manifest_hash="a" * 64,
            )

    def test_invalid_manifest_hash_raises_error(self):
        """Test that invalid manifest hashes are rejected."""
        with pytest.raises(ValueError, match="Invalid manifest digest format"):
            ComponentPlan(
                component_id="valid-component",
                file_actions=[],
                manifest_hash="too-short",
            )

    def test_total_files_property(self):
        """Test total_files property calculation."""
        actions = [
            FileAction("COPY", Path("f1"), Path("f1")),
            FileAction("MERGE", Path("f2"), Path("f2")),
            FileAction("SKIP", Path("f3"), Path("f3")),
        ]

        plan = ComponentPlan(
            component_id="test",
            file_actions=actions,
            manifest_hash="a" * 64,
        )

        assert plan.total_files == 3

    def test_actionable_files_property(self):
        """Test actionable_files property calculation."""
        actions = [
            FileAction("COPY", Path("f1"), Path("f1")),
            FileAction("MERGE", Path("f2"), Path("f2")),
            FileAction("SKIP", Path("f3"), Path("f3")),  # Not actionable
        ]

        plan = ComponentPlan(
            component_id="test",
            file_actions=actions,
            manifest_hash="a" * 64,
        )

        assert plan.actionable_files == 2


class TestInstallPlan:
    """Test InstallPlan domain model."""

    def test_valid_install_plan(self):
        """Test creating a valid InstallPlan."""
        component1 = ComponentPlan(
            component_id="comp1",
            file_actions=[FileAction("COPY", Path("f1"), Path("f1"))],
            manifest_hash="a" * 64,
        )
        component2 = ComponentPlan(
            component_id="comp2",
            file_actions=[FileAction("MERGE", Path("f2"), Path("f2"))],
            manifest_hash="b" * 64,
        )

        plan = InstallPlan(
            profile="test-profile",
            components=[component1, component2],
        )

        assert plan.profile == "test-profile"
        assert len(plan.components) == 2
        assert plan.total_files == 2  # Auto-calculated

    def test_file_count_mismatch_raises_error(self):
        """Test that file count mismatches are detected."""
        component = ComponentPlan(
            component_id="comp",
            file_actions=[FileAction("COPY", Path("f1"), Path("f1"))],
            manifest_hash="a" * 64,
        )

        with pytest.raises(ValueError, match="File count mismatch"):
            InstallPlan(
                profile="test",
                components=[component],
                total_files=999,  # Wrong count
            )

    def test_component_count_property(self):
        """Test component_count property."""
        components = [
            ComponentPlan("comp1", [], "a" * 64),
            ComponentPlan("comp2", [], "b" * 64),
        ]

        plan = InstallPlan(
            profile="test",
            components=components,
        )

        assert plan.component_count == 2

    def test_get_component_by_name(self):
        """Test getting components by name."""
        comp1 = ComponentPlan("comp1", [], "a" * 64)
        comp2 = ComponentPlan("comp2", [], "b" * 64)

        plan = InstallPlan(
            profile="test",
            components=[comp1, comp2],
        )

        assert plan.get_component("comp1") == comp1
        assert plan.get_component("comp2") == comp2
        assert plan.get_component("nonexistent") is None

    def test_has_conflicts_detection(self):
        """Test conflict detection for overlapping paths."""
        # No conflicts
        comp1 = ComponentPlan(
            "comp1",
            [FileAction("COPY", Path("src1"), Path("dst1"))],
            "a" * 64,
        )
        comp2 = ComponentPlan(
            "comp2",
            [FileAction("COPY", Path("src2"), Path("dst2"))],
            "b" * 64,
        )

        plan = InstallPlan("test", [comp1, comp2])
        assert not plan.has_conflicts()

        # With conflicts
        comp3 = ComponentPlan(
            "comp3",
            [FileAction("COPY", Path("src3"), Path("dst1"))],  # Same dst as comp1
            "c" * 64,
        )

        plan_with_conflicts = InstallPlan("test", [comp1, comp3])
        assert plan_with_conflicts.has_conflicts()

    def test_to_dict_serialization(self):
        """Test plan serialization to dictionary."""
        action = FileAction("COPY", Path("src"), Path("dst"), target_hash="hash123")
        component = ComponentPlan("comp1", [action], "a" * 64)
        plan = InstallPlan("test", [component])

        result = plan.to_dict()

        assert result["profile"] == "test"
        assert len(result["components"]) == 1
        assert result["components"][0]["component_id"] == "comp1"
        assert result["components"][0]["file_actions"][0]["action_type"] == "COPY"


class TestReceipt:
    """Test Receipt domain model."""

    def test_valid_receipt(self):
        """Test creating a valid Receipt."""
        actions = [FileAction("COPY", Path("src"), Path("dst"))]

        receipt = Receipt(
            component_id="test-component",
            installed_at="2025-09-07T10:00:00",
            manifest_hash="a" * 64,
            files=actions,
        )

        assert receipt.component_id == "test-component"
        assert receipt.installed_at == "2025-09-07T10:00:00"
        assert receipt.manifest_hash == "a" * 64
        assert receipt.files == actions
        assert receipt.metadata == {}

    def test_empty_component_id_raises_error(self):
        """Test that empty component IDs are rejected."""
        with pytest.raises(ValueError, match="Component ID cannot be empty"):
            Receipt(
                component_id="",
                installed_at="2025-09-07T10:00:00",
                manifest_hash="a" * 64,
                files=[],
            )

    def test_invalid_manifest_hash_raises_error(self):
        """Test that invalid manifest hashes are rejected."""
        with pytest.raises(ValueError, match="Invalid manifest hash format"):
            Receipt(
                component_id="test",
                installed_at="2025-09-07T10:00:00",
                manifest_hash="invalid",
                files=[],
            )

    def test_create_classmethod(self):
        """Test Receipt.create classmethod."""
        actions = [FileAction("COPY", Path("src"), Path("dst"))]

        receipt = Receipt.create(
            component_id="test",
            manifest_hash="a" * 64,
            files=actions,
            metadata={"test": "value"},
        )

        assert receipt.component_id == "test"
        assert receipt.manifest_hash == "a" * 64
        assert receipt.files == actions
        assert receipt.metadata == {"test": "value"}

        # Check timestamp is recent
        timestamp = datetime.fromisoformat(receipt.installed_at)
        now = datetime.now()
        assert (now - timestamp).total_seconds() < 60  # Within last minute

    def test_to_dict_serialization(self):
        """Test receipt serialization to dictionary."""
        action = FileAction("MERGE", Path("src"), Path("dst"), metadata={"key": "value"})
        receipt = Receipt(
            component_id="test",
            installed_at="2025-09-07T10:00:00",
            manifest_hash="a" * 64,
            files=[action],
            metadata={"receipt_meta": "data"},
        )

        result = receipt.to_dict()

        assert result["component_id"] == "test"
        assert result["installed_at"] == "2025-09-07T10:00:00"
        assert result["manifest_hash"] == "a" * 64
        assert len(result["files"]) == 1
        assert result["files"][0]["action_type"] == "MERGE"
        assert result["metadata"] == {"receipt_meta": "data"}
