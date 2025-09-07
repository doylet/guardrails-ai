#!/usr/bin/env bash
# test_network_scenarios.sh - Network failure and resilience testing
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

# Setup test environment
setup_test_env() {
    TEST_DIR="$(mktemp -d)"
    export TEST_DIR
    echo "Network test environment: $TEST_DIR"

    # Get the script directory
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

    # Copy modular script to test dir
    cp "$SCRIPT_DIR/src/ai_guardrails_bootstrap_modular.sh" "$TEST_DIR/"

    cd "$TEST_DIR"
}

# Cleanup test environment
cleanup_test_env() {
    cd - > /dev/null
    rm -rf "$TEST_DIR"
}

# Test with invalid URL (should fallback to offline)
test_invalid_url_fallback() {
    mkdir -p test_invalid_url
    cd test_invalid_url
    git init > /dev/null 2>&1

    # Test with completely invalid URL
    output=$(../ai_guardrails_bootstrap_modular.sh --apply --template-repo="https://invalid.nonexistent.domain/templates" --verbose 2>&1)

    # Should fallback to offline mode and still succeed
    echo "$output" | grep -q "offline\|embedded\|fallback" && [[ -f .ai/guardrails.yaml ]]
}

# Test with valid domain but invalid path
test_valid_domain_invalid_path() {
    mkdir -p test_invalid_path
    cd test_invalid_path
    git init > /dev/null 2>&1

    # Test with valid domain but invalid path
    output=$(../ai_guardrails_bootstrap_modular.sh --apply --template-repo="https://github.com/nonexistent/repo" --verbose 2>&1)

    # Should fallback gracefully
    echo "$output" | grep -q "offline\|embedded\|fallback\|404"
}

# Test with no network tools available
test_no_network_tools() {
    mkdir -p test_no_tools
    cd test_no_tools
    git init > /dev/null 2>&1

    # Create a wrapper script that hides curl and wget
    cat > wrapper.sh << 'EOF'
#!/bin/bash
export PATH="/usr/bin:/bin"
# Remove common network tool paths
export PATH=$(echo "$PATH" | tr ':' '\n' | grep -v curl | grep -v wget | tr '\n' ':')
exec "$@"
EOF
    chmod +x wrapper.sh

    # Run without network tools - should force offline mode
    output=$(./wrapper.sh ../ai_guardrails_bootstrap_modular.sh --apply --verbose 2>&1)

    # Should warn about missing tools and use offline mode
    echo "$output" | grep -q "curl.*wget.*not found\|offline"
}

# Test network timeout simulation
test_network_timeout() {
    mkdir -p test_timeout
    cd test_timeout
    git init > /dev/null 2>&1

    # Use a URL that will timeout (httpbin delay endpoint)
    output=$(timeout 10s ../ai_guardrails_bootstrap_modular.sh --apply --template-repo="https://httpbin.org/delay/30" --verbose 2>&1 || true)

    # Should handle timeout gracefully
    echo "$output" | grep -q "timeout\|offline\|fallback" || [[ $? -eq 124 ]]  # 124 is timeout exit code
}

# Test offline mode explicitly
test_explicit_offline_mode() {
    mkdir -p test_explicit_offline
    cd test_explicit_offline
    git init > /dev/null 2>&1

    # Test explicit offline mode
    output=$(../ai_guardrails_bootstrap_modular.sh --offline --apply --verbose 2>&1)

    # Should use embedded templates and succeed
    echo "$output" | grep -q "offline\|embedded" && [[ -f .ai/guardrails.yaml ]]
}

# Test with different network tools (curl vs wget)
test_network_tool_fallback() {
    # This test checks if the script properly falls back between curl and wget
    mkdir -p test_tool_fallback
    cd test_tool_fallback
    git init > /dev/null 2>&1

    # Test that script handles missing curl by using wget (if available)
    if command -v wget >/dev/null 2>&1; then
        # Create script that hides curl
        cat > no_curl.sh << 'EOF'
#!/bin/bash
if [[ "$1" == "curl" ]]; then
    echo "curl: command not found" >&2
    exit 127
fi
exec "$@"
EOF
        chmod +x no_curl.sh

        # Should fall back to wget
        PATH="$PWD:$PATH" ../ai_guardrails_bootstrap_modular.sh --list-versions --verbose 2>&1 | grep -q "wget\|Available versions"
    else
        echo "wget not available, skipping curl fallback test"
        return 0
    fi
}

# Test partial download recovery
test_partial_download_recovery() {
    mkdir -p test_partial
    cd test_partial
    git init > /dev/null 2>&1

    # Simulate partial download by using a URL that returns incomplete data
    # This is harder to test without a mock server, so we'll test the error handling
    output=$(../ai_guardrails_bootstrap_modular.sh --apply --template-repo="https://httpbin.org/status/500" --verbose 2>&1 || true)

    # Should handle HTTP errors gracefully
    echo "$output" | grep -q "500\|error\|offline\|fallback"
}

# Main test execution
main() {
    echo "=== AI Guardrails Bootstrap - Network Scenarios Test Suite ==="
    echo

    # Change to script directory
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
    cd "$SCRIPT_DIR"

    # Check if we have network connectivity for some tests
    if ! ping -c 1 8.8.8.8 >/dev/null 2>&1; then
        echo "Warning: No network connectivity detected. Some tests may be skipped."
    fi

    # Setup test environment
    setup_test_env

    # Run network scenario tests
    test_case "Invalid URL Fallback" "test_invalid_url_fallback"
    test_case "Valid Domain Invalid Path" "test_valid_domain_invalid_path"
    test_case "No Network Tools Available" "test_no_network_tools"
    test_case "Network Timeout Handling" "test_network_timeout"
    test_case "Explicit Offline Mode" "test_explicit_offline_mode"
    test_case "Network Tool Fallback" "test_network_tool_fallback"
    test_case "Partial Download Recovery" "test_partial_download_recovery"

    # Cleanup
    cleanup_test_env

    # Report results
    echo "=== Network Test Results ==="
    echo "Tests run: $TESTS_RUN"
    echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
    if [[ $TESTS_FAILED -gt 0 ]]; then
        echo -e "Failed: ${RED}$TESTS_FAILED${NC}"
        exit 1
    else
        echo "All network tests passed!"
        exit 0
    fi
}

# Run tests if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
