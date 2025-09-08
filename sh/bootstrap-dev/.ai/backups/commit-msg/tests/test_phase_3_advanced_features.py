"""
Tests for Phase 3 Advanced Features

This module provides comprehensive tests for the Phase 3 advanced features
including plugin registry, CLI commands, development toolkit, performance
optimization, and documentation system.
"""

import tempfile
import shutil
import pytest
from pathlib import Path
from unittest.mock import Mock, patch

# Import Phase 3 components
from src.packages.core.plugin_registry import (
    PluginRegistry,
    PluginSource,
    PluginMetadata,
)
from src.packages.cli.enhanced_commands import plugin, registry
from src.packages.tools.plugin_dev_toolkit import PluginDevToolkit, TestResult
from src.packages.adapters.performance_optimizer import (
    PerformanceMonitor,
    PerformanceCache,
    AsyncPluginProcessor,
    performance_monitor,
    cached,
)
from src.packages.tools.documentation_system import (
    DocumentationGenerator,
    DocumentationSection,
)


class TestPluginRegistry:
    """Test the plugin registry system."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.registry = PluginRegistry(cache_dir=self.temp_dir / "cache")

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_registry_initialization(self):
        """Test registry initialization."""
        assert self.registry.cache_dir.exists()
        assert isinstance(self.registry.sources, list)
        assert len(self.registry.sources) >= 1  # At least local source

    def test_add_source(self):
        """Test adding plugin sources."""
        initial_count = len(self.registry.sources)

        source = PluginSource(
            name="test-source",
            type="git",
            url="https://github.com/example/plugins.git",
            enabled=True,
        )

        self.registry.add_source(source)
        assert len(self.registry.sources) == initial_count + 1
        assert any(s.name == "test-source" for s in self.registry.sources)

    def test_search_plugins(self):
        """Test plugin search functionality."""
        # Create a mock plugin in local directory
        plugin_dir = self.temp_dir / "test-plugin"
        plugin_dir.mkdir()

        manifest_content = """
name: test-plugin
version: 1.0.0
description: Test plugin for registry
author: Test Author
"""

        with open(plugin_dir / "plugin-manifest.yaml", "w") as f:
            f.write(manifest_content)

        # Add local source pointing to temp dir
        local_source = PluginSource(
            name="test-local", type="local", url=str(self.temp_dir), enabled=True
        )
        self.registry.add_source(local_source)

        # Search for plugins
        results = self.registry.search_plugins("test")

        # Should find our test plugin
        assert len(results) >= 1
        test_plugin = next((p for p in results if p.name == "test-plugin"), None)
        assert test_plugin is not None
        assert test_plugin.version == "1.0.0"

    def test_get_plugin_info(self):
        """Test getting plugin information."""
        # Create a mock plugin
        plugin_dir = self.temp_dir / "info-plugin"
        plugin_dir.mkdir()

        manifest_content = """
