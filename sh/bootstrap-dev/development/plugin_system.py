#!/usr/bin/env python3
"""
Plugin System for AI Guardrails Bootstrap
Allows extending functionality with custom plugins
"""

import importlib.util
from pathlib import Path
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod

class BootstrapPlugin(ABC):
    """Base class for bootstrap plugins"""

    @abstractmethod
    def get_name(self) -> str:
        """Return plugin name"""
        pass

    @abstractmethod
    def get_version(self) -> str:
        """Return plugin version"""
        pass

    @abstractmethod
    def get_description(self) -> str:
        """Return plugin description"""
        pass

    def get_dependencies(self) -> List[str]:
        """Return list of required components"""
        return []

    def pre_install(self, context: Dict[str, Any]) -> bool:
        """Called before component installation"""
        return True

    def post_install(self, context: Dict[str, Any]) -> bool:
        """Called after component installation"""
        return True

    def get_custom_components(self) -> Dict[str, Any]:
        """Return custom components to add to configuration"""
        return {}

    def validate_environment(self, env: Dict[str, bool]) -> List[str]:
        """Validate environment and return list of issues"""
        return []

class PluginManager:
    """Manages bootstrap plugins"""

    def __init__(self, plugin_dir: Path):
        self.plugin_dir = plugin_dir
        self.plugins: Dict[str, BootstrapPlugin] = {}
        self.load_plugins()

    def load_plugins(self):
        """Load all plugins from plugin directory"""
        if not self.plugin_dir.exists():
            return

        for plugin_file in self.plugin_dir.glob("*.py"):
            if plugin_file.name.startswith("_"):
                continue

            try:
                self.load_plugin(plugin_file)
            except Exception as e:
                print(f"Warning: Failed to load plugin {plugin_file}: {e}")

    def load_plugin(self, plugin_file: Path):
        """Load a single plugin file"""
        spec = importlib.util.spec_from_file_location(
            plugin_file.stem, plugin_file
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Look for BootstrapPlugin subclasses
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (isinstance(attr, type) and
                issubclass(attr, BootstrapPlugin) and
                attr != BootstrapPlugin):

                plugin_instance = attr()
                self.plugins[plugin_instance.get_name()] = plugin_instance
                print(f"Loaded plugin: {plugin_instance.get_name()}")

    def get_plugin(self, name: str) -> Optional[BootstrapPlugin]:
        """Get plugin by name"""
        return self.plugins.get(name)

    def list_plugins(self) -> List[BootstrapPlugin]:
        """List all loaded plugins"""
        return list(self.plugins.values())

    def extend_configuration(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Extend configuration with plugin components"""
        extended_config = config.copy()

        for plugin in self.plugins.values():
            custom_components = plugin.get_custom_components()
            if custom_components:
                extended_config.setdefault('components', {}).update(custom_components)

        return extended_config

    def run_pre_install_hooks(self, context: Dict[str, Any]) -> bool:
        """Run pre-install hooks for all plugins"""
        for plugin in self.plugins.values():
            if not plugin.pre_install(context):
                print(f"Plugin {plugin.get_name()} pre-install failed")
                return False
        return True

    def run_post_install_hooks(self, context: Dict[str, Any]) -> bool:
        """Run post-install hooks for all plugins"""
        for plugin in self.plugins.values():
            if not plugin.post_install(context):
                print(f"Plugin {plugin.get_name()} post-install failed")
                return False
        return True

# Example plugin implementations
class DockerPlugin(BootstrapPlugin):
    """Plugin for Docker integration"""

    def get_name(self) -> str:
        return "docker"

    def get_version(self) -> str:
        return "1.0.0"

    def get_description(self) -> str:
        return "Docker integration for AI Guardrails"

    def get_custom_components(self) -> Dict[str, Any]:
        return {
            "docker": {
                "name": "Docker Integration",
                "optional": True,
                "files": [
                    {
                        "source": "docker/Dockerfile.ai-guardrails",
                        "target": "Dockerfile.ai-guardrails"
                    },
                    {
                        "source": "docker/docker-compose.ai.yml",
                        "target": "docker-compose.ai.yml"
                    }
                ],
                "post_install": [
                    "echo 'Docker files installed. Run: docker-compose -f docker-compose.ai.yml up'"
                ]
            }
        }

    def validate_environment(self, env: Dict[str, bool]) -> List[str]:
        issues = []
        if not env.get('has_docker', False):
            issues.append("Docker not found. Install Docker to use Docker integration.")
        return issues

class KubernetesPlugin(BootstrapPlugin):
    """Plugin for Kubernetes integration"""

    def get_name(self) -> str:
        return "kubernetes"

    def get_version(self) -> str:
        return "1.0.0"

    def get_description(self) -> str:
        return "Kubernetes deployment for AI Guardrails"

    def get_dependencies(self) -> List[str]:
        return ["docker"]  # Depends on docker plugin

    def get_custom_components(self) -> Dict[str, Any]:
        return {
            "kubernetes": {
                "name": "Kubernetes Deployment",
                "optional": True,
                "depends_on": ["docker"],
                "files": [
                    {
                        "source": "k8s/ai-guardrails-deployment.yaml",
                        "target": "k8s/ai-guardrails-deployment.yaml"
                    },
                    {
                        "source": "k8s/ai-guardrails-service.yaml",
                        "target": "k8s/ai-guardrails-service.yaml"
                    }
                ]
            }
        }

# Integration with main bootstrap manager
def create_enhanced_manager_with_plugins(config_path: str, template_repo: str, plugin_dir: str):
    """Create bootstrap manager with plugin support"""
    from bootstrap_manager import BootstrapManager

    # Load plugins
    plugin_manager = PluginManager(Path(plugin_dir))

    # Extend BootstrapManager
    class EnhancedBootstrapManager(BootstrapManager):
        def __init__(self, config_path: str, template_repo: str):
            super().__init__(config_path, template_repo)
            self.plugin_manager = plugin_manager

            # Extend configuration with plugins
            self.config = self.plugin_manager.extend_configuration(self.config)

        def install_component(self, comp_name: str, env: Dict[str, bool], force: bool = False) -> bool:
            # Run pre-install hooks
            context = {
                'component': comp_name,
                'environment': env,
                'target_dir': self.target_dir,
                'force': force
            }

            if not self.plugin_manager.run_pre_install_hooks(context):
                return False

            # Install component
            success = super().install_component(comp_name, env, force)

            # Run post-install hooks
            if success:
                success = self.plugin_manager.run_post_install_hooks(context)

            return success

        def list_plugins(self):
            """List available plugins"""
            print("Available plugins:")
            for plugin in self.plugin_manager.list_plugins():
                print(f"  {plugin.get_name()}: {plugin.get_description()} (v{plugin.get_version()})")

    return EnhancedBootstrapManager(config_path, template_repo)

if __name__ == "__main__":
    # Example usage
    plugin_dir = Path("plugins")
    manager = create_enhanced_manager_with_plugins(
        "bootstrap-config.yaml",
        ".",
        str(plugin_dir)
    )

    # List plugins
    manager.list_plugins()
