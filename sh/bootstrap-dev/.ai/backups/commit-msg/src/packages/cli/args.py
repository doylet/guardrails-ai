"""Command-line argument parsing for the AI Guardrails Bootstrap System.

This module defines the CLI interface and parses user arguments into
structured configuration objects for use by the orchestrator.
"""

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from ..domain.constants import DEFAULT_PROFILE


@dataclass
class BootstrapArgs:
    """Parsed command-line arguments."""

    # Commands
    command: str  # plan, install, doctor, list, uninstall

    # Target and source configuration
    target_dir: Path
    manifest_path: Optional[Path] = None
    profile: str = DEFAULT_PROFILE
    components: List[str] = None

    # Operation modes
    dry_run: bool = False
    force: bool = False
    repair: bool = False

    # List command flags (renamed to avoid conflicts)
    list_profiles: bool = False
    list_components: bool = False
    list_installed: bool = False

    # Output configuration
    verbose: bool = False
    quiet: bool = False
    structured_logs: bool = False
    log_file: Optional[Path] = None

    # Formatting options
    output_format: str = "text"  # text, json, yaml
    no_color: bool = False

    def __post_init__(self):
        """Validate and normalize arguments."""
        if self.components is None:
            self.components = []

        # Convert string paths to Path objects
        if isinstance(self.target_dir, str):
            self.target_dir = Path(self.target_dir)
        if isinstance(self.manifest_path, str):
            self.manifest_path = Path(self.manifest_path)
        if isinstance(self.log_file, str):
            self.log_file = Path(self.log_file)


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser."""

    parser = argparse.ArgumentParser(
        prog="ai-guardrails",
        description="AI Guardrails Bootstrap System - Install and manage AI guardrails for development projects",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Preview installation plan
  ai-guardrails plan --profile full

  # Install with dry run preview
  ai-guardrails install --profile standard --dry-run

  # Install with verbose output
  ai-guardrails install --verbose

  # Validate current installation
  ai-guardrails doctor

  # Repair detected issues
  ai-guardrails doctor --repair

  # List available components
  ai-guardrails list --components

  # Uninstall specific components
  ai-guardrails uninstall --components hooks,workflows
        """,
    )

    # Global options
    parser.add_argument(
        "--target-dir",
        type=Path,
        default=Path.cwd(),
        help="Target directory for installation (default: current directory)",
    )

    parser.add_argument(
        "--manifest",
        dest="manifest_path",
        type=Path,
        help="Path to installation manifest (default: auto-detect)",
    )

    parser.add_argument(
        "--profile",
        default=DEFAULT_PROFILE,
        help=f"Installation profile to use (default: {DEFAULT_PROFILE})",
    )

    parser.add_argument(
        "--components",
        nargs="*",
        help="Specific components to operate on (default: all in profile)",
    )

    # Operation modes
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Force operation even if files are up-to-date",
    )

    # Output configuration
    output_group = parser.add_argument_group("output options")

    output_group.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    output_group.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress output except errors",
    )

    output_group.add_argument(
        "--structured-logs",
        action="store_true",
        help="Output structured JSON logs (for CI integration)",
    )

    output_group.add_argument(
        "--log-file",
        type=Path,
        help="Write detailed logs to file",
    )

    output_group.add_argument(
        "--output-format",
        choices=["text", "json", "yaml"],
        default="text",
        help="Output format for structured data (default: text)",
    )

    output_group.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output",
    )

    # Subcommands
    subparsers = parser.add_subparsers(
        dest="command",
        title="commands",
        description="Available commands",
        help="Command to execute",
        required=True,
    )

    # Plan command
    subparsers.add_parser(
        "plan",
        help="Show installation plan without making changes",
        description="Generate and display the installation plan showing what files would be installed, modified, or skipped.",
    )

    # Install command
    subparsers.add_parser(
        "install",
        help="Install AI guardrails components",
        description="Install the specified profile and components to the target directory.",
    )    # Doctor command
    doctor_parser = subparsers.add_parser(
        "doctor",
        help="Validate and repair installation",
        description="Validate the current installation and optionally repair detected issues.",
    )

    doctor_parser.add_argument(
        "--repair",
        action="store_true",
        help="Automatically repair detected issues",
    )

    # List command
    list_parser = subparsers.add_parser(
        "list",
        help="List available profiles and components",
        description="Display available installation profiles, components, and their descriptions.",
    )

    list_group = list_parser.add_mutually_exclusive_group()
    list_group.add_argument(
        "--profiles",
        action="store_true",
        help="List available profiles",
    )
    list_group.add_argument(
        "--components",
        action="store_true",
        help="List available components",
    )
    list_group.add_argument(
        "--installed",
        action="store_true",
        help="List currently installed components",
    )

    # Uninstall command
    uninstall_parser = subparsers.add_parser(
        "uninstall",
        help="Remove installed components",
        description="Remove the specified components from the target directory.",
    )

    uninstall_parser.add_argument(
        "--components",
        nargs="+",
        required=True,
        help="Components to uninstall",
    )

    return parser


