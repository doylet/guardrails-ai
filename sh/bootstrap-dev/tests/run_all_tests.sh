#!/usr/bin/env bash
# run_all_tests.sh - Comprehensive test runner for modular bootstrap
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Test suite tracking
TOTAL_SUITES=0
PASSED_SUITES=0
FAILED_SUITES=0

# Function to run a test suite
run_test_suite() {
    local suite_name="$1"
    local suite_script="$2"
    local description="$3"

    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}Test Suite: ${suite_name}${NC}"
    echo -e "${CYAN}Description: ${description}${NC}"
    echo -e "${CYAN}========================================${NC}"
    echo

    TOTAL_SUITES=$((TOTAL_SUITES + 1))

    if [[ ! -f "$suite_script" ]]; then
        echo -e "${RED}✗ Test suite script not found: $suite_script${NC}"
        FAILED_SUITES=$((FAILED_SUITES + 1))
        return 1
    fi

    if "./$suite_script"; then
        echo -e "${GREEN}✅ Test Suite PASSED: ${suite_name}${NC}"
        PASSED_SUITES=$((PASSED_SUITES + 1))
        return 0
    else
        echo -e "${RED}❌ Test Suite FAILED: ${suite_name}${NC}"
        FAILED_SUITES=$((FAILED_SUITES + 1))
        return 1
    fi
}

# Function to check prerequisites
check_prerequisites() {
    echo -e "${BLUE}Checking prerequisites...${NC}"

    local missing_tools=()

    # Check required tools
    command -v git >/dev/null || missing_tools+=("git")
    command -v bash >/dev/null || missing_tools+=("bash")

    # Check optional tools (warn but don't fail)
    local optional_tools=("curl" "wget" "python" "python3" "shellcheck" "pre-commit")
    local missing_optional=()

    for tool in "${optional_tools[@]}"; do
        if ! command -v "$tool" >/dev/null; then
            missing_optional+=("$tool")
        fi
    done

    if [[ ${#missing_tools[@]} -gt 0 ]]; then
        echo -e "${RED}Missing required tools: ${missing_tools[*]}${NC}"
        exit 1
    fi

    if [[ ${#missing_optional[@]} -gt 0 ]]; then
        echo -e "${YELLOW}Missing optional tools (some tests may be skipped): ${missing_optional[*]}${NC}"
    fi

    # Check network connectivity
    if ! ping -c 1 8.8.8.8 >/dev/null 2>&1; then
        echo -e "${YELLOW}No network connectivity detected. Network tests may be limited.${NC}"
    fi

    echo -e "${GREEN}Prerequisites check complete.${NC}"
    echo
}

# Function to display system information
show_system_info() {
    echo -e "${BLUE}System Information:${NC}"
    echo "OS: $(uname -s)"
    echo "Architecture: $(uname -m)"
    echo "Shell: $SHELL"
    echo "Bash version: $BASH_VERSION"

    if command -v git >/dev/null; then
        echo "Git version: $(git --version)"
    fi

    echo "Current directory: $(pwd)"
    echo "Test timestamp: $(date)"
    echo
}

# Function to run shellcheck on all scripts
run_shellcheck() {
    if ! command -v shellcheck >/dev/null; then
        echo -e "${YELLOW}Shellcheck not available, skipping static analysis${NC}"
        return 0
    fi

    echo -e "${BLUE}Running shellcheck on all scripts...${NC}"

    local scripts=(
        "ai_guardrails_bootstrap_modular.sh"
        "tests/test_bootstrap_modular.sh"
        "tests/test_network_scenarios.sh"
        "tests/test_integration.sh"
        "tests/run_all_tests.sh"
    )

    local shellcheck_failed=0

    for script in "${scripts[@]}"; do
        if [[ -f "$script" ]]; then
            echo "Checking $script..."
            if ! shellcheck "$script"; then
                shellcheck_failed=1
            fi
        fi
    done

    if [[ $shellcheck_failed -eq 0 ]]; then
        echo -e "${GREEN}✅ All scripts pass shellcheck${NC}"
    else
        echo -e "${RED}❌ Some scripts have shellcheck issues${NC}"
    fi

    echo
    return $shellcheck_failed
}

# Function to display final summary
show_summary() {
    echo
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}Final Test Summary${NC}"
    echo -e "${CYAN}========================================${NC}"
    echo "Total test suites: $TOTAL_SUITES"
    echo -e "Passed: ${GREEN}$PASSED_SUITES${NC}"

    if [[ $FAILED_SUITES -gt 0 ]]; then
        echo -e "Failed: ${RED}$FAILED_SUITES${NC}"
        echo
        echo -e "${RED}Some tests failed. Please review the output above.${NC}"
        return 1
    else
        echo -e "Failed: ${FAILED_SUITES}"
        echo
        echo -e "${GREEN}🎉 All test suites passed successfully!${NC}"
        echo -e "${GREEN}The modular bootstrap architecture is ready for deployment.${NC}"
        return 0
    fi
}

# Main execution
main() {
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║           AI Guardrails Bootstrap - Full Test Suite          ║${NC}"
    echo -e "${CYAN}║                    Modular Architecture                       ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo

    # Change to script directory
    cd "$(dirname "${BASH_SOURCE[0]}")/.."

    # Show system information
    show_system_info

    # Check prerequisites
    check_prerequisites

    # Run shellcheck if available
    run_shellcheck || echo -e "${YELLOW}Continuing despite shellcheck issues...${NC}"

    # Test suites in order of complexity
    local test_suites=(
        "Basic Functionality|tests/test_bootstrap_modular.sh|Core CLI functionality, doctor mode, version management"
        "Network Scenarios|tests/test_network_scenarios.sh|Network failure handling, offline mode, resilience testing"
        "Integration Testing|tests/test_integration.sh|Compatibility, migration, project type support"
    )

    local overall_result=0

    for suite_info in "${test_suites[@]}"; do
        IFS='|' read -r suite_name suite_script suite_description <<< "$suite_info"

        if ! run_test_suite "$suite_name" "$suite_script" "$suite_description"; then
            overall_result=1
        fi

        echo
    done

    # Show final summary
    if ! show_summary; then
        overall_result=1
    fi

    exit $overall_result
}

# Parse command line arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [options]"
        echo "Options:"
        echo "  --help, -h    Show this help message"
        echo "  --quick, -q   Run only basic tests (faster)"
        echo "  --network, -n Run only network tests"
        echo "  --integration, -i Run only integration tests"
        echo
        echo "This script runs the complete test suite for the modular bootstrap architecture."
        echo "It validates functionality, network resilience, and integration compatibility."
        exit 0
        ;;
    --quick|-q)
        echo "Running quick test suite (basic functionality only)..."
        cd "$(dirname "${BASH_SOURCE[0]}")/.."
        exec ./tests/test_bootstrap_modular.sh
        ;;
    --network|-n)
        echo "Running network test suite only..."
        cd "$(dirname "${BASH_SOURCE[0]}")/.."
        exec ./tests/test_network_scenarios.sh
        ;;
    --integration|-i)
        echo "Running integration test suite only..."
        cd "$(dirname "${BASH_SOURCE[0]}")/.."
        exec ./tests/test_integration.sh
        ;;
    "")
        # Run all tests
        main
        ;;
    *)
        echo "Unknown option: $1"
        echo "Use --help for usage information."
        exit 1
        ;;
esac
