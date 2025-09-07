"""Unit tests for the doctor component.

Tests health checks, drift detection, and repair capabilities.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

from src.packages.core.doctor import Doctor
from src.packages.domain.model import Receipt


class TestDoctor:
    """Test doctor health check and repair functionality."""

    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def mock_adapters(self):
        """Create mock adapters for testing."""
        receipts_adapter = Mock()
        hashing_adapter = Mock()

        return {
            'receipts': receipts_adapter,
            'hashing': hashing_adapter
        }

    @pytest.fixture
    def doctor(self, temp_workspace, mock_adapters):
        """Create doctor with mocked adapters."""
        return Doctor(
            target_dir=temp_workspace,
            receipts_adapter=mock_adapters['receipts'],
            hashing_adapter=mock_adapters['hashing']
        )

    @pytest.fixture
    def sample_receipts(self):
        """Create sample receipts for testing."""
        return [
            Receipt(
                component_id="component-1",
                installed_files=["file1.txt", "file2.txt"],
                manifest_hash="a" * 64,
                install_timestamp="2024-01-01T12:00:00Z"
            ),
            Receipt(
                component_id="component-2",
                installed_files=["config.yml"],
                manifest_hash="b" * 64,
                install_timestamp="2024-01-01T12:01:00Z"
            )
        ]

    def test_healthy_system_diagnosis(self, doctor, temp_workspace, mock_adapters, sample_receipts):
        """Test diagnosis of a healthy system with no issues."""
        # Setup: Create all expected files
        (temp_workspace / "file1.txt").write_text("content1")
        (temp_workspace / "file2.txt").write_text("content2")
        (temp_workspace / "config.yml").write_text("config: value")

        # Mock receipts and hashing
        mock_adapters['receipts'].list_receipts.return_value = sample_receipts
        mock_adapters['hashing'].hash_file.side_effect = [
            "hash1", "hash2", "hash3"  # All hashes match expectations
        ]

        # Run diagnosis
        diagnostics = doctor.diagnose()

        # Should have no errors or warnings for healthy system
        errors = [d for d in diagnostics if d.severity == "error"]
        warnings = [d for d in diagnostics if d.severity == "warning"]

        assert len(errors) == 0, f"Unexpected errors: {errors}"
        assert len(warnings) == 0, f"Unexpected warnings: {warnings}"

        # Should have info messages about healthy components
        info_messages = [d for d in diagnostics if d.severity == "info"]
        assert len(info_messages) >= 2  # At least one per component

    def test_missing_file_detection(self, doctor, temp_workspace, mock_adapters, sample_receipts):
        """Test detection of missing installed files."""
        # Setup: Only create some expected files
        (temp_workspace / "file1.txt").write_text("content1")
        # file2.txt and config.yml are missing

        # Mock receipts
        mock_adapters['receipts'].list_receipts.return_value = sample_receipts

        # Run diagnosis
        diagnostics = doctor.diagnose()

        # Should detect missing files as errors
        errors = [d for d in diagnostics if d.severity == "error"]
        missing_errors = [e for e in errors if "missing" in e.message.lower()]

        assert len(missing_errors) >= 2, f"Should detect missing files: {errors}"

        # Check specific missing files are mentioned
        error_messages = " ".join([e.message for e in missing_errors])
        assert "file2.txt" in error_messages
        assert "config.yml" in error_messages

    def test_file_content_drift_detection(self, doctor, temp_workspace, mock_adapters, sample_receipts):
        """Test detection of file content changes (drift)."""
        # Setup: Create files with different content than expected
        (temp_workspace / "file1.txt").write_text("modified content")
        (temp_workspace / "file2.txt").write_text("content2")
        (temp_workspace / "config.yml").write_text("config: modified")

        # Mock receipts
        mock_adapters['receipts'].list_receipts.return_value = sample_receipts

        # Mock hashing to show content differences
        def mock_hash_file(file_path):
            if "file1.txt" in str(file_path):
                return "different_hash1"  # Content changed
            elif "config.yml" in str(file_path):
                return "different_hash3"  # Content changed
            else:
                return "original_hash2"  # Content unchanged

        mock_adapters['hashing'].hash_file.side_effect = mock_hash_file

        # Also need to mock the expected hashes from receipts
        with patch.object(doctor, '_get_expected_file_hash') as mock_expected:
            mock_expected.side_effect = lambda component_id, file_path: "original_hash"

            # Run diagnosis
            diagnostics = doctor.diagnose()

            # Should detect content drift as warnings
            warnings = [d for d in diagnostics if d.severity == "warning"]
            drift_warnings = [w for w in warnings if "drift" in w.message.lower()]

            assert len(drift_warnings) >= 2, f"Should detect content drift: {warnings}"

            # Check specific files with drift are mentioned
            warning_messages = " ".join([w.message for w in drift_warnings])
            assert "file1.txt" in warning_messages
            assert "config.yml" in warning_messages

    def test_orphaned_receipt_detection(self, doctor, temp_workspace, mock_adapters):
        """Test detection of receipts for uninstalled components."""
        # Setup: No files in target directory

        # Mock receipts that reference missing files
        orphaned_receipts = [
            Receipt(
                component_id="orphaned-component",
                installed_files=["nonexistent.txt"],
                manifest_hash="x" * 64,
                install_timestamp="2024-01-01T12:00:00Z"
            )
        ]

        mock_adapters['receipts'].list_receipts.return_value = orphaned_receipts

        # Run diagnosis
        diagnostics = doctor.diagnose()

        # Should detect orphaned receipts as warnings
        warnings = [d for d in diagnostics if d.severity == "warning"]
        orphan_warnings = [w for w in warnings if "orphaned" in w.message.lower()]

        assert len(orphan_warnings) >= 1, f"Should detect orphaned receipts: {warnings}"

    def test_corrupted_receipt_handling(self, doctor, temp_workspace, mock_adapters):
        """Test handling of corrupted or invalid receipts."""
        # Mock receipts adapter to raise exception
        mock_adapters['receipts'].list_receipts.side_effect = Exception("Corrupted receipt data")

        # Run diagnosis
        diagnostics = doctor.diagnose()

        # Should report receipt corruption as error
        errors = [d for d in diagnostics if d.severity == "error"]
        corruption_errors = [e for e in errors if "receipt" in e.message.lower()]

        assert len(corruption_errors) >= 1, f"Should detect receipt corruption: {errors}"

    def test_repair_missing_files(self, doctor, temp_workspace, mock_adapters, sample_receipts):
        """Test repair functionality for missing files."""
        # Setup: Missing files scenario
        (temp_workspace / "file1.txt").write_text("content1")
        # file2.txt and config.yml are missing

        mock_adapters['receipts'].list_receipts.return_value = sample_receipts

        # Mock the repair process
        with patch.object(doctor, '_repair_missing_file') as mock_repair:
            mock_repair.return_value = True

            # Run repair
            repair_results = doctor.repair()

            # Should attempt to repair missing files
            assert "component-1" in repair_results
            assert "component-2" in repair_results

            # Verify repair was attempted for missing files
            assert mock_repair.call_count >= 2

    def test_repair_drift_files(self, doctor, temp_workspace, mock_adapters, sample_receipts):
        """Test repair functionality for drifted files."""
        # Setup: Files with modified content
        (temp_workspace / "file1.txt").write_text("modified content")
        (temp_workspace / "file2.txt").write_text("content2")
        (temp_workspace / "config.yml").write_text("modified config")

        mock_adapters['receipts'].list_receipts.return_value = sample_receipts

        # Mock hashing to detect drift
        mock_adapters['hashing'].hash_file.side_effect = [
            "different_hash", "original_hash", "different_hash"
        ]

        # Mock the repair process
        with patch.object(doctor, '_repair_drifted_file') as mock_repair:
            mock_repair.return_value = True

            with patch.object(doctor, '_get_expected_file_hash') as mock_expected:
                mock_expected.return_value = "original_hash"

                # Run repair
                doctor.repair()

                # Should attempt to repair drifted files
                assert mock_repair.call_count >= 2  # For drifted files

    def test_clean_orphaned_receipts(self, doctor, temp_workspace, mock_adapters):
        """Test cleaning of orphaned receipts."""
        # Setup: Orphaned receipt scenario
        orphaned_receipts = [
            Receipt(
                component_id="orphaned-component",
                installed_files=["nonexistent.txt"],
                manifest_hash="x" * 64,
                install_timestamp="2024-01-01T12:00:00Z"
            )
        ]

        mock_adapters['receipts'].list_receipts.return_value = orphaned_receipts

        # Mock cleanup
        with patch.object(doctor, '_clean_orphaned_receipt') as mock_clean:
            mock_clean.return_value = True

            # Run repair
            doctor.repair()

            # Should clean orphaned receipts
            assert mock_clean.call_count >= 1

    def test_validate_component_integrity(self, doctor, temp_workspace, mock_adapters):
        """Test validation of individual component integrity."""
        # Create component files
        (temp_workspace / "component_file.txt").write_text("component content")

        receipt = Receipt(
            component_id="test-component",
            installed_files=["component_file.txt"],
            manifest_hash="a" * 64,
            install_timestamp="2024-01-01T12:00:00Z"
        )

        # Mock expected hash
        with patch.object(doctor, '_get_expected_file_hash') as mock_expected:
            mock_expected.return_value = "correct_hash"
            mock_adapters['hashing'].hash_file.return_value = "correct_hash"

            # Validate component
            is_valid = doctor.validate_component("test-component", receipt)

            assert is_valid is True

    def test_validate_component_with_missing_files(self, doctor, temp_workspace, mock_adapters):
        """Test validation fails for components with missing files."""
        receipt = Receipt(
            component_id="test-component",
            installed_files=["missing_file.txt"],
            manifest_hash="a" * 64,
            install_timestamp="2024-01-01T12:00:00Z"
        )

        # Validate component (file doesn't exist)
        is_valid = doctor.validate_component("test-component", receipt)

        assert is_valid is False

    def test_generate_health_report(self, doctor, temp_workspace, mock_adapters, sample_receipts):
        """Test generation of comprehensive health reports."""
        # Setup healthy system
        (temp_workspace / "file1.txt").write_text("content1")
        (temp_workspace / "file2.txt").write_text("content2")
        (temp_workspace / "config.yml").write_text("config: value")

        mock_adapters['receipts'].list_receipts.return_value = sample_receipts
        mock_adapters['hashing'].hash_file.side_effect = ["hash1", "hash2", "hash3"]

        # Generate report
        with patch.object(doctor, '_get_expected_file_hash') as mock_expected:
            mock_expected.return_value = "hash1"  # All hashes match

            report = doctor.generate_health_report()

            # Should contain summary information
            assert "components_checked" in report
            assert "files_verified" in report
            assert "issues_found" in report

            # For healthy system
            assert report["components_checked"] == 2
            assert report["files_verified"] == 3
            assert report["issues_found"] == 0

    def test_error_handling_during_diagnosis(self, doctor, temp_workspace, mock_adapters):
        """Test error handling during diagnosis operations."""
        # Mock receipts to raise unexpected error
        mock_adapters['receipts'].list_receipts.side_effect = Exception("Unexpected error")

        # Diagnosis should handle errors gracefully
        diagnostics = doctor.diagnose()

        # Should report the error but not crash
        errors = [d for d in diagnostics if d.severity == "error"]
        assert len(errors) >= 1

        # Error should mention the issue
        error_messages = " ".join([e.message for e in errors])
        assert "error" in error_messages.lower()

    def test_performance_diagnosis_large_installation(self, doctor, temp_workspace, mock_adapters):
        """Test diagnosis performance with many components and files."""
        # Create many receipts with multiple files each
        receipts = []
        for i in range(20):
            files = [f"component_{i}/file_{j}.txt" for j in range(10)]

            # Create the actual files
            comp_dir = temp_workspace / f"component_{i}"
            comp_dir.mkdir(exist_ok=True)
            for j in range(10):
                (comp_dir / f"file_{j}.txt").write_text(f"content {i}-{j}")

            receipt = Receipt(
                component_id=f"component-{i}",
                installed_files=files,
                manifest_hash=f"{i:02d}" * 32,
                install_timestamp="2024-01-01T12:00:00Z"
            )
            receipts.append(receipt)

        mock_adapters['receipts'].list_receipts.return_value = receipts
        mock_adapters['hashing'].hash_file.return_value = "consistent_hash"

        # Mock expected hashes
        with patch.object(doctor, '_get_expected_file_hash') as mock_expected:
            mock_expected.return_value = "consistent_hash"

            # Run diagnosis - should complete without issues
            import time
            start_time = time.time()
            diagnostics = doctor.diagnose()
            diagnosis_time = time.time() - start_time

            # Should complete quickly even with many files
            assert diagnosis_time < 5.0, f"Diagnosis took too long: {diagnosis_time:.3f}s"

            # Should successfully check all components
            info_messages = [d for d in diagnostics if d.severity == "info"]
            assert len(info_messages) >= 20  # At least one per component
