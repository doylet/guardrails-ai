#!/bin/bash
# AI Guardrails Bootstrap Installer v1.0.0
# Quick installation script for the modular bootstrap architecture

set -euo pipefail

REPO_URL="https://raw.githubusercontent.com/yourorg/ai-guardrails/main"
SCRIPT_NAME="ai_guardrails_bootstrap_modular.sh"
INSTALL_DIR="${AI_GUARDRAILS_INSTALL_DIR:-$(pwd)}"

echo "🚀 Installing AI Guardrails Bootstrap..."
echo "📍 Installation directory: $INSTALL_DIR"

# Download the bootstrap script
if command -v curl >/dev/null 2>&1; then
    curl -fsSL "$REPO_URL/$SCRIPT_NAME" -o "$INSTALL_DIR/$SCRIPT_NAME"
elif command -v wget >/dev/null 2>&1; then
    wget -q "$REPO_URL/$SCRIPT_NAME" -O "$INSTALL_DIR/$SCRIPT_NAME"
else
    echo "❌ Error: curl or wget required for installation"
    exit 1
fi

# Make executable
chmod +x "$INSTALL_DIR/$SCRIPT_NAME"

echo "✅ AI Guardrails Bootstrap installed successfully!"
echo ""
echo "📋 Usage:"
echo "  ./$SCRIPT_NAME                    # Install guardrails to current project"
echo "  ./$SCRIPT_NAME --doctor           # Check installation status"
echo "  ./$SCRIPT_NAME --offline          # Install using embedded templates"
echo "  ./$SCRIPT_NAME --help             # Show all options"
echo ""
echo "🎯 Quick start: ./$SCRIPT_NAME"
