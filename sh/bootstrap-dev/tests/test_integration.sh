#!/usr/bin/env bash
# test_integration.sh - Integration tests for modular bootstrap
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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
    echo "Integration test environment: $TEST_DIR"

    # Get the script directory
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

    # Copy both scripts to test dir (if they exist)
    if [[ -f "$SCRIPT_DIR/src/ai_guardrails_bootstrap_unified.sh" ]]; then
        cp "$SCRIPT_DIR/src/ai_guardrails_bootstrap_unified.sh" "$TEST_DIR/"
    fi
    if [[ -f "$SCRIPT_DIR/src/ai_guardrails_bootstrap_modular.sh" ]]; then
        cp "$SCRIPT_DIR/src/ai_guardrails_bootstrap_modular.sh" "$TEST_DIR/"
    fi

    # Copy template repo for local testing
    if [[ -d "$SCRIPT_DIR/src/ai-guardrails-templates" ]]; then
        cp -r "$SCRIPT_DIR/src/ai-guardrails-templates" "$TEST_DIR/"
    fi

    cd "$TEST_DIR"
}

# Cleanup test environment
cleanup_test_env() {
    cd - > /dev/null
    rm -rf "$TEST_DIR"
}

# Test that modular produces same files as unified
test_output_compatibility() {
    # Create two identical projects
    mkdir -p unified_output modular_output

    # Test unified script
    cd unified_output
    git init > /dev/null 2>&1
    ../ai_guardrails_bootstrap_unified.sh --apply > /dev/null 2>&1
    cd ..

    # Test modular script with local templates
    cd modular_output
    git init > /dev/null 2>&1
    ../ai_guardrails_bootstrap_modular.sh --apply --template-repo="file://$TEST_DIR/ai-guardrails-templates" > /dev/null 2>&1
    cd ..

    # Compare key files exist in both
    local key_files=(
        ".ai/guardrails.yaml"
        ".ai/envelope.json"
        "ai/schemas/copilot_envelope.schema.json"
        "ai/scripts/check_envelope.py"
        "ai/scripts/lang_lint.sh"
        ".pre-commit-config.yaml"
        ".github/workflows/ai_guardrails_on_commit.yaml"
    )

    for file in "${key_files[@]}"; do
        [[ -f "unified_output/$file" ]] || { echo "Missing in unified: $file"; return 1; }
        [[ -f "modular_output/$file" ]] || { echo "Missing in modular: $file"; return 1; }
    done

    # Compare content of key files (allowing for minor differences)
    diff -q "unified_output/.ai/guardrails.yaml" "modular_output/.ai/guardrails.yaml" >/dev/null
}

# Test migration from existing unified installation
test_migration_scenario() {
    mkdir -p migration_test
    cd migration_test
    git init > /dev/null 2>&1

    # Install with unified script first
    ../ai_guardrails_bootstrap_unified.sh --apply > /dev/null 2>&1

    # Backup original files
    cp .ai/guardrails.yaml .ai/guardrails.yaml.backup

    # Install with modular script (should update, not break)
    ../ai_guardrails_bootstrap_modular.sh --apply --template-repo="file://$TEST_DIR/ai-guardrails-templates" --force > /dev/null 2>&1

    # Verify files still exist and are valid
    [[ -f .ai/guardrails.yaml ]] && [[ -f ai/schemas/copilot_envelope.schema.json ]]

    cd ..
}

# Test different project types
test_project_type_compatibility() {
    local project_types=("python" "node" "go" "rust")

    for project_type in "${project_types[@]}"; do
        mkdir -p "test_${project_type}"
        cd "test_${project_type}"
        git init > /dev/null 2>&1

        # Create project type indicators
        case $project_type in
            python)
                echo "requests==2.31.0" > requirements.txt
                echo "print('hello')" > main.py
                ;;
            node)
                echo '{"name": "test", "version": "1.0.0"}' > package.json
                echo "console.log('hello');" > index.js
                ;;
            go)
                echo "module test" > go.mod
                printf 'package main\nimport "fmt"\nfunc main() { fmt.Println("hello") }' > main.go
                ;;
            rust)
                mkdir -p src
                printf '[package]\nname = "test"\nversion = "0.1.0"' > Cargo.toml
                echo 'fn main() { println!("hello"); }' > src/main.rs
                ;;
        esac

        # Install guardrails
        ../ai_guardrails_bootstrap_modular.sh --apply --template-repo="file://$TEST_DIR/ai-guardrails-templates" > /dev/null 2>&1

        # Verify installation worked
        [[ -f .ai/guardrails.yaml ]] || { echo "Failed for $project_type"; return 1; }

        cd ..
    done
}

