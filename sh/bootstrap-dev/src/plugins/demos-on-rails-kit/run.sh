#!/usr/bin/env bash
# demos-on-rails-kit runner script

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$SCRIPT_DIR"

# Load environment if available
if [[ -f "$PLUGIN_ROOT/.env" ]]; then
    source "$PLUGIN_ROOT/.env"
fi

# Default values
AI_DECK_GEN_ROOT="${AI_DECK_GEN_ROOT:-/Users/thomasdoyle/Daintree/projects/python/ai_deck_gen}"
DECKGEN_CLI="${DECKGEN_CLI:-python $PLUGIN_ROOT/ai/tools/deckgen_bridge.py}"

usage() {
    cat <<EOF
demos-on-rails-kit runner

Usage:
    $0 test                     # Run integration tests
    $0 run <scenario.yaml>      # Run demo scenario
    $0 list                     # List available scenarios
    $0 setup                    # Setup environment

Examples:
    $0 test
    $0 run ai/demo_scenarios/example.yaml
    $0 setup

Environment:
    AI_DECK_GEN_ROOT    Path to ai-deck-gen project
    DECKGEN_CLI         CLI command for demos
    LM_STUDIO_URL       LMStudio server URL
    LM_STUDIO_MODEL     Model name
EOF
}

cmd_test() {
    echo "🧪 Running integration tests..."
    cd "$PLUGIN_ROOT"
    python test_integration.py
}

cmd_run() {
    local scenario="$1"
    echo "🚀 Running demo scenario: $scenario"
    cd "$PLUGIN_ROOT"

    if [[ ! -f "$scenario" ]]; then
        echo "❌ Scenario file not found: $scenario"
        exit 1
    fi

    export DECKGEN_CLI
    python ai/tools/demo_harness.py run "$scenario"
}

cmd_list() {
    echo "📋 Available demo scenarios:"
    find "$PLUGIN_ROOT/ai/demo_scenarios" -name "*.yaml" -exec basename {} \; | sort
}

cmd_setup() {
    echo "🔧 Setting up demos-on-rails-kit environment..."

    # Check for ai-deck-gen
    if [[ ! -d "$AI_DECK_GEN_ROOT" ]]; then
        echo "❌ ai-deck-gen not found at: $AI_DECK_GEN_ROOT"
        echo "   Set AI_DECK_GEN_ROOT environment variable to correct path"
        exit 1
    fi

    echo "✅ ai-deck-gen found: $AI_DECK_GEN_ROOT"

    # Check for LMStudio
    if command -v curl >/dev/null; then
        LM_STUDIO_URL="${LM_STUDIO_URL:-http://localhost:1234}"
        if curl -s "$LM_STUDIO_URL/v1/models" >/dev/null 2>&1; then
            echo "✅ LMStudio accessible: $LM_STUDIO_URL"
        else
            echo "⚠️  LMStudio not accessible: $LM_STUDIO_URL"
            echo "   Make sure LMStudio is running with local server enabled"
        fi
    fi

    # Create .env if it doesn't exist
    if [[ ! -f "$PLUGIN_ROOT/.env" ]]; then
        echo "📝 Creating .env file..."
        cp "$PLUGIN_ROOT/.env.example" "$PLUGIN_ROOT/.env"
        echo "   Edit .env file to customize settings"
    fi

    echo "🎉 Setup complete!"
}

main() {
    case "${1:-}" in
        test) cmd_test ;;
        run)
            if [[ $# -lt 2 ]]; then
                echo "❌ Scenario file required"
                usage
                exit 1
            fi
            cmd_run "$2"
            ;;
        list) cmd_list ;;
        setup) cmd_setup ;;
        -h|--help|help) usage ;;
        *)
            echo "❌ Unknown command: ${1:-}"
            usage
            exit 1
            ;;
    esac
}

main "$@"
