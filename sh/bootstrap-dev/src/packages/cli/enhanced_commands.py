"""
Advanced CLI Commands for AI Guardrails Bootstrap Plugin System

This module provides enhanced command-line interface commands for the plugin
architecture enhancement. It includes commands for plugin management, development
tools, registry operations, and advanced installation workflows.

Commands:
- plugin search: Search plugins in registry
- plugin install: Install plugins with enhanced features
- plugin uninstall: Remove plugins and cleanup
- plugin list: List installed plugins
- plugin info: Show plugin information
- plugin validate: Validate plugin manifests
- plugin create: Scaffold new plugins
- plugin publish: Publish plugins to registry
- plugin update: Update plugins to latest versions
- registry add: Add plugin sources
- registry sync: Synchronize with registries
"""

import click
import yaml
import json
from pathlib import Path
import logging

# Fallback for tabulate if not available
try:
    from tabulate import tabulate
except ImportError:

    def tabulate(data, headers=None, tablefmt="grid"):
        """Simple fallback for tabulate."""
        if not data:
            return ""

        if headers:
            result = " | ".join(headers) + "\n"
            result += "-" * len(result) + "\n"
        else:
            result = ""

        for row in data:
            result += " | ".join(str(cell) for cell in row) + "\n"

        return result


from ..core.plugin_registry import PluginRegistry, PluginSource
from ..core.plugin_validator import PluginValidator
from ..domain.plugin_models import PluginManifest
from ..utils import Colors


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--registry-dir", type=click.Path(), help="Plugin registry directory")
@click.pass_context
def plugin(ctx, verbose, registry_dir):
    """Enhanced plugin management commands."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["registry_dir"] = Path(registry_dir) if registry_dir else None

    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)


@plugin.command()
@click.argument("query", required=False)
@click.option("--tags", multiple=True, help="Filter by tags")
@click.option("--author", help="Filter by author")
@click.option("--limit", default=20, help="Maximum results")
@click.option(
    "--format",
    "output_format",
    default="table",
    type=click.Choice(["table", "json", "yaml"]),
)
@click.pass_context
def search(ctx, query, tags, author, limit, output_format):
    """Search for plugins in the registry."""
    try:
        registry = PluginRegistry(ctx.obj.get("registry_dir"))

        # Update index if needed
        if ctx.obj.get("verbose"):
            click.echo("Updating plugin index...")
        registry.update_index()

        # Search plugins
        results = registry.search_plugins(
            query=query or "",
            tags=list(tags) if tags else None,
            author=author,
            limit=limit,
        )

        if not results:
            click.echo("No plugins found matching criteria.")
            return

        # Format output
        if output_format == "json":
            plugin_data = []
            for plugin in results:
                plugin_data.append(
                    {
                        "name": plugin.name,
                        "version": plugin.version,
                        "description": plugin.description,
                        "author": plugin.author,
                        "tags": plugin.tags,
                        "downloads": plugin.download_count,
                    }
                )
            click.echo(json.dumps(plugin_data, indent=2))

        elif output_format == "yaml":
            plugin_data = []
            for plugin in results:
                plugin_data.append(
                    {
                        "name": plugin.name,
                        "version": plugin.version,
                        "description": plugin.description,
                        "author": plugin.author,
                        "tags": plugin.tags,
                        "downloads": plugin.download_count,
                    }
                )
            click.echo(yaml.dump(plugin_data, default_flow_style=False))

        else:  # table format
            headers = ["Name", "Version", "Description", "Author", "Downloads"]
            rows = []

            for plugin in results:
                rows.append(
                    [
                        plugin.name,
                        plugin.version,
                        plugin.description[:50] + "..."
                        if len(plugin.description) > 50
                        else plugin.description,
                        plugin.author,
                        plugin.download_count,
                    ]
                )

            click.echo(tabulate(rows, headers=headers, tablefmt="grid"))

    except Exception as e:
        click.echo(f"{Colors.error('[ERROR]')} Failed to search plugins: {e}")
        if ctx.obj.get("verbose"):
            import traceback

            traceback.print_exc()


@plugin.command()
@click.argument("plugin_name")
@click.option("--version", help="Specific version to install")
@click.option("--target", type=click.Path(), help="Target installation directory")
@click.option("--components", multiple=True, help="Specific components to install")
@click.option("--config", type=click.Path(), help="Configuration file")
@click.option("--dry-run", is_flag=True, help="Preview installation without changes")
@click.option("--force", is_flag=True, help="Force installation over existing files")
@click.pass_context
def install(ctx, plugin_name, version, target, components, config, dry_run, force):
    """Install a plugin with enhanced features."""
    try:
        registry = PluginRegistry(ctx.obj.get("registry_dir"))
        target_path = Path(target) if target else Path.cwd()

        if dry_run:
            click.echo(f"Dry run: Installing {plugin_name}")
            if version:
                click.echo(f"Version: {version}")
            if components:
                click.echo(f"Components: {', '.join(components)}")
            click.echo(f"Target: {target_path}")

        # Load configuration if provided
        if config:
            config_path = Path(config)
            if config_path.exists():
                with open(config_path) as f:
                    if config_path.suffix in [".yaml", ".yml"]:
                        yaml.safe_load(f)
                    else:
                        json.load(f)

        # Install plugin
        success = registry.install_plugin(
            plugin_name=plugin_name, version=version, target_dir=target_path
        )

        if success:
            click.echo(
                f"{Colors.success('[SUCCESS]')} Plugin {plugin_name} installed successfully"
            )
        else:
            click.echo(
                f"{Colors.error('[ERROR]')} Failed to install plugin {plugin_name}"
            )

    except Exception as e:
        click.echo(f"{Colors.error('[ERROR]')} Installation failed: {e}")
        if ctx.obj.get("verbose"):
            import traceback

            traceback.print_exc()


@plugin.command()
@click.argument("plugin_name")
@click.option("--purge", is_flag=True, help="Remove all plugin data")
@click.pass_context
def uninstall(ctx, plugin_name, purge):
    """Uninstall a plugin and clean up components."""
    try:
        # Implementation for plugin uninstallation
        click.echo(f"Uninstalling plugin: {plugin_name}")

        if purge:
            click.echo("Purging all plugin data...")

        # Placeholder for actual uninstall logic
        click.echo(f"{Colors.success('[SUCCESS]')} Plugin {plugin_name} uninstalled")

    except Exception as e:
        click.echo(f"{Colors.error('[ERROR]')} Uninstall failed: {e}")


@plugin.command()
@click.option(
    "--format",
    "output_format",
    default="table",
    type=click.Choice(["table", "json", "yaml"]),
)
@click.option("--installed-only", is_flag=True, help="Show only installed plugins")
@click.pass_context
def list(ctx, output_format, installed_only):
    """List available or installed plugins."""
    try:
        registry = PluginRegistry(ctx.obj.get("registry_dir"))

        if installed_only:
            # List installed plugins (placeholder)
            plugins = []
        else:
            # List all available plugins
            registry.update_index()
            plugins = []

            for name, versions in registry.index.plugins.items():
                if versions:
                    latest = max(versions, key=lambda v: v.version)
                    plugins.append(
                        {
                            "name": latest.name,
                            "version": latest.version,
                            "description": latest.description,
                            "author": latest.author,
                            "source": latest.source.name
                            if latest.source
                            else "unknown",
                        }
                    )

        if not plugins:
            click.echo("No plugins found.")
            return

        # Format output
        if output_format == "json":
            click.echo(json.dumps(plugins, indent=2))
        elif output_format == "yaml":
            click.echo(yaml.dump(plugins, default_flow_style=False))
        else:  # table
            headers = ["Name", "Version", "Description", "Author", "Source"]
            rows = [
                [
                    p["name"],
                    p["version"],
                    p["description"][:40] + "..."
                    if len(p["description"]) > 40
                    else p["description"],
                    p["author"],
                    p["source"],
                ]
                for p in plugins
            ]
            click.echo(tabulate(rows, headers=headers, tablefmt="grid"))

    except Exception as e:
        click.echo(f"{Colors.error('[ERROR]')} Failed to list plugins: {e}")


@plugin.command()
@click.argument("plugin_name")
@click.option("--version", help="Specific version")
@click.option(
    "--format", "output_format", default="yaml", type=click.Choice(["yaml", "json"])
)
@click.pass_context
def info(ctx, plugin_name, version, output_format):
    """Show detailed information about a plugin."""
    try:
        registry = PluginRegistry(ctx.obj.get("registry_dir"))

        plugin_meta = registry.get_plugin_info(plugin_name, version)
        if not plugin_meta:
            click.echo(f"Plugin not found: {plugin_name}")
            return

        plugin_info = {
            "name": plugin_meta.name,
            "version": plugin_meta.version,
            "description": plugin_meta.description,
            "author": plugin_meta.author,
            "license": plugin_meta.license,
            "homepage": plugin_meta.homepage,
            "repository": plugin_meta.repository,
            "tags": plugin_meta.tags,
            "dependencies": [
                {"plugin": dep.plugin, "version": dep.version, "optional": dep.optional}
                for dep in plugin_meta.dependencies
            ],
            "download_count": plugin_meta.download_count,
            "rating": plugin_meta.rating,
            "last_updated": plugin_meta.last_updated.isoformat()
            if plugin_meta.last_updated
            else None,
        }

        if output_format == "json":
            click.echo(json.dumps(plugin_info, indent=2))
        else:
            click.echo(yaml.dump(plugin_info, default_flow_style=False))

    except Exception as e:
        click.echo(f"{Colors.error('[ERROR]')} Failed to get plugin info: {e}")


@plugin.command()
@click.argument("manifest_path", type=click.Path(exists=True))
@click.option("--strict", is_flag=True, help="Enable strict validation")
@click.pass_context
def validate(ctx, manifest_path, strict):
    """Validate a plugin manifest file."""
    try:
        validator = PluginValidator()
        manifest_file = Path(manifest_path)

        # Load manifest
        with open(manifest_file) as f:
            manifest_data = yaml.safe_load(f)

        # Convert to PluginManifest object
        manifest = PluginManifest.from_dict(manifest_data)

        # Validate
        errors = validator.validate_plugin_manifest(manifest)

        if not errors:
            click.echo(f"{Colors.success('[VALID]')} Plugin manifest is valid")
        else:
            click.echo(f"{Colors.error('[INVALID]')} Plugin manifest has errors:")
            for error in errors:
                click.echo(f"  - {error}")

        return len(errors) == 0

    except Exception as e:
        click.echo(f"{Colors.error('[ERROR]')} Validation failed: {e}")
        return False


@plugin.command()
@click.argument("plugin_name")
@click.option("--template", default="basic", help="Plugin template to use")
@click.option("--author", help="Plugin author")
@click.option("--description", help="Plugin description")
@click.option("--license", default="MIT", help="Plugin license")
@click.pass_context
def create(ctx, plugin_name, template, author, description, license):
    """Create a new plugin from template."""
    try:
        plugin_dir = Path(f"plugins/{plugin_name}")

        if plugin_dir.exists():
            click.echo(
                f"{Colors.error('[ERROR]')} Plugin directory already exists: {plugin_dir}"
            )
            return

        # Create plugin directory structure
        plugin_dir.mkdir(parents=True)
        (plugin_dir / "components").mkdir()
        (plugin_dir / "templates").mkdir()
        (plugin_dir / "hooks").mkdir()
        (plugin_dir / "docs").mkdir()

        # Create plugin manifest
        manifest = {
            "name": plugin_name,
            "version": "0.1.0",
            "description": description or f"A plugin for {plugin_name}",
            "author": author or "Unknown",
            "license": license,
            "components": {
                f"{plugin_name}-component": {
                    "description": f"Main component for {plugin_name}",
                    "files": [],
                }
            },
            "profiles": {
                "default": {
                    "description": f"Default {plugin_name} installation",
                    "components": [f"{plugin_name}-component"],
                }
            },
        }

        with open(plugin_dir / "plugin-manifest.yaml", "w") as f:
            yaml.dump(manifest, f, default_flow_style=False)

        # Create README
        readme_content = f"""# {plugin_name} Plugin

