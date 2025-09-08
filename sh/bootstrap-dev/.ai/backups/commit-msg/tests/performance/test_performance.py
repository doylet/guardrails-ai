"""Performance tests for installation and planning operations.

Tests timing constraints and resource usage to ensure
scalability of the architecture.
"""

import pytest
import time
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch

from src.packages.core import Orchestrator


class TestPerformanceConstraints:
    """Test performance characteristics of core operations."""

    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def large_template_repo(self, temp_workspace):
        """Create a large template repository for performance testing."""
        template_repo = temp_workspace / "large_templates"
        template_repo.mkdir()

        # Create many files to simulate larger installations
        for i in range(100):
            (template_repo / f"file_{i:03d}.txt").write_text(f"Content for file {i}")

        # Create some subdirectories
        for i in range(10):
            subdir = template_repo / f"subdir_{i}"
            subdir.mkdir()
            for j in range(10):
                (subdir / f"nested_{j}.txt").write_text(f"Nested content {i}-{j}")

        return template_repo

    @pytest.fixture
    def orchestrator(self, temp_workspace):
        """Create orchestrator for performance testing."""
        return Orchestrator(target_dir=temp_workspace / "target")

    def test_planning_performance(self, orchestrator, temp_workspace, large_template_repo):
        """Test that planning completes within reasonable time limits."""
        target_dir = temp_workspace / "target"
        target_dir.mkdir()

        with patch.object(orchestrator.resolver, 'resolve') as mock_resolve:
            from src.packages.core.resolver import ResolvedSpec, ComponentSpec

            # Create a large component spec
            files = {}
            for file_path in large_template_repo.rglob("*.txt"):
                rel_path = file_path.relative_to(large_template_repo)
                files[str(rel_path)] = str(file_path)

            component_spec = ComponentSpec(
                component_id="large-component",
                files=files,
                manifest_hash="a" * 64,
            )

            mock_resolve.return_value = ResolvedSpec(
                profile="large",
                components=[component_spec],
                target_dir=target_dir,
            )

            # Measure planning time
            start_time = time.time()
            plan = orchestrator.plan(profile="large")
            planning_time = time.time() - start_time

            # Should complete planning in reasonable time (< 1 second for 200 files)
            assert planning_time < 1.0, f"Planning took too long: {planning_time:.3f}s"

            # Verify plan was generated correctly
            assert plan.profile == "large"
            assert len(plan.components) == 1
            assert len(plan.components[0].file_actions) == len(files)

    def test_installation_performance(self, orchestrator, temp_workspace, large_template_repo):
        """Test that installation completes within reasonable time limits."""
        target_dir = temp_workspace / "target"
        target_dir.mkdir()

        with patch.object(orchestrator.resolver, 'resolve') as mock_resolve:
            from src.packages.core.resolver import ResolvedSpec, ComponentSpec

            # Create multiple smaller components (more realistic)
            components = []
            for i in range(10):
                files = {}
                for j in range(10):
                    file_path = large_template_repo / f"file_{i*10 + j:03d}.txt"
                    if file_path.exists():
                        files[f"component_{i}/file_{j}.txt"] = str(file_path)

                if files:
                    components.append(ComponentSpec(
                        component_id=f"component-{i}",
                        files=files,
                        manifest_hash=f"{i:02d}" * 32,
                    ))

            mock_resolve.return_value = ResolvedSpec(
                profile="multi-component",
                components=components,
                target_dir=target_dir,
            )

            # Measure installation time
            start_time = time.time()
            results = orchestrator.install(profile="multi-component")
            installation_time = time.time() - start_time

            # Should complete installation in reasonable time (< 5 seconds for 100 files)
            assert installation_time < 5.0, f"Installation took too long: {installation_time:.3f}s"

            # Verify installation was successful
            assert all(results.values()), f"Installation failed: {results}"

    def test_doctor_performance(self, orchestrator, temp_workspace, large_template_repo):
        """Test that health checks complete within reasonable time limits."""
        target_dir = temp_workspace / "target"
        target_dir.mkdir()

        # Install components first
        with patch.object(orchestrator.resolver, 'resolve') as mock_resolve:
            from src.packages.core.resolver import ResolvedSpec, ComponentSpec

            # Install a moderate number of files for health checking
            files = {}
            for i in range(50):
                file_path = large_template_repo / f"file_{i:03d}.txt"
                if file_path.exists():
                    files[f"health_file_{i}.txt"] = str(file_path)

            component_spec = ComponentSpec(
                component_id="health-component",
                files=files,
                manifest_hash="h" * 64,
            )

            mock_resolve.return_value = ResolvedSpec(
                profile="health",
                components=[component_spec],
                target_dir=target_dir,
            )

            # Install first
            orchestrator.install(profile="health")

            # Measure health check time
            start_time = time.time()
            diagnostics = orchestrator.doctor()
            doctor_time = time.time() - start_time

            # Should complete health check in reasonable time (< 2 seconds for 50 files)
            assert doctor_time < 2.0, f"Health check took too long: {doctor_time:.3f}s"

            # Should complete without errors
            errors = [d for d in diagnostics if d.severity == "error"]
            assert len(errors) == 0, f"Unexpected errors: {errors}"

    def test_memory_usage_stability(self, orchestrator, temp_workspace, large_template_repo):
        """Test that operations don't consume excessive memory."""
        import psutil
        import os

        target_dir = temp_workspace / "target"
        target_dir.mkdir()

        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        with patch.object(orchestrator.resolver, 'resolve') as mock_resolve:
            from src.packages.core.resolver import ResolvedSpec, ComponentSpec

            # Create a large number of small components
            components = []
            for i in range(20):
                files = {}
                for j in range(5):
                    file_path = large_template_repo / f"file_{i*5 + j:03d}.txt"
                    if file_path.exists():
                        files[f"memory_test_{i}_{j}.txt"] = str(file_path)

                if files:
                    components.append(ComponentSpec(
                        component_id=f"memory-test-{i}",
                        files=files,
                        manifest_hash=f"{i:02d}" * 32,
                    ))

            mock_resolve.return_value = ResolvedSpec(
                profile="memory-test",
                components=components,
                target_dir=target_dir,
            )

            # Perform multiple operations
            for _ in range(3):
                orchestrator.plan(profile="memory-test")
                orchestrator.install(profile="memory-test", force=True)
                orchestrator.doctor()

            # Check memory usage after operations
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory

            # Should not consume more than 50MB additional memory
            assert memory_increase < 50, f"Excessive memory usage: {memory_increase:.1f}MB increase"

    def test_concurrent_operations_safety(self, orchestrator, temp_workspace):
        """Test that concurrent operations don't interfere with each other."""
        import concurrent.futures

        target_dir = temp_workspace / "target"
        target_dir.mkdir()

        # Create separate template files for concurrent operations
        template_repo = temp_workspace / "concurrent_templates"
        template_repo.mkdir()

        for i in range(5):
            (template_repo / f"concurrent_{i}.txt").write_text(f"Content {i}")

        def install_component(component_id, file_name):
            """Install a single component."""
            try:
                with patch.object(orchestrator.resolver, 'resolve') as mock_resolve:
                    from src.packages.core.resolver import ResolvedSpec, ComponentSpec

                    component_spec = ComponentSpec(
                        component_id=component_id,
                        files={f"{component_id}.txt": str(template_repo / file_name)},
                        manifest_hash=component_id.encode().hex()[:64].ljust(64, '0'),
                    )

                    mock_resolve.return_value = ResolvedSpec(
                        profile=f"concurrent-{component_id}",
                        components=[component_spec],
                        target_dir=target_dir,
                    )

                    results = orchestrator.install(profile=f"concurrent-{component_id}")
                    return all(results.values())
            except Exception:
                return False

        # Run concurrent installations
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(install_component, f"component-{i}", f"concurrent_{i}.txt")
                for i in range(5)
            ]

            results = [future.result() for future in concurrent.futures.as_completed(futures)]

        # All installations should succeed
        assert all(results), f"Some concurrent installations failed: {results}"

        # Verify all files were created
        for i in range(5):
            expected_file = target_dir / f"component-{i}.txt"
            assert expected_file.exists(), f"File for component-{i} was not created"

    def test_large_file_handling(self, orchestrator, temp_workspace):
        """Test handling of larger files efficiently."""
        target_dir = temp_workspace / "target"
        target_dir.mkdir()

        # Create a large template file (1MB)
        large_template = temp_workspace / "large_file.txt"
        large_content = "A" * (1024 * 1024)  # 1MB of 'A's
        large_template.write_text(large_content)

        with patch.object(orchestrator.resolver, 'resolve') as mock_resolve:
            from src.packages.core.resolver import ResolvedSpec, ComponentSpec

            component_spec = ComponentSpec(
                component_id="large-file-component",
                files={"large_output.txt": str(large_template)},
                manifest_hash="l" * 64,
            )

            mock_resolve.return_value = ResolvedSpec(
                profile="large-file",
                components=[component_spec],
                target_dir=target_dir,
            )

            # Measure time to handle large file
            start_time = time.time()
            results = orchestrator.install(profile="large-file")
            large_file_time = time.time() - start_time

            # Should handle 1MB file efficiently (< 3 seconds)
            assert large_file_time < 3.0, f"Large file handling took too long: {large_file_time:.3f}s"

            # Verify file was copied correctly
            assert all(results.values()), "Large file installation failed"

            output_file = target_dir / "large_output.txt"
            assert output_file.exists(), "Large file was not created"
            assert output_file.stat().st_size == len(large_content), "Large file size mismatch"

    def test_repeated_operations_performance(self, orchestrator, temp_workspace):
        """Test that repeated operations maintain consistent performance."""
        target_dir = temp_workspace / "target"
        target_dir.mkdir()

        # Create template
        template_repo = temp_workspace / "repeat_templates"
        template_repo.mkdir()
        (template_repo / "repeat.txt").write_text("Repeated content")

        with patch.object(orchestrator.resolver, 'resolve') as mock_resolve:
            from src.packages.core.resolver import ResolvedSpec, ComponentSpec

            component_spec = ComponentSpec(
                component_id="repeat-component",
                files={"repeat_output.txt": str(template_repo / "repeat.txt")},
                manifest_hash="r" * 64,
            )

            mock_resolve.return_value = ResolvedSpec(
                profile="repeat",
                components=[component_spec],
                target_dir=target_dir,
            )

            # Measure time for repeated operations
            times = []
            for i in range(5):
                start_time = time.time()

                # Force reinstall each time
                results = orchestrator.install(profile="repeat", force=True)
                assert all(results.values()), f"Repeat {i} failed"

                operation_time = time.time() - start_time
                times.append(operation_time)

            # Times should be consistent (no significant degradation)
            avg_time = sum(times) / len(times)
            max_time = max(times)

            # No operation should take more than 2x the average time
            assert max_time < avg_time * 2, f"Performance degradation detected: {times}"

            # All operations should complete quickly
            assert all(t < 1.0 for t in times), f"Some operations were too slow: {times}"