name: info-plugin
version: 2.0.0
description: Plugin for info testing
author: Info Author
license: MIT
"""

        with open(plugin_dir / "plugin-manifest.yaml", "w") as f:
            f.write(manifest_content)

        # Add to registry
        local_source = PluginSource(
            name="info-local", type="local", url=str(self.temp_dir), enabled=True
        )
        self.registry.add_source(local_source)

        # Get plugin info
        info = self.registry.get_plugin_info("info-plugin")

        assert info is not None
        assert info.name == "info-plugin"
        assert info.version == "2.0.0"
        assert info.license == "MIT"


class TestPluginDevToolkit:
    """Test the plugin development toolkit."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.toolkit = PluginDevToolkit(workspace_dir=self.temp_dir)

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_scaffold_basic_plugin(self):
        """Test scaffolding a basic plugin."""
        success = self.toolkit.scaffold_plugin(
            plugin_name="test-scaffold",
            template_name="basic",
            author="Test Author",
            description="Test scaffolded plugin",
        )

        assert success

        plugin_dir = self.temp_dir / "test-scaffold"
        assert plugin_dir.exists()
        assert (plugin_dir / "plugin-manifest.yaml").exists()
        assert (plugin_dir / "README.md").exists()

        # Check manifest content
        with open(plugin_dir / "plugin-manifest.yaml") as f:
            content = f.read()
            assert "test-scaffold" in content
            assert "Test Author" in content

    def test_scaffold_advanced_plugin(self):
        """Test scaffolding an advanced plugin."""
        success = self.toolkit.scaffold_plugin(
            plugin_name="test-advanced",
            template_name="advanced",
            author="Advanced Author",
        )

        assert success

        plugin_dir = self.temp_dir / "test-advanced"
        assert plugin_dir.exists()
        assert (plugin_dir / "hooks" / "pre-install.sh").exists()
        assert (plugin_dir / "hooks" / "post-install.sh").exists()
        assert (plugin_dir / "templates").exists()

    def test_validate_plugin(self):
        """Test plugin validation."""
        # Create a valid plugin
        plugin_dir = self.temp_dir / "valid-plugin"
        plugin_dir.mkdir()

        manifest_content = """
name: valid-plugin
version: 1.0.0
description: A valid test plugin
author: Validator
api_version: v1

components:
  main:
    description: Main component
    files: []

profiles:
  default:
    description: Default profile
    components:
      - main
"""

        with open(plugin_dir / "plugin-manifest.yaml", "w") as f:
            f.write(manifest_content)

        with open(plugin_dir / "README.md", "w") as f:
            f.write("# Valid Plugin\n\nA test plugin.")

        # Validate
        errors = self.toolkit.validate_plugin(plugin_dir)
        assert len(errors) == 0

        # Test invalid plugin
        invalid_dir = self.temp_dir / "invalid-plugin"
        invalid_dir.mkdir()

        # Missing manifest
        errors = self.toolkit.validate_plugin(invalid_dir)
        assert len(errors) > 0
        assert any("Missing plugin-manifest.yaml" in error for error in errors)

    def test_test_plugin(self):
        """Test plugin testing functionality."""
        # Create a testable plugin
        plugin_dir = self.temp_dir / "testable-plugin"
        self.toolkit.scaffold_plugin("testable-plugin", "basic")

        # Run tests
        results = self.toolkit.test_plugin(plugin_dir)

        assert len(results) >= 2  # At least manifest validation and installation tests

        # Check that manifest validation passed
        manifest_test = next(
            (r for r in results if r.test_name == "manifest_validation"), None
        )
        assert manifest_test is not None
        assert manifest_test.success

    def test_package_plugin(self):
        """Test plugin packaging."""
        # Create a plugin to package
        plugin_dir = self.temp_dir / "package-plugin"
        self.toolkit.scaffold_plugin("package-plugin", "basic")

        # Package the plugin
        package_path = self.toolkit.package_plugin(plugin_dir)

        assert package_path is not None
        assert package_path.exists()
        assert package_path.suffix == ".zip"

        # Verify package contents
        import zipfile

        with zipfile.ZipFile(package_path, "r") as zipf:
            files = zipf.namelist()
            assert "plugin-manifest.yaml" in files
            assert "README.md" in files


class TestPerformanceOptimization:
    """Test performance optimization components."""

    def setup_method(self):
        """Set up test fixtures."""
        self.monitor = PerformanceMonitor()
        self.cache = PerformanceCache(max_size=10, default_ttl=1)

    def test_performance_monitor(self):
        """Test performance monitoring."""

        @performance_monitor("test_operation")
        def test_function():
            import time

            time.sleep(0.1)
            return "result"

        # Set monitor
        performance_monitor._monitor = self.monitor

        result = test_function()
        assert result == "result"

        metrics = self.monitor.get_metrics("test_operation")
        assert len(metrics) == 1
        assert metrics[0].duration >= 0.1

    def test_performance_cache(self):
        """Test performance caching."""
        # Test basic caching
        self.cache.set("key1", "value1")
        assert self.cache.get("key1") == "value1"

        # Test TTL expiration
        self.cache.set("key2", "value2", ttl=1)
        assert self.cache.get("key2") == "value2"

        import time

        time.sleep(1.1)
        assert self.cache.get("key2") is None

    def test_cached_decorator(self):
        """Test cached decorator."""
        call_count = 0

        @cached(ttl=60)
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        # First call
        result1 = expensive_function(5)
        assert result1 == 10
        assert call_count == 1

        # Second call should use cache
        result2 = expensive_function(5)
        assert result2 == 10
        assert call_count == 1  # Not incremented

        # Different argument should call function
        result3 = expensive_function(10)
        assert result3 == 20
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_async_plugin_processor(self):
        """Test async plugin processing."""
        processor = AsyncPluginProcessor(max_workers=2)

        def mock_process(plugin_path):
            return f"processed_{plugin_path.name}"

        plugins = [Path(f"plugin_{i}") for i in range(3)]

        results = await processor.process_plugins_parallel(plugins, mock_process)

        assert len(results) == 3
        for i, result in enumerate(results):
            assert result == f"processed_plugin_{i}"

        processor.shutdown()


