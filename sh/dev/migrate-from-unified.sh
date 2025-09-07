#!/usr/bin/env bash
# migrate-from-unified.sh - Helper script to migrate from unified to modular bootstrap
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
MODULAR_SCRIPT="ai_guardrails_bootstrap_modular.sh"
UNIFIED_SCRIPT="ai_guardrails_bootstrap_unified.sh"
BACKUP_DIR=".ai_guardrails_backup_$(date +%Y%m%d_%H%M%S)"

# Functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_header() {
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║               AI Guardrails Migration Helper                  ║${NC}"
    echo -e "${CYAN}║                 Unified → Modular                            ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check if we're in a git repository
    if ! git rev-parse --git-dir >/dev/null 2>&1; then
        log_error "Not in a git repository. Migration requires git for safety."
        exit 1
    fi

    # Check for modular script
    if [[ ! -f "$MODULAR_SCRIPT" ]]; then
        log_error "Modular script not found: $MODULAR_SCRIPT"
        log_info "Please download the modular script first."
        exit 1
    fi

    # Check if current directory has existing installation
    if [[ ! -d .ai ]] && [[ ! -d ai ]]; then
        log_warning "No existing AI guardrails installation detected."
        log_info "This appears to be a fresh installation."
    fi

    log_success "Prerequisites check complete"
    echo
}

# Create backup
create_backup() {
    log_info "Creating backup of existing installation..."

    mkdir -p "$BACKUP_DIR"

    # Backup key directories and files
    local backup_items=(
        ".ai"
        "ai"
        ".github/workflows/ai_guardrails_on_commit.yml"
        ".pre-commit-config.yaml"
        ".github/pull_request_template.md"
        ".github/chatmodes"
    )

    for item in "${backup_items[@]}"; do
        if [[ -e "$item" ]]; then
            cp -r "$item" "$BACKUP_DIR/" 2>/dev/null || true
            log_info "Backed up: $item"
        fi
    done

    log_success "Backup created: $BACKUP_DIR"
    echo
}

# Run migration
run_migration() {
    log_info "Running migration to modular bootstrap..."

    # Use force to ensure all files are updated
    if ./"$MODULAR_SCRIPT" --apply --force --verbose; then
        log_success "Migration completed successfully"
    else
        log_error "Migration failed"
        return 1
    fi

    echo
}

# Validate migration
validate_migration() {
    log_info "Validating migration..."

    # Run doctor mode
    if ./"$MODULAR_SCRIPT" --doctor; then
        log_success "Doctor mode validation passed"
    else
        log_error "Doctor mode validation failed"
        return 1
    fi

    # Check key files exist
    local key_files=(
        ".ai/guardrails.yaml"
        ".ai/envelope.json"
        "ai/schemas/copilot_envelope.schema.json"
        "ai/scripts/check_envelope.py"
        ".pre-commit-config.yaml"
    )

    local missing_files=()
    for file in "${key_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            missing_files+=("$file")
        fi
    done

    if [[ ${#missing_files[@]} -gt 0 ]]; then
        log_error "Missing files after migration:"
        for file in "${missing_files[@]}"; do
            echo "  - $file"
        done
        return 1
    fi

    log_success "All key files present"
    echo
}

# Show rollback instructions
show_rollback_instructions() {
    log_info "Rollback instructions (if needed):"
    echo
    echo "If you encounter issues, you can rollback using:"
    echo "  1. Git rollback:"
    echo "     git checkout HEAD~1 -- .ai/ ai/ .github/ .pre-commit-config.yaml"
    echo
    echo "  2. Restore from backup:"
    echo "     cp -r $BACKUP_DIR/* ."
    echo
    echo "  3. Reinstall with unified script (if available):"
    echo "     ./$UNIFIED_SCRIPT --apply --force"
    echo
}

# Show next steps
show_next_steps() {
    log_success "Migration completed successfully!"
    echo
    log_info "Next steps:"
    echo "  1. Test your setup:"
    echo "     ./$MODULAR_SCRIPT --doctor"
    echo
    echo "  2. Explore new features:"
    echo "     ./$MODULAR_SCRIPT --list-versions"
    echo "     ./$MODULAR_SCRIPT --help"
    echo
    echo "  3. Update to latest templates anytime:"
    echo "     ./$MODULAR_SCRIPT --update"
    echo
    echo "  4. Use offline mode when needed:"
    echo "     ./$MODULAR_SCRIPT --offline"
    echo
    log_info "Keep your backup safe: $BACKUP_DIR"
    log_info "See docs/migration-guide.md for detailed information"
}

# Main execution
main() {
    log_header

    # Parse command line arguments
    case "${1:-}" in
        --help|-h)
            echo "Usage: $0 [options]"
            echo
            echo "Options:"
            echo "  --help, -h     Show this help message"
            echo "  --dry-run      Show what would be done without making changes"
            echo
            echo "This script helps migrate from the unified AI guardrails bootstrap"
            echo "to the new modular template repository approach."
            echo
            echo "The script will:"
            echo "  1. Check prerequisites and existing installation"
            echo "  2. Create a backup of current setup"
            echo "  3. Run the modular bootstrap script"
            echo "  4. Validate the migration"
            echo "  5. Provide rollback instructions"
            echo
            echo "For detailed migration information, see docs/migration-guide.md"
            exit 0
            ;;
        --dry-run)
            echo "DRY RUN MODE - No changes will be made"
            echo
            log_info "Would check prerequisites..."
            log_info "Would create backup in: $BACKUP_DIR"
            log_info "Would run: ./$MODULAR_SCRIPT --apply --force --verbose"
            log_info "Would validate migration with doctor mode"
            log_info "Would show rollback instructions and next steps"
            echo
            log_info "To perform actual migration, run without --dry-run"
            exit 0
            ;;
        "")
            # Continue with normal execution
            ;;
        *)
            log_error "Unknown option: $1"
            echo "Use --help for usage information."
            exit 1
            ;;
    esac

    # Run migration steps
    check_prerequisites
    create_backup

    if run_migration && validate_migration; then
        show_next_steps
    else
        log_error "Migration failed. Backup available at: $BACKUP_DIR"
        show_rollback_instructions
        exit 1
    fi
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