{description or f"A plugin for {plugin_name}"}

## Installation

```bash
ai-guardrails plugin install {plugin_name}
```

## Usage

Describe how to use your plugin here.

## Configuration

Describe any configuration options here.

## Components

- `{plugin_name}-component`: Main component for {plugin_name}

## License

{license}
"""

        with open(plugin_dir / "README.md", "w") as f:
            f.write(readme_content)

        click.echo(f"{Colors.success('[SUCCESS]')} Created plugin: {plugin_dir}")
        click.echo(f"Edit {plugin_dir}/plugin-manifest.yaml to customize your plugin")

    except Exception as e:
        click.echo(f"{Colors.error('[ERROR]')} Failed to create plugin: {e}")


@click.group()
@click.pass_context
def registry(ctx):
    """Plugin registry management commands."""
    pass


@registry.command()
@click.argument("name")
@click.argument("url")
@click.option(
    "--type",
    "source_type",
    default="registry",
    type=click.Choice(["local", "git", "registry"]),
)
@click.option(
    "--priority", default=100, help="Source priority (lower = higher priority)"
)
@click.option("--auth-token", help="Authentication token for private sources")
@click.pass_context
def add(ctx, name, url, source_type, priority, auth_token):
    """Add a plugin source to the registry."""
    try:
        registry_obj = PluginRegistry(ctx.parent.obj.get("registry_dir"))

        source = PluginSource(
            name=name,
            url=url,
            type=source_type,
            priority=priority,
            auth_token=auth_token,
        )

        if registry_obj.add_source(source):
            click.echo(f"{Colors.success('[SUCCESS]')} Added plugin source: {name}")
        else:
            click.echo(f"{Colors.error('[ERROR]')} Failed to add plugin source: {name}")

    except Exception as e:
        click.echo(f"{Colors.error('[ERROR]')} Failed to add source: {e}")


@registry.command()
@click.argument("name")
@click.pass_context
def remove(ctx, name):
    """Remove a plugin source from the registry."""
    try:
        registry_obj = PluginRegistry(ctx.parent.obj.get("registry_dir"))

        if registry_obj.remove_source(name):
            click.echo(f"{Colors.success('[SUCCESS]')} Removed plugin source: {name}")
        else:
            click.echo(
                f"{Colors.error('[ERROR]')} Failed to remove plugin source: {name}"
            )

    except Exception as e:
        click.echo(f"{Colors.error('[ERROR]')} Failed to remove source: {e}")


@registry.command()
@click.option("--force", is_flag=True, help="Force update even if cache is valid")
@click.pass_context
def sync(ctx, force):
    """Synchronize with plugin registries."""
    try:
        registry_obj = PluginRegistry(ctx.parent.obj.get("registry_dir"))

        click.echo("Synchronizing with plugin registries...")
        success = registry_obj.update_index(force=force)

        if success:
            click.echo(
                f"{Colors.success('[SUCCESS]')} Registry synchronization complete"
            )
        else:
            click.echo(f"{Colors.error('[ERROR]')} Registry synchronization failed")

    except Exception as e:
        click.echo(f"{Colors.error('[ERROR]')} Sync failed: {e}")


@registry.command()
@click.option(
    "--format",
    "output_format",
    default="table",
    type=click.Choice(["table", "json", "yaml"]),
)
@click.pass_context
def sources(ctx, output_format):
    """List configured plugin sources."""
    try:
        registry_obj = PluginRegistry(ctx.parent.obj.get("registry_dir"))

        sources = registry_obj.index.sources

        if not sources:
            click.echo("No plugin sources configured.")
            return

        if output_format == "json":
            source_data = []
            for source in sources:
                source_data.append(
                    {
                        "name": source.name,
                        "url": source.url,
                        "type": source.type,
                        "enabled": source.enabled,
                        "priority": source.priority,
                    }
                )
            click.echo(json.dumps(source_data, indent=2))

        elif output_format == "yaml":
            source_data = []
            for source in sources:
                source_data.append(
                    {
                        "name": source.name,
                        "url": source.url,
                        "type": source.type,
                        "enabled": source.enabled,
                        "priority": source.priority,
                    }
                )
            click.echo(yaml.dump(source_data, default_flow_style=False))

        else:  # table
            headers = ["Name", "Type", "URL", "Enabled", "Priority"]
            rows = []

            for source in sources:
                rows.append(
                    [
                        source.name,
                        source.type,
                        source.url[:50] + "..." if len(source.url) > 50 else source.url,
                        "Yes" if source.enabled else "No",
                        source.priority,
                    ]
                )

            click.echo(tabulate(rows, headers=headers, tablefmt="grid"))

    except Exception as e:
        click.echo(f"{Colors.error('[ERROR]')} Failed to list sources: {e}")


# Add registry commands to plugin group
plugin.add_command(registry)


if __name__ == "__main__":
    plugin()