def parse_args(args: Optional[List[str]] = None) -> BootstrapArgs:
    """Parse command-line arguments.

    Args:
        args: List of arguments to parse (default: sys.argv)

    Returns:
        Parsed arguments as BootstrapArgs object
    """
    parser = create_parser()

    if args is None:
        args = sys.argv[1:]

    parsed = parser.parse_args(args)

    # Convert Namespace to BootstrapArgs
    # Handle the conflict between global --components and list --components
    if parsed.command == "list":
        # For list command, use the boolean flags from the list subcommand
        list_components_flag = getattr(parsed, "components", False)
        global_components = []  # List command doesn't use global components
    else:
        # For other commands, use the global components list
        list_components_flag = False
        global_components = getattr(parsed, "components", None) or []
    
    return BootstrapArgs(
        command=parsed.command,
        target_dir=parsed.target_dir,
        manifest_path=getattr(parsed, "manifest_path", None),
        profile=parsed.profile,
        components=global_components,
        dry_run=parsed.dry_run,
        force=parsed.force,
        repair=getattr(parsed, "repair", False),
        list_profiles=getattr(parsed, "profiles", False),
        list_components=list_components_flag,
        list_installed=getattr(parsed, "installed", False),
        verbose=parsed.verbose,
        quiet=parsed.quiet,
        structured_logs=parsed.structured_logs,
        log_file=parsed.log_file,
        output_format=parsed.output_format,
        no_color=parsed.no_color,
    )


def validate_args(args: BootstrapArgs) -> None:
    """Validate parsed arguments for consistency.

    Args:
        args: Parsed arguments to validate

    Raises:
        SystemExit: If validation fails
    """
    # Check mutually exclusive options
    if args.verbose and args.quiet:
        print("Error: --verbose and --quiet cannot be used together", file=sys.stderr)
        sys.exit(1)

    # Validate target directory for install/doctor commands
    if args.command in ("install", "doctor") and not args.target_dir.exists():
        if args.command == "install":
            # Create target directory for install
            try:
                args.target_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                print(f"Error: Cannot create target directory {args.target_dir}: {e}", file=sys.stderr)
                sys.exit(1)
        else:
            print(f"Error: Target directory does not exist: {args.target_dir}", file=sys.stderr)
            sys.exit(1)

    # Validate manifest path if provided
    if args.manifest_path and not args.manifest_path.exists():
        print(f"Error: Manifest file not found: {args.manifest_path}", file=sys.stderr)
        sys.exit(1)

    # Validate log file directory
    if args.log_file:
        try:
            args.log_file.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"Error: Cannot create log directory {args.log_file.parent}: {e}", file=sys.stderr)
            sys.exit(1)
