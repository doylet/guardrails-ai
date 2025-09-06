"""Main entry point for the AI Guardrails Bootstrap System CLI.

This module provides the main() function that coordinates argument parsing,
logging configuration, and command execution through the orchestrator.
"""

import sys

from .args import parse_args, validate_args
from ..adapters.logging import configure_logging, get_logger
from ..core.orchestrator import Orchestrator
from ..domain.errors import BootstrapError


def main() -> int:
    """Main entry point for the CLI.

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        # Parse and validate arguments
        args = parse_args()
        validate_args(args)

        # Configure logging
        log_level = "DEBUG" if args.verbose else "INFO"
        configure_logging(
            level=log_level,
            structured=args.structured_logs,
            log_file=args.log_file,
            quiet=args.quiet,
        )

        logger = get_logger(__name__)
        logger.debug(f"Starting {args.command} command with args: {args}")

        # Create and run orchestrator
        orchestrator = Orchestrator(
            target_dir=args.target_dir,
            manifest_path=args.manifest_path,
        )

        # Execute command
        result = execute_command(orchestrator, args)

        if result:
            logger.info(f"Command {args.command} completed successfully")
            return 0
        else:
            logger.error(f"Command {args.command} failed")
            return 1

    except BootstrapError as e:
        logger = get_logger(__name__)
        logger.error(f"Bootstrap error: {e}")

        # Print structured error info if verbose
        if hasattr(args, "verbose") and args.verbose and e.details:
            logger.debug(f"Error details: {e.details}")

        return 1

    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        return 130  # Standard exit code for SIGINT

    except Exception as e:
        logger = get_logger(__name__)
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


def execute_command(orchestrator: "Orchestrator", args) -> bool:
    """Execute the specified command using the orchestrator.

    Args:
        orchestrator: Orchestrator instance
        args: Parsed command arguments

    Returns:
        True if command succeeded, False otherwise
    """
    logger = get_logger(__name__)

    try:
        if args.command == "plan":
            return execute_plan(orchestrator, args)
        elif args.command == "install":
            return execute_install(orchestrator, args)
        elif args.command == "doctor":
            return execute_doctor(orchestrator, args)
        elif args.command == "list":
            return execute_list(orchestrator, args)
        elif args.command == "uninstall":
            return execute_uninstall(orchestrator, args)
        else:
            logger.error(f"Unknown command: {args.command}")
            return False

    except BootstrapError:
        # Re-raise bootstrap errors to be handled at top level
        raise
    except Exception as e:
        logger.error(f"Error executing {args.command}: {e}", exc_info=True)
        return False


def execute_plan(orchestrator: "Orchestrator", args) -> bool:
    """Execute the plan command.

    Args:
        orchestrator: Orchestrator instance
        args: Parsed command arguments

    Returns:
        True if successful, False otherwise
    """
    logger = get_logger(__name__)
    logger.info("Generating installation plan...")

    plan = orchestrator.create_plan(
        profile=args.profile,
        components=args.components,
        force=args.force,
    )

    # Display plan based on output format
    if args.output_format == "json":
        import json
        print(json.dumps(plan.to_dict(), indent=2))
    elif args.output_format == "yaml":
        import yaml
        print(yaml.dump(plan.to_dict(), default_flow_style=False))
    else:
        # Text format
        display_plan_text(plan, args)

    return True


def execute_install(orchestrator: "Orchestrator", args) -> bool:
    """Execute the install command.

    Args:
        orchestrator: Orchestrator instance
        args: Parsed command arguments

    Returns:
        True if successful, False otherwise
    """
    logger = get_logger(__name__)

    if args.dry_run:
        logger.info("Performing dry run installation...")
        return execute_plan(orchestrator, args)
    else:
        logger.info("Installing AI guardrails...")

        result = orchestrator.install(
            profile=args.profile,
            components=args.components,
            force=args.force,
        )

        if result:
            logger.info("Installation completed successfully")

        return result


def execute_doctor(orchestrator: "Orchestrator", args) -> bool:
    """Execute the doctor command.

    Args:
        orchestrator: Orchestrator instance
        args: Parsed command arguments

    Returns:
        True if successful, False otherwise
    """
    logger = get_logger(__name__)
    logger.info("Running diagnostic checks...")

    issues = orchestrator.diagnose()

    if not issues:
        logger.info("✅ No issues detected")
        return True

    # Display issues
    logger.warning(f"Found {len(issues)} issues:")
    for issue in issues:
        logger.warning(f"  - {issue}")

    if args.repair:
        logger.info("Attempting to repair issues...")
        repair_result = orchestrator.repair()

        if repair_result:
            logger.info("✅ Repair completed successfully")
        else:
            logger.error("❌ Repair failed")

        return repair_result
    else:
        logger.info("Use --repair to automatically fix these issues")
        return False


def execute_list(orchestrator: "Orchestrator", args) -> bool:
    """Execute the list command.

    Args:
        orchestrator: Orchestrator instance
        args: Parsed command arguments

    Returns:
        True if successful, False otherwise
    """
    if args.profiles or not any([args.components, args.installed]):
        # List profiles (default)
        profiles = orchestrator.list_profiles()
        print("Available profiles:")
        for profile in profiles:
            print(f"  {profile}")

    elif args.components:
        # List components
        components = orchestrator.list_components()
        print("Available components:")
        for component in components:
            print(f"  {component}")

    elif args.installed:
        # List installed components
        installed = orchestrator.list_installed()
        if installed:
            print("Installed components:")
            for component in installed:
                print(f"  {component}")
        else:
            print("No components installed")

    return True


def execute_uninstall(orchestrator: "Orchestrator", args) -> bool:
    """Execute the uninstall command.

    Args:
        orchestrator: Orchestrator instance
        args: Parsed command arguments

    Returns:
        True if successful, False otherwise
    """
    logger = get_logger(__name__)
    logger.info(f"Uninstalling components: {', '.join(args.components)}")

    result = orchestrator.uninstall(components=args.components)

    if result:
        logger.info("Uninstallation completed successfully")

    return result


def display_plan_text(plan, args) -> None:
    """Display installation plan in human-readable text format.

    Args:
        plan: InstallPlan object
        args: Command arguments for formatting options
    """
    # Colors (if not disabled)
    if args.no_color:
        colors = {"reset": "", "green": "", "yellow": "", "red": "", "blue": ""}
    else:
        colors = {
            "reset": "\033[0m",
            "green": "\033[32m",
            "yellow": "\033[33m",
            "red": "\033[31m",
            "blue": "\033[34m",
        }

    print(f"\n{colors['blue']}Installation Plan{colors['reset']}")
    print("=" * 50)
    print(f"Components: {plan.component_count}")
    print(f"Total files: {plan.total_files}")
    print(f"Actionable files: {plan.actionable_files}")
    print(f"Estimated size: {plan.estimated_size} bytes")
    print()

    for component in plan.components:
        print(f"{colors['blue']}Component: {component.name}{colors['reset']}")
        if component.plugin_id:
            print(f"  Plugin: {component.plugin_id}")
        print(f"  Files: {component.total_files} ({component.actionable_files} actionable)")

        for action in component.actions:
            # Color-code by action type
            if action.kind == "COPY":
                color = colors["green"]
            elif action.kind == "MERGE":
                color = colors["yellow"]
            elif action.kind == "TEMPLATE":
                color = colors["blue"]
            else:  # SKIP
                color = colors["reset"]

            print(f"    {color}{action.kind}{colors['reset']} {action.src} → {action.dst} ({action.reason})")

        print()


if __name__ == "__main__":
    sys.exit(main())