# Test pre-commit hook installation and functionality
test_precommit_integration() {
    mkdir -p precommit_test
    cd precommit_test
    git init > /dev/null 2>&1

    # Install guardrails
    ../ai_guardrails_bootstrap_modular.sh --apply --template-repo="file://$TEST_DIR/ai-guardrails-templates" > /dev/null 2>&1

    # Verify pre-commit config exists
    [[ -f .pre-commit-config.yaml ]] || return 1

    # Test pre-commit installation (if pre-commit is available)
    if command -v pre-commit >/dev/null 2>&1; then
        # Install pre-commit hooks
        pre-commit install > /dev/null 2>&1

        # Verify hooks were installed
        [[ -f .git/hooks/pre-commit ]] || return 1
    else
        echo "pre-commit not available, skipping hook installation test"
    fi

    cd ..
}

# Test doctor mode validation
test_doctor_validation() {
    mkdir -p doctor_test
    cd doctor_test
    git init > /dev/null 2>&1

    # Install guardrails
    ../ai_guardrails_bootstrap_modular.sh --apply --template-repo="file://$TEST_DIR/ai-guardrails-templates" > /dev/null 2>&1

    # Run doctor mode
    output=$(../ai_guardrails_bootstrap_modular.sh --doctor 2>&1)

    # Should pass validation
    echo "$output" | grep -q "Key files present" && echo "$output" | grep -q "Done"

    cd ..
}

# Test update scenario
test_update_scenario() {
    mkdir -p update_test
    cd update_test
    git init > /dev/null 2>&1

    # Install initial version
    ../ai_guardrails_bootstrap_modular.sh --apply --template-repo="file://$TEST_DIR/ai-guardrails-templates" > /dev/null 2>&1

    # Modify a file to simulate older version
    echo "# old version marker" >> .ai/guardrails.yaml

    # Run update
    ../ai_guardrails_bootstrap_modular.sh --update --template-repo="file://$TEST_DIR/ai-guardrails-templates" --force > /dev/null 2>&1

    # Verify update worked (old marker should be gone)
    grep -q "old version marker" .ai/guardrails.yaml && exit 1

    cd ..
}

# Test ensure mode (minimal setup)
test_ensure_mode() {
    mkdir -p ensure_test
    cd ensure_test
    git init > /dev/null 2>&1

    # Run ensure mode
    ../ai_guardrails_bootstrap_modular.sh --ensure > /dev/null 2>&1

    # Should create minimal setup
    [[ -d .ai ]] && [[ -f .ai/guardrails.yaml ]]

    cd ..
}

# Main test execution
main() {
    echo "=== AI Guardrails Bootstrap - Integration Test Suite ==="
    echo

    # Change to script directory
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
    cd "$SCRIPT_DIR"

    # Verify we have both scripts
    if [[ ! -f ai_guardrails_bootstrap_unified.sh ]]; then
        echo "Warning: Unified script not found. Some compatibility tests will be skipped."
    fi

    if [[ ! -f ai_guardrails_bootstrap_modular.sh ]]; then
        echo "Error: Modular script not found."
        exit 1
    fi

    # Setup test environment
    setup_test_env

    # Run integration tests
    if [[ -f ai_guardrails_bootstrap_unified.sh ]]; then
        test_case "Output Compatibility (Unified vs Modular)" "test_output_compatibility"
        test_case "Migration from Unified Installation" "test_migration_scenario"
    else
        echo -e "${BLUE}Skipping unified compatibility tests${NC}"
    fi

    test_case "Project Type Compatibility" "test_project_type_compatibility"
    test_case "Pre-commit Integration" "test_precommit_integration"
    test_case "Doctor Mode Validation" "test_doctor_validation"
    test_case "Update Scenario" "test_update_scenario"
    test_case "Ensure Mode" "test_ensure_mode"

    # Cleanup
    cleanup_test_env

    # Report results
    echo "=== Integration Test Results ==="
    echo "Tests run: $TESTS_RUN"
    echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
    if [[ $TESTS_FAILED -gt 0 ]]; then
        echo -e "Failed: ${RED}$TESTS_FAILED${NC}"
        exit 1
    else
        echo "All integration tests passed!"
        exit 0
    fi
}

# Run tests if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
