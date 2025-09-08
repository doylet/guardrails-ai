"""
Enhanced Documentation System for AI Guardrails Bootstrap

Provides comprehensive documentation generation, management, and maintenance
for plugins, components, and the bootstrap system.

Features:
- Automatic documentation generation
- Multi-format output (Markdown, HTML, PDF)
- API documentation extraction
- Component documentation
- Configuration documentation
- Usage examples generation
- Documentation validation
- Template system
"""

import re
import ast
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import yaml
import logging

from ..domain.plugin_models import PluginManifest


@dataclass
class DocumentationSection:
    """A section of documentation."""

    title: str
    content: str
    level: int = 1
    subsections: List["DocumentationSection"] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentationTemplate:
    """Documentation template definition."""

    name: str
    description: str
    template: str
    variables: List[str] = field(default_factory=list)
    output_format: str = "markdown"


@dataclass
class APIDocumentation:
    """API documentation for a component."""

    name: str
    description: str
    functions: List[Dict[str, Any]] = field(default_factory=list)
    classes: List[Dict[str, Any]] = field(default_factory=list)
    constants: List[Dict[str, Any]] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)


class DocumentationGenerator:
    """Generate comprehensive documentation."""

    def __init__(self, workspace_dir: Path = None):
        self.workspace_dir = workspace_dir or Path.cwd()
        self.logger = logging.getLogger(__name__)
        self.templates = self._load_templates()

    def generate_plugin_docs(
        self, plugin_dir: Path, output_dir: Path = None, formats: List[str] = None
    ) -> bool:
        """
        Generate complete documentation for a plugin.

        Args:
            plugin_dir: Plugin directory path
            output_dir: Documentation output directory
            formats: Output formats (markdown, html, pdf)

        Returns:
            True if documentation generated successfully
        """
        try:
            formats = formats or ["markdown"]
            output_dir = output_dir or plugin_dir / "docs"
            output_dir.mkdir(exist_ok=True)

            # Load plugin manifest
            manifest_path = plugin_dir / "plugin-manifest.yaml"
            if not manifest_path.exists():
                self.logger.error("Plugin manifest not found")
                return False

            with open(manifest_path) as f:
                manifest_data = yaml.safe_load(f)

            manifest = PluginManifest.from_dict(manifest_data)

            # Generate different documentation sections
            sections = []

            # Overview section
            overview = self._generate_overview_section(manifest, plugin_dir)
            sections.append(overview)

            # Installation section
            installation = self._generate_installation_section(manifest)
            sections.append(installation)

            # Components section
            components = self._generate_components_section(manifest, plugin_dir)
            sections.append(components)

            # Configuration section
            configuration = self._generate_configuration_section(manifest)
            sections.append(configuration)

            # API section
            api_docs = self._generate_api_section(plugin_dir)
            if api_docs:
                sections.append(api_docs)

            # Examples section
            examples = self._generate_examples_section(manifest, plugin_dir)
            sections.append(examples)

            # Generate output in requested formats
            for format_type in formats:
                success = self._generate_format(
                    sections, output_dir, format_type, manifest.name
                )
                if not success:
                    self.logger.warning(
                        f"Failed to generate {format_type} documentation"
                    )

            self.logger.info(f"Generated documentation for {manifest.name}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to generate plugin documentation: {e}")
            return False

    def generate_system_docs(self, output_dir: Path, formats: List[str] = None) -> bool:
        """
        Generate system-wide documentation.

        Args:
            output_dir: Documentation output directory
            formats: Output formats

        Returns:
            True if documentation generated successfully
        """
        try:
            formats = formats or ["markdown"]
            output_dir.mkdir(parents=True, exist_ok=True)

            sections = []

            # System overview
            system_overview = self._generate_system_overview()
            sections.append(system_overview)

            # Architecture documentation
            architecture = self._generate_architecture_docs()
            sections.append(architecture)

            # Plugin development guide
            dev_guide = self._generate_development_guide()
            sections.append(dev_guide)

            # API reference
            api_reference = self._generate_system_api_reference()
            sections.append(api_reference)

            # Generate output
            for format_type in formats:
                success = self._generate_format(
                    sections, output_dir, format_type, "AI-Guardrails-Bootstrap"
                )
                if not success:
                    self.logger.warning(
                        f"Failed to generate {format_type} system documentation"
                    )

            return True

        except Exception as e:
            self.logger.error(f"Failed to generate system documentation: {e}")
            return False

    def validate_documentation(self, docs_dir: Path) -> List[str]:
        """
        Validate documentation for completeness and accuracy.

        Args:
            docs_dir: Documentation directory

        Returns:
            List of validation issues
        """
        issues = []

        try:
            # Check for required files
            required_files = ["README.md"]
            for required_file in required_files:
                if not (docs_dir / required_file).exists():
                    issues.append(
                        f"Missing required documentation file: {required_file}"
                    )

            # Check for broken links
            link_issues = self._check_broken_links(docs_dir)
            issues.extend(link_issues)

            # Check for outdated content
            outdated_issues = self._check_outdated_content(docs_dir)
            issues.extend(outdated_issues)

            # Check for formatting issues
            format_issues = self._check_formatting_issues(docs_dir)
            issues.extend(format_issues)

            return issues

        except Exception as e:
            issues.append(f"Documentation validation failed: {e}")
            return issues

    def update_documentation(self, plugin_dir: Path) -> bool:
        """
        Update existing documentation.

        Args:
            plugin_dir: Plugin directory

        Returns:
            True if update successful
        """
        try:
            docs_dir = plugin_dir / "docs"
            if not docs_dir.exists():
                # Generate new documentation
                return self.generate_plugin_docs(plugin_dir)

            # Check if manifest is newer than docs
            manifest_path = plugin_dir / "plugin-manifest.yaml"
            if not manifest_path.exists():
                return False

            manifest_mtime = manifest_path.stat().st_mtime

            # Check main documentation files
            readme_path = docs_dir / "README.md"
            if readme_path.exists():
                readme_mtime = readme_path.stat().st_mtime
                if manifest_mtime > readme_mtime:
                    # Regenerate documentation
                    return self.generate_plugin_docs(plugin_dir)

            return True

        except Exception as e:
            self.logger.error(f"Failed to update documentation: {e}")
            return False

    def _generate_overview_section(
        self, manifest: PluginManifest, plugin_dir: Path
    ) -> DocumentationSection:
        """Generate overview section."""
        content = f"# {manifest.name}\n\n"
        content += f"{manifest.description}\n\n"

        if manifest.author:
            content += f"**Author:** {manifest.author}\n"
        if manifest.version:
            content += f"**Version:** {manifest.version}\n"
        if manifest.license:
            content += f"**License:** {manifest.license}\n"

        content += "\n"

        # Add badges if applicable
        badges = self._generate_badges(manifest)
        if badges:
            content += f"{badges}\n\n"

        return DocumentationSection(title="Overview", content=content, level=1)

    def _generate_installation_section(
        self, manifest: PluginManifest
    ) -> DocumentationSection:
        """Generate installation section."""
        content = "## Installation\n\n"

        # Basic installation
        content += "### Basic Installation\n\n"
        content += f"```bash\nai-guardrails plugin install {manifest.name}\n```\n\n"

        # Profile-based installation
        if manifest.profiles and len(manifest.profiles) > 1:
            content += "### Profile-based Installation\n\n"
            for profile_name, profile in manifest.profiles.items():
                content += f"**{profile_name}**: {profile.description}\n"
                content += f"```bash\nai-guardrails plugin install {manifest.name} --profile {profile_name}\n```\n\n"

        # Requirements
        if manifest.environment and manifest.environment.requires:
            content += "### Requirements\n\n"
            for req in manifest.environment.requires:
                content += f"- {req}\n"
            content += "\n"

        return DocumentationSection(title="Installation", content=content, level=2)

    def _generate_components_section(
        self, manifest: PluginManifest, plugin_dir: Path
    ) -> DocumentationSection:
        """Generate components section."""
        content = "## Components\n\n"

        if not manifest.components:
            content += "No components defined.\n\n"
            return DocumentationSection(title="Components", content=content, level=2)

        for name, component in manifest.components.items():
            content += f"### {name}\n\n"
            content += f"{component.description}\n\n"

            # Dependencies
            if component.dependencies:
                content += f"**Dependencies:** {', '.join(component.dependencies)}\n\n"

            # Files
            if component.files:
                content += "**Files:**\n"
                for file_op in component.files:
                    content += (
                        f"- {file_op.action}: `{file_op.source}` → `{file_op.target}`\n"
                    )
                content += "\n"

            # Hooks
            if component.hooks:
                content += "**Hooks:**\n"
                for hook_name, hook_script in component.hooks.items():
                    content += f"- {hook_name}: `{hook_script}`\n"
                content += "\n"

        return DocumentationSection(title="Components", content=content, level=2)

    def _generate_configuration_section(
        self, manifest: PluginManifest
    ) -> DocumentationSection:
        """Generate configuration section."""
        content = "## Configuration\n\n"

        if manifest.configuration:
            content += "```yaml\n"
            content += yaml.dump(
                {manifest.name: manifest.configuration}, default_flow_style=False
            )
            content += "```\n\n"
        else:
            content += "No configuration options available.\n\n"

        return DocumentationSection(title="Configuration", content=content, level=2)

    def _generate_api_section(self, plugin_dir: Path) -> Optional[DocumentationSection]:
        """Generate API documentation section."""
        try:
            # Look for Python files to document
            python_files = list(plugin_dir.glob("**/*.py"))
            if not python_files:
                return None

            content = "## API Reference\n\n"

            for py_file in python_files:
                if py_file.name.startswith("__"):
                    continue

                api_doc = self._extract_api_documentation(py_file)
                if api_doc:
                    content += f"### {api_doc.name}\n\n"
                    content += f"{api_doc.description}\n\n"

                    # Functions
                    if api_doc.functions:
                        content += "#### Functions\n\n"
                        for func in api_doc.functions:
                            content += f"**{func['name']}**\n\n"
                            content += f"{func['description']}\n\n"
                            if func.get("parameters"):
                                content += "Parameters:\n"
                                for param in func["parameters"]:
                                    content += (
                                        f"- `{param['name']}`: {param['description']}\n"
                                    )
                                content += "\n"

                    # Classes
                    if api_doc.classes:
                        content += "#### Classes\n\n"
                        for cls in api_doc.classes:
                            content += f"**{cls['name']}**\n\n"
                            content += f"{cls['description']}\n\n"

            return DocumentationSection(title="API Reference", content=content, level=2)

        except Exception as e:
            self.logger.warning(f"Failed to generate API documentation: {e}")
            return None

    def _generate_examples_section(
        self, manifest: PluginManifest, plugin_dir: Path
    ) -> DocumentationSection:
        """Generate examples section."""
        content = "## Examples\n\n"

        # Look for example files
        examples_dir = plugin_dir / "examples"
        if examples_dir.exists():
            example_files = list(examples_dir.glob("*"))
            if example_files:
                for example_file in example_files:
                    if example_file.is_file():
                        content += f"### {example_file.stem}\n\n"

                        # Include file content if it's small
                        if example_file.stat().st_size < 10000:  # 10KB limit
                            try:
                                with open(example_file) as f:
                                    example_content = f.read()

                                # Determine language for syntax highlighting
                                lang = self._detect_language(example_file)
                                content += f"```{lang}\n{example_content}\n```\n\n"
                            except Exception:
                                content += (
                                    f"See: `{example_file.relative_to(plugin_dir)}`\n\n"
                                )
                        else:
                            content += (
                                f"See: `{example_file.relative_to(plugin_dir)}`\n\n"
                            )

        # Generate basic usage examples
        if manifest.profiles:
            content += "### Basic Usage\n\n"
            default_profile = manifest.profiles.get("default")
            if default_profile:
                content += f"```bash\n# Install {manifest.name}\nai-guardrails plugin install {manifest.name}\n\n"
                content += f"# Verify installation\nai-guardrails plugin list | grep {manifest.name}\n```\n\n"

        return DocumentationSection(title="Examples", content=content, level=2)

    def _generate_system_overview(self) -> DocumentationSection:
        """Generate system overview documentation."""
        content = "# AI Guardrails Bootstrap System\n\n"
        content += "A comprehensive plugin-based bootstrap system for AI development environments.\n\n"

        content += "## Features\n\n"
        content += "- **Plugin Architecture**: Modular, extensible plugin system\n"
        content += "- **Environment Detection**: Automatic detection and setup of development environments\n"
        content += "- **Configuration Management**: Centralized configuration with validation\n"
        content += "- **Security First**: Built-in security validation and sandboxing\n"
        content += "- **Performance Optimized**: Caching, async operations, and performance monitoring\n\n"

        return DocumentationSection(title="System Overview", content=content, level=1)

    def _generate_architecture_docs(self) -> DocumentationSection:
        """Generate architecture documentation."""
        content = "## Architecture\n\n"

        content += "### Core Components\n\n"
        content += "- **Plugin Manager**: Handles plugin lifecycle\n"
        content += (
            "- **Configuration System**: Manages configuration validation and merging\n"
        )
        content += "- **Security Layer**: Provides validation and sandboxing\n"
        content += (
            "- **Performance Monitor**: Tracks and optimizes system performance\n\n"
        )

        content += "### Plugin Architecture\n\n"
        content += "Plugins are self-contained units that extend the bootstrap system functionality.\n\n"

        return DocumentationSection(title="Architecture", content=content, level=2)

    def _generate_development_guide(self) -> DocumentationSection:
        """Generate development guide."""
        content = "## Development Guide\n\n"

        content += "### Creating a Plugin\n\n"
        content += (
            "```bash\n# Create new plugin\nai-guardrails plugin create my-plugin\n\n"
        )
        content += "# Validate plugin\nai-guardrails plugin validate my-plugin\n\n"
        content += "# Test plugin\nai-guardrails plugin test my-plugin\n```\n\n"

        content += "### Plugin Structure\n\n"
        content += "```\nmy-plugin/\n├── plugin-manifest.yaml\n├── README.md\n├── components/\n│   └── my-component/\n│       └── files/\n├── templates/\n├── hooks/\n└── docs/\n```\n\n"

        return DocumentationSection(title="Development Guide", content=content, level=2)

    def _generate_system_api_reference(self) -> DocumentationSection:
        """Generate system API reference."""
        content = "## API Reference\n\n"

        content += "### Plugin Management\n\n"
        content += "- `ai-guardrails plugin list`: List installed plugins\n"
        content += "- `ai-guardrails plugin install <name>`: Install plugin\n"
        content += "- `ai-guardrails plugin uninstall <name>`: Uninstall plugin\n"
        content += "- `ai-guardrails plugin update <name>`: Update plugin\n\n"

        content += "### Development Tools\n\n"
        content += "- `ai-guardrails plugin create <name>`: Create new plugin\n"
        content += "- `ai-guardrails plugin validate <path>`: Validate plugin\n"
        content += "- `ai-guardrails plugin test <path>`: Test plugin\n"
        content += "- `ai-guardrails plugin package <path>`: Package plugin\n\n"

        return DocumentationSection(title="API Reference", content=content, level=2)

    def _generate_format(
        self,
        sections: List[DocumentationSection],
        output_dir: Path,
        format_type: str,
        title: str,
    ) -> bool:
        """Generate documentation in specified format."""
        try:
            if format_type == "markdown":
                return self._generate_markdown(sections, output_dir, title)
            elif format_type == "html":
                return self._generate_html(sections, output_dir, title)
            elif format_type == "pdf":
                return self._generate_pdf(sections, output_dir, title)
            else:
                self.logger.warning(f"Unsupported format: {format_type}")
                return False

        except Exception as e:
            self.logger.error(f"Failed to generate {format_type} documentation: {e}")
            return False

    def _generate_markdown(
        self, sections: List[DocumentationSection], output_dir: Path, title: str
    ) -> bool:
        """Generate Markdown documentation."""
        try:
            content = ""

            for section in sections:
                content += section.content

                # Add subsections
                for subsection in section.subsections:
                    content += subsection.content

            output_path = output_dir / "README.md"
            with open(output_path, "w") as f:
                f.write(content)

            return True

        except Exception as e:
            self.logger.error(f"Failed to generate Markdown: {e}")
            return False

    def _generate_html(
        self, sections: List[DocumentationSection], output_dir: Path, title: str
    ) -> bool:
        """Generate HTML documentation."""
        try:
            # Simple HTML generation
            html_content = f"<!DOCTYPE html>\n<html>\n<head>\n<title>{title}</title>\n</head>\n<body>\n"

            for section in sections:
                # Convert Markdown to HTML (simplified)
                html_section = self._markdown_to_html(section.content)
                html_content += html_section

            html_content += "\n</body>\n</html>"

            output_path = output_dir / "index.html"
            with open(output_path, "w") as f:
                f.write(html_content)

            return True

        except Exception as e:
            self.logger.error(f"Failed to generate HTML: {e}")
            return False

    def _generate_pdf(
        self, sections: List[DocumentationSection], output_dir: Path, title: str
    ) -> bool:
        """Generate PDF documentation."""
        try:
            # Generate HTML first
            if not self._generate_html(sections, output_dir, title):
                return False

            # Try to convert HTML to PDF using wkhtmltopdf or similar
            html_path = output_dir / "index.html"
            pdf_path = output_dir / f"{title}.pdf"

            # Check if wkhtmltopdf is available
            try:
                subprocess.run(
                    ["wkhtmltopdf", "--version"], capture_output=True, check=True
                )
                subprocess.run(
                    ["wkhtmltopdf", str(html_path), str(pdf_path)],
                    capture_output=True,
                    check=True,
                )
                return True
            except (subprocess.CalledProcessError, FileNotFoundError):
                self.logger.warning("wkhtmltopdf not found, skipping PDF generation")
                return False

        except Exception as e:
            self.logger.error(f"Failed to generate PDF: {e}")
            return False

    def _extract_api_documentation(self, py_file: Path) -> Optional[APIDocumentation]:
        """Extract API documentation from Python file."""
        try:
            with open(py_file) as f:
                content = f.read()

            tree = ast.parse(content)

            api_doc = APIDocumentation(
                name=py_file.stem,
                description=ast.get_docstring(tree) or f"Module: {py_file.stem}",
            )

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_doc = {
                        "name": node.name,
                        "description": ast.get_docstring(node) or "No description",
                        "parameters": [],
                    }

                    # Extract parameters
                    for arg in node.args.args:
                        func_doc["parameters"].append(
                            {"name": arg.arg, "description": f"Parameter: {arg.arg}"}
                        )

                    api_doc.functions.append(func_doc)

                elif isinstance(node, ast.ClassDef):
                    class_doc = {
                        "name": node.name,
                        "description": ast.get_docstring(node) or "No description",
                    }
                    api_doc.classes.append(class_doc)

            return api_doc

        except Exception as e:
            self.logger.warning(f"Failed to extract API docs from {py_file}: {e}")
            return None

    def _load_templates(self) -> Dict[str, DocumentationTemplate]:
        """Load documentation templates."""
        return {
            "plugin_readme": DocumentationTemplate(
                name="plugin_readme",
                description="Plugin README template",
                template="""# {{ plugin_name }}

{{ description }}

## Installation

```bash
ai-guardrails plugin install {{ plugin_name }}
```

## Usage

{{ usage_instructions }}

## Components

{{ components_list }}

## Configuration

{{ configuration_options }}
""",
                variables=[
                    "plugin_name",
                    "description",
                    "usage_instructions",
                    "components_list",
                    "configuration_options",
                ],
            )
        }

    def _generate_badges(self, manifest: PluginManifest) -> str:
        """Generate badges for plugin documentation."""
        badges = []

        if manifest.version:
            badges.append(
                f"![Version](https://img.shields.io/badge/version-{manifest.version}-blue)"
            )

        if manifest.license:
            badges.append(
                f"![License](https://img.shields.io/badge/license-{manifest.license}-green)"
            )

        return " ".join(badges)

    def _detect_language(self, file_path: Path) -> str:
        """Detect programming language from file extension."""
        ext = file_path.suffix.lower()

        lang_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".sh": "bash",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".json": "json",
            ".md": "markdown",
        }

        return lang_map.get(ext, "text")

    def _markdown_to_html(self, markdown: str) -> str:
        """Convert Markdown to HTML (simplified)."""
        html = markdown

        # Headers
        html = re.sub(r"^# (.+)$", r"<h1>\1</h1>", html, flags=re.MULTILINE)
        html = re.sub(r"^## (.+)$", r"<h2>\1</h2>", html, flags=re.MULTILINE)
        html = re.sub(r"^### (.+)$", r"<h3>\1</h3>", html, flags=re.MULTILINE)

        # Code blocks
        html = re.sub(
            r"```(\w+)?\n(.*?)```", r"<pre><code>\2</code></pre>", html, flags=re.DOTALL
        )

        # Inline code
        html = re.sub(r"`([^`]+)`", r"<code>\1</code>", html)

        # Bold
        html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)

        # Paragraphs
        html = re.sub(r"\n\n", "</p><p>", html)
        html = f"<p>{html}</p>"

        return html

    def _check_broken_links(self, docs_dir: Path) -> List[str]:
        """Check for broken links in documentation."""
        issues = []

        for md_file in docs_dir.glob("**/*.md"):
            try:
                with open(md_file) as f:
                    content = f.read()

                # Find markdown links
                links = re.findall(r"\[.*?\]\(([^)]+)\)", content)

                for link in links:
                    if link.startswith("http"):
                        continue  # Skip external links for now

                    # Check relative links
                    link_path = docs_dir / link
                    if not link_path.exists():
                        issues.append(f"Broken link in {md_file.name}: {link}")

            except Exception as e:
                issues.append(f"Failed to check links in {md_file.name}: {e}")

        return issues

    def _check_outdated_content(self, docs_dir: Path) -> List[str]:
        """Check for outdated content."""
        issues = []

        # Check if documentation is older than source files
        try:
            source_dir = docs_dir.parent / "src"
            if source_dir.exists():
                newest_source = max(
                    (f.stat().st_mtime for f in source_dir.rglob("*") if f.is_file()),
                    default=0,
                )

                for doc_file in docs_dir.glob("**/*.md"):
                    if doc_file.stat().st_mtime < newest_source:
                        issues.append(f"Documentation may be outdated: {doc_file.name}")

        except Exception as e:
            issues.append(f"Failed to check for outdated content: {e}")

        return issues

    def _check_formatting_issues(self, docs_dir: Path) -> List[str]:
        """Check for formatting issues."""
        issues = []

        for md_file in docs_dir.glob("**/*.md"):
            try:
                with open(md_file) as f:
                    lines = f.readlines()

                for i, line in enumerate(lines, 1):
                    # Check for long lines
                    if len(line.strip()) > 120:
                        issues.append(
                            f"{md_file.name}:{i}: Line too long ({len(line.strip())} chars)"
                        )

                    # Check for inconsistent heading formats
                    if line.startswith("#"):
                        if (
                            not line.startswith("# ")
                            and not line.startswith("## ")
                            and not line.startswith("### ")
                        ):
                            issues.append(
                                f"{md_file.name}:{i}: Inconsistent heading format"
                            )

            except Exception as e:
                issues.append(f"Failed to check formatting in {md_file.name}: {e}")

        return issues


class DocumentationError(Exception):
    """Exception raised during documentation operations."""

    pass
