#!/bin/bash
# AI Guardrails Bootstrap - Production Interface
# Version: 2.0.0 (Infrastructure-as-Code)
# Description: Simple wrapper for infrastructure_bootstrap.py with backward compatibility

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRASTRUCTURE_ENGINE="${SCRIPT_DIR}/../infrastructure_bootstrap.py"
MANIFEST_FILE="${SCRIPT_DIR}/../installation-manifest.yaml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Help function
show_help() {
    cat << EOF
AI Guardrails Bootstrap v2.0.0

USAGE:
    ai-guardrails-bootstrap [OPTIONS] [COMPONENT...]

OPTIONS:
    -h, --help              Show this help message
    -p, --profile PROFILE   Installation profile (minimal|standard|full)
    -t, --target DIR        Target directory (default: current)
    --list-components       List available components
    --list-profiles         List available profiles
    --dry-run              Show what would be installed without installing
    --force                Force overwrite existing files

COMPONENTS:
    Can specify individual components instead of profile.
    Use --list-components to see available options.

EXAMPLES:
    # Install standard profile in current directory
    ai-guardrails-bootstrap --profile standard

    # Install specific components
    ai-guardrails-bootstrap docs precommit

    # Dry run to see what would be installed
    ai-guardrails-bootstrap --profile full --dry-run

    # Force overwrite in specific directory
    ai-guardrails-bootstrap --target /path/to/project --force

INFRASTRUCTURE-AS-CODE:
    This version uses infrastructure_bootstrap.py with declarative 
    configuration in installation-manifest.yaml. No more hardcoded 
    file lists - templates are discovered dynamically.

EOF
}

# Check dependencies
check_dependencies() {
    if ! command -v python3 &> /dev/null; then
        print_error "python3 is required but not installed"
        exit 1
    fi
    
    if [[ ! -f "$INFRASTRUCTURE_ENGINE" ]]; then
        print_error "Infrastructure engine not found: $INFRASTRUCTURE_ENGINE"
        exit 1
    fi
    
    if [[ ! -f "$MANIFEST_FILE" ]]; then
        print_error "Installation manifest not found: $MANIFEST_FILE"
        exit 1
    fi
}

# Main execution
main() {
    local args=()
    
    # Parse arguments and convert to infrastructure_bootstrap.py format
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -p|--profile)
                args+=("--profile" "$2")
                shift 2
                ;;
            -t|--target)
                args+=("--target" "$2")
                shift 2
                ;;
            --list-components)
                args+=("list-components")
                shift
                ;;
            --list-profiles)
                # Profiles are handled by the install command
                args+=("install" "--help")
                shift
                ;;
            --dry-run)
                print_info "Dry-run mode: Using discover to show what would be installed"
                args=("discover")
                shift
                ;;
            --force)
                args+=("--force")
                shift
                ;;
            -*)
                print_error "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
            *)
                # Assume it's a component name
                args+=("$1")
                shift
                ;;
        esac
    done
    
    # Default action if no specific action provided
    if [[ ${#args[@]} -eq 0 ]]; then
        args=("--profile" "standard")
    fi
    
    # Check if first arg looks like a command vs component
    if [[ ${#args[@]} -gt 0 && "${args[0]}" == "list-components" ]]; then
        # Direct command, pass through
        :
    elif [[ ${#args[@]} -gt 0 && "${args[0]}" != "--"* && "${args[0]}" != "list-components" && "${args[0]}" != "discover" && "${args[0]}" != "install" && "${args[0]}" != "component" ]]; then
        # Looks like component names, use component command
        args=("component" "${args[@]}")
    elif [[ ${#args[@]} -gt 0 && "${args[0]}" == "--profile" ]]; then
        # Profile specified, use install command
        args=("install" "${args[@]}")
    fi
    
    print_info "AI Guardrails Bootstrap v2.0.0 (Infrastructure-as-Code)"
    print_info "Using manifest: $(basename "$MANIFEST_FILE")"
    print_info "Engine: $(basename "$INFRASTRUCTURE_ENGINE")"
    
    # Execute the infrastructure engine
    python3 "$INFRASTRUCTURE_ENGINE" "${args[@]}"
    
    if [[ $? -eq 0 ]]; then
        print_success "Bootstrap completed successfully"
    else
        print_error "Bootstrap failed"
        exit 1
    fi
}

# Verify dependencies and run
check_dependencies
main "$@"
