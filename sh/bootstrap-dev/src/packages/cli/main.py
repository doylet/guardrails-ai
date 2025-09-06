"""Main entry point for the AI Guardrails Bootstrap System CLI.

This module provides the main() function that coordinates argument parsing,
logging configuration, and command execution through the orchestrator.
"""

import sys

from .args import parse_args, validate_args
from ..adapters.logging import configure_logging, get_logger
from ..core.orchestrator import Orchestrator
from ..domain.errors import BootstrapError, ConflictError, DepError, DriftError, ValidationError, InstallationError


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
        orchestrator = Orchestrator(target_dir=args.target_dir)

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

        # Display enhanced error information
        display_enhanced_error(e, args)

        # Print structured error info if verbose
        if hasattr(args, "verbose") and args.verbose and hasattr(e, 'details') and e.details:
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

    plan = orchestrator.plan(
        profile=args.profile,
        template_repo=getattr(args, 'template_repo', None),
        plugins_dir=getattr(args, 'plugins_dir', None),
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

        results = orchestrator.install(
            profile=args.profile,
            template_repo=getattr(args, 'template_repo', None),
            plugins_dir=getattr(args, 'plugins_dir', None),
            dry_run=args.dry_run,
            force=args.force,
        )

        # Check if all components succeeded
        success = all(results.values())

        if success:
            logger.info("Installation completed successfully")
        else:
            failed_components = [comp for comp, result in results.items() if not result]
            logger.error(f"Installation failed for components: {', '.join(failed_components)}")

        return success


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

    diagnostics = orchestrator.doctor(
        components=getattr(args, 'components', None),
        repair=args.repair,
        dry_run=getattr(args, 'dry_run', False),
    )

    if not diagnostics:
        logger.info("✅ No issues detected")
        return True

    # Display diagnostics
    logger.warning(f"Found {len(diagnostics)} issues:")
    for diagnostic in diagnostics:
        print(f"  {diagnostic}")

    # Check if any errors were found
    has_errors = any(d.severity == "error" for d in diagnostics)

    if args.repair:
        # Repair was already attempted in the orchestrator.doctor() call
        repairable_count = sum(1 for d in diagnostics if d.repairable)
        if repairable_count > 0:
            logger.info(f"Repair attempted for {repairable_count} issues")
        return not has_errors  # Success if no errors remain
    else:
        if any(d.repairable for d in diagnostics):
            logger.info("Use --repair to automatically fix repairable issues")
        return not has_errors  # Success if no errors found


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

    # Uninstall each component individually
    results = []
    for component in args.components:
        result = orchestrator.uninstall(component)
        results.append(result)

    success = all(results)

    if success:
        logger.info("Uninstallation completed successfully")
    else:
        logger.error("Some components failed to uninstall")

    return success


def display_plan_text(plan, args) -> None:
    """Display installation plan in human-readable text format.

    Args:
        plan: InstallPlan object
        args: Command arguments for formatting options
    """
    # Colors (if not disabled)
    if getattr(args, 'no_color', False):
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
    print(f"Profile: {plan.profile}")
    print(f"Components: {len(plan.components)}")

    total_files = sum(len(comp.file_actions) for comp in plan.components)
    actionable_files = sum(1 for comp in plan.components for action in comp.file_actions if action.action_type != "SKIP")

    print(f"Total files: {total_files}")
    print(f"Actionable files: {actionable_files}")
    print()

    for component_plan in plan.components:
        print(f"{colors['blue']}Component: {component_plan.component_id}{colors['reset']}")
        print(f"  Files: {len(component_plan.file_actions)}")

        for action in component_plan.file_actions:
            # Color-code by action type
            if action.action_type == "COPY":
                color = colors["green"]
            elif action.action_type == "MERGE":
                color = colors["yellow"]
            elif action.action_type == "TEMPLATE":
                color = colors["blue"]
            else:  # SKIP
                color = colors["reset"]

            print(f"    {color}{action.action_type:8}{colors['reset']} {action.source_path} → {action.target_path} ({action.reason})")

        print()


def display_enhanced_error(error: BootstrapError, args) -> None:
    """Display enhanced error messages with resolution suggestions.

    Args:
        error: Bootstrap error to display
        args: Parsed command arguments
    """
    print(f"\n❌ Error: {error}")

    # Provide context-specific help
    if isinstance(error, ConflictError):
        print("\n💡 Resolution suggestions:")
        print("  • Use --force to override existing files")
        print("  • Check for conflicting component dependencies")
        print("  • Review your profile configuration")

    elif isinstance(error, DepError):
        print("\n💡 Resolution suggestions:")
        print("  • Check component dependencies in manifest files")
        print("  • Verify all required plugins are available")
        print("  • Use 'ai-guardrails list --components' to see available components")

    elif isinstance(error, DriftError):
        print("\n💡 Resolution suggestions:")
        print("  • Use 'ai-guardrails doctor' to diagnose drift issues")
        print("  • Use 'ai-guardrails doctor --repair' to fix drift automatically")
        print("  • Use --force to ignore drift and proceed")

    elif isinstance(error, ValidationError):
        print("\n💡 Resolution suggestions:")
        print("  • Check your installation manifest syntax")
        print("  • Verify plugin manifest files are valid")
        print("  • Use --verbose for detailed validation messages")

    elif isinstance(error, InstallationError):
        print("\n💡 Resolution suggestions:")
        print("  • Check available disk space")
        print("  • Verify write permissions in target directory")
        print("  • Use --dry-run to preview changes first")

    # Always show how to get more help
    print("\n🔍 For more details, run with --verbose")
    if not getattr(args, 'verbose', False):
        print("💬 For troubleshooting help, see the documentation or run 'ai-guardrails doctor'")


if __name__ == "__main__":
    sys.exit(main())