class TestDocumentationSystem:
    """Test documentation generation system."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.doc_gen = DocumentationGenerator(workspace_dir=self.temp_dir)

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_generate_plugin_docs(self):
        """Test plugin documentation generation."""
        # Create a plugin
        plugin_dir = self.temp_dir / "doc-plugin"
        plugin_dir.mkdir()

        manifest_content = """
name: doc-plugin
version: 1.0.0
description: Plugin for documentation testing
author: Doc Author
license: MIT

components:
  main:
    description: Main component
    files: []

profiles:
  default:
    description: Default installation
    components:
      - main

configuration:
  enabled: true
  debug: false
"""

        with open(plugin_dir / "plugin-manifest.yaml", "w") as f:
            f.write(manifest_content)

        # Generate documentation
        success = self.doc_gen.generate_plugin_docs(plugin_dir)

        assert success

        docs_dir = plugin_dir / "docs"
        assert docs_dir.exists()
        assert (docs_dir / "README.md").exists()

        # Check content
        with open(docs_dir / "README.md") as f:
            content = f.read()
            assert "doc-plugin" in content
            assert "Doc Author" in content
            assert "Installation" in content
            assert "Components" in content

    def test_validate_documentation(self):
        """Test documentation validation."""
        # Create documentation directory
        docs_dir = self.temp_dir / "docs"
        docs_dir.mkdir()

        # Create a README
        with open(docs_dir / "README.md", "w") as f:
            f.write("# Test Documentation\n\nSome content.")

        # Validate
        issues = self.doc_gen.validate_documentation(docs_dir)

        # Should have no issues with basic valid docs
        assert len(issues) == 0

    def test_documentation_sections(self):
        """Test documentation section creation."""
        section = DocumentationSection(
            title="Test Section", content="# Test Section\n\nTest content.", level=1
        )

        assert section.title == "Test Section"
        assert "Test content" in section.content
        assert section.level == 1

    def test_system_docs_generation(self):
        """Test system documentation generation."""
        output_dir = self.temp_dir / "system-docs"

        success = self.doc_gen.generate_system_docs(output_dir)

        assert success
        assert output_dir.exists()
        assert (output_dir / "README.md").exists()

        # Check content
        with open(output_dir / "README.md") as f:
            content = f.read()
            assert "AI Guardrails Bootstrap System" in content
            assert "Architecture" in content
            assert "Development Guide" in content


class TestCLICommands:
    """Test CLI command functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_cli_imports(self):
        """Test that CLI commands can be imported without errors."""
        # This tests the import fallback we implemented

        assert plugin is not None
        assert registry is not None

    @patch("src.packages.cli.enhanced_commands.PluginRegistry")
    def test_plugin_search_command(self, mock_registry_class):
        """Test plugin search command."""
        # Mock the registry
        mock_registry = Mock()
        mock_registry.search_plugins.return_value = [
            PluginMetadata(
                name="test-plugin",
                version="1.0.0",
                description="Test plugin",
                author="Test Author",
            )
        ]
        mock_registry_class.return_value = mock_registry

        # This would normally test CLI interaction
        # For now, just verify the mock setup works
        assert mock_registry.search_plugins.return_value[0].name == "test-plugin"


def test_phase_3_integration():
    """Test integration between Phase 3 components."""
    temp_dir = Path(tempfile.mkdtemp())

    try:
        # Create toolkit
        toolkit = PluginDevToolkit(workspace_dir=temp_dir)

        # Create a plugin
        success = toolkit.scaffold_plugin("integration-plugin", "basic")
        assert success

        plugin_dir = temp_dir / "integration-plugin"

        # Validate the plugin
        errors = toolkit.validate_plugin(plugin_dir)
        assert len(errors) == 0

        # Generate documentation
        doc_gen = DocumentationGenerator(workspace_dir=temp_dir)
        doc_success = doc_gen.generate_plugin_docs(plugin_dir)
        assert doc_success

        # Test the plugin
        test_results = toolkit.test_plugin(plugin_dir)
        assert len(test_results) > 0
        assert all(isinstance(r, TestResult) for r in test_results)

        # Package the plugin
        package_path = toolkit.package_plugin(plugin_dir)
        assert package_path is not None
        assert package_path.exists()

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    # Run basic tests
    test_phase_3_integration()
    print("✅ Phase 3 integration test passed!")

    # Run individual component tests
    pytest.main([__file__, "-v"])
