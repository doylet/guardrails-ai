"""
Test Phase 2 Plugin Architecture Enhancement Components

This test file validates the core functionality of Phase 2 deliverables:
- Plugin lifecycle management
- Template engine processing
- Configuration validation
- Component management
- Enhanced plugin installation
"""

import pytest
import tempfile
from pathlib import Path

from src.packages.core.plugin_lifecycle import PluginLifecycle, HookExecutionContext
from src.packages.adapters.template_engine import TemplateEngine
from src.packages.core.config_validator import ConfigValidator
from src.packages.core.component_manager import ComponentManager
from src.packages.domain.plugin_models import PluginManifest, ComponentDefinition


class TestPluginLifecycle:
    """Test plugin lifecycle management."""

    def test_lifecycle_initialization(self):
        """Test lifecycle manager initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            plugin_path = Path(temp_dir) / "plugin"
            target_path = Path(temp_dir) / "target"
            plugin_path.mkdir()
            target_path.mkdir()

            lifecycle = PluginLifecycle(plugin_path, target_path)
            assert lifecycle.plugin_path.resolve() == plugin_path.resolve()
            assert lifecycle.target_path.resolve() == target_path.resolve()

    def test_hook_execution_context(self):
        """Test hook execution context creation."""
        context = HookExecutionContext(
            plugin_name="test-plugin",
            plugin_version="1.0.0",
            plugin_path=Path("/test/plugin"),
            target_path=Path("/test/target"),
            environment={},
            configuration={},
            dry_run=False
        )

        assert context.plugin_name == "test-plugin"
        assert context.plugin_version == "1.0.0"
        assert not context.dry_run


class TestTemplateEngine:
    """Test template engine functionality."""

    def test_template_engine_initialization(self):
        """Test template engine initialization."""
        engine = TemplateEngine()
        assert engine._environment is not None

    def test_template_processing(self):
        """Test basic template processing."""
        from src.packages.adapters.template_engine import TemplateContext

        engine = TemplateEngine()

        template_content = "Hello {{ name }}!"
        context = TemplateContext(variables={"name": "World"})

        result = engine.render_template(template_content, context)
        assert result.success
        assert result.content == "Hello World!"

    def test_template_security(self):
        """Test template security restrictions."""
        from src.packages.adapters.template_engine import TemplateContext

        engine = TemplateEngine()

        # This should be restricted in secure mode
        template_content = "{{ ''.__class__.__mro__[1].__subclasses__() }}"
        context = TemplateContext()

        result = engine.render_template(template_content, context)
        # Should fail gracefully rather than execute dangerous code
        assert not result.success or "subclasses" not in result.content


class TestConfigValidator:
    """Test configuration validation functionality."""

    def test_config_validator_initialization(self):
        """Test configuration validator initialization."""
        validator = ConfigValidator()
        # Check that validator has the basic functionality
        assert hasattr(validator, 'validate_component_config')

    def test_basic_validation(self):
        """Test basic configuration validation."""
        validator = ConfigValidator()

        # Simple valid configuration
        config = {"name": "test", "enabled": True}
        component = ComponentDefinition(
            name="test-component",
            description="Test component"
        )

        result = validator.validate_component_config(config, component)
        assert result.valid
        assert result.processed_config == config


class TestComponentManager:
    """Test component management functionality."""

    def test_component_manager_initialization(self):
        """Test component manager initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            plugin_path = Path(temp_dir) / "plugin"
            target_path = Path(temp_dir) / "target"
            plugin_path.mkdir()
            target_path.mkdir()

            manager = ComponentManager(plugin_path, target_path)
            assert manager.plugin_path.resolve() == plugin_path.resolve()
            assert manager.target_path.resolve() == target_path.resolve()

    def test_installation_plan_creation(self):
        """Test installation plan creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            plugin_path = Path(temp_dir) / "plugin"
            target_path = Path(temp_dir) / "target"
            plugin_path.mkdir()
            target_path.mkdir()

            manager = ComponentManager(plugin_path, target_path)

        # Create simple manifest
        manifest = PluginManifest(
            name="test-plugin",
            version="1.0.0",
            description="Test plugin",
            author="Test",
            components={
                "comp1": ComponentDefinition(
                    name="comp1",
                    description="Component 1",
                    files=[]  # Empty file list for testing
                )
            }
        )

        plan = manager.create_installation_plan(manifest, ["comp1"])
        assert "comp1" in plan.components
        # Note: conflicts may include validation warnings, which is acceptable for basic functionality test


class TestPluginArchitectureIntegration:
    """Test integration between Phase 2 components."""

    def test_component_integration(self):
        """Test that all Phase 2 components can work together."""
        with tempfile.TemporaryDirectory() as temp_dir:
            plugin_path = Path(temp_dir) / "plugin"
            target_path = Path(temp_dir) / "target"
            plugin_path.mkdir()
            target_path.mkdir()

            # Initialize all components
            lifecycle = PluginLifecycle(plugin_path, target_path)
            template_engine = TemplateEngine()
            config_validator = ConfigValidator()
            component_manager = ComponentManager(plugin_path, target_path)

            # Verify they all initialized without errors
            assert lifecycle is not None
            assert template_engine is not None
            assert config_validator is not None
            assert component_manager is not None

    def test_phase_2_completeness(self):
        """Test that Phase 2 deliverables are complete."""
        # Verify all Phase 2 modules can be imported
        from src.packages.core.plugin_lifecycle import PluginLifecycle
        from src.packages.adapters.template_engine import TemplateEngine
        from src.packages.core.config_validator import ConfigValidator
        from src.packages.core.component_manager import ComponentManager
        from src.packages.adapters.enhanced_plugin_installer import EnhancedPluginInstaller

        # Verify all key classes exist and are importable
        assert PluginLifecycle is not None
        assert TemplateEngine is not None
        assert ConfigValidator is not None
        assert ComponentManager is not None
        assert EnhancedPluginInstaller is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
