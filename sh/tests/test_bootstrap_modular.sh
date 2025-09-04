#!/usr/bin/env bash
# test_bootstrap_modular.sh - Test suite for modular bootstrap script
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Test function
test_case() {
    local test_name="$1"
    local test_command="$2"

    echo -e "${YELLOW}Running: ${test_name}${NC}"
    TESTS_RUN=$((TESTS_RUN + 1))

    if eval "$test_command"; then
        echo -e "${GREEN}✓ PASS: ${test_name}${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗ FAIL: ${test_name}${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    echo
}

# Setup temporary test directory
setup_test_env() {
    TEST_DIR="$(mktemp -d)"
    export TEST_DIR
    echo "Test environment: $TEST_DIR"

    # Copy modular script to test dir
    cp ai_guardrails_bootstrap_modular.sh "$TEST_DIR/"

    # Create a local template repo for testing
    mkdir -p "$TEST_DIR/local-templates/templates"
    cp -r ai-guardrails-templates/* "$TEST_DIR/local-templates/"

    cd "$TEST_DIR"
}

# Cleanup test environment
cleanup_test_env() {
    cd - > /dev/null
    rm -rf "$TEST_DIR"
}

# Test script help output
test_help_output() {
    ./ai_guardrails_bootstrap_modular.sh --help | grep -q "AI Guardrails Bootstrap"
}

# Test doctor mode
test_doctor_mode() {
    ./ai_guardrails_bootstrap_modular.sh --doctor | grep -q "== Doctor =="
}

# Test list versions
test_list_versions() {
    ./ai_guardrails_bootstrap_modular.sh --list-versions | grep -q "Available versions"
}

# Test template fetching with local repository
test_local_template_fetching() {
    mkdir -p test_project
    cd test_project

    # Initialize a git repo
    git init > /dev/null 2>&1

    # Test with local file:// URL (space-separated arguments)
    ../ai_guardrails_bootstrap_modular.sh --apply --template-repo "file://$TEST_DIR/local-templates" --verbose

    # Check that core files were created
    [[ -f .ai/guardrails.yaml ]] && [[ -f ai/schemas/copilot_envelope.schema.json ]]
}# Test offline mode fallback
test_offline_fallback() {
    mkdir -p test_project_offline
    cd test_project_offline

    # Initialize a git repo
    git init > /dev/null 2>&1

    # Test offline mode
    ../ai_guardrails_bootstrap_modular.sh --offline --verbose 2>&1 | grep -q "offline"
}

# Test ensure mode
test_ensure_mode() {
    mkdir -p test_project_ensure
    cd test_project_ensure

    # Initialize a git repo
    git init > /dev/null 2>&1

    # Test ensure mode - use relative path that will work from test dir
    if [[ -f ../ai_guardrails_bootstrap_modular.sh ]]; then
        ../ai_guardrails_bootstrap_modular.sh --ensure --verbose
    else
        # Fallback - copy script to local directory
        cp "$TEST_DIR/ai_guardrails_bootstrap_modular.sh" ./
        ./ai_guardrails_bootstrap_modular.sh --ensure --verbose
    fi

    # Should create minimal setup
    [[ -d .ai ]]
}

# Test script validation with shellcheck
test_shellcheck_validation() {
    if command -v shellcheck >/dev/null 2>&1; then
        if [[ -f ai_guardrails_bootstrap_modular.sh ]]; then
            shellcheck ai_guardrails_bootstrap_modular.sh
        else
            shellcheck "$TEST_DIR/ai_guardrails_bootstrap_modular.sh"
        fi
    else
        echo "shellcheck not available, skipping"
        return 0
    fi
}

# Main test execution
main() {
    echo "=== AI Guardrails Bootstrap Modular - Test Suite ==="
    echo

    # Change to script directory
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
    cd "$SCRIPT_DIR"

    # Setup test environment
    setup_test_env

    # Run tests
    test_case "Help Output" "test_help_output"
    test_case "Doctor Mode" "test_doctor_mode"
    test_case "List Versions" "test_list_versions"
    test_case "Local Template Fetching" "test_local_template_fetching"
    test_case "Offline Mode" "test_offline_fallback"
    test_case "Ensure Mode" "test_ensure_mode"
    test_case "Shellcheck Validation" "test_shellcheck_validation"

    # Cleanup
    cleanup_test_env

    # Report results
    echo "=== Test Results ==="
    echo "Tests run: $TESTS_RUN"
    echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
    if [[ $TESTS_FAILED -gt 0 ]]; then
        echo -e "Failed: ${RED}$TESTS_FAILED${NC}"
        exit 1
    else
        echo "All tests passed!"
        exit 0
    fi
}

# Run tests if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
