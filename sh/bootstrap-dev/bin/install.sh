#!/bin/bash
# AI Guardrails Bootstrap - Installation Script
# This script installs ai-guardrails for convenient system-wide access

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="${AI_GUARDRAILS_INSTALL_DIR:-$HOME/.local/bin}"
SYMLINK_NAME="ai-guardrails"

echo "🚀 Installing AI Guardrails Bootstrap..."

# Create install directory if it doesn't exist
mkdir -p "$INSTALL_DIR"

# Create symlink to the wrapper script
if [[ -L "$INSTALL_DIR/$SYMLINK_NAME" || -f "$INSTALL_DIR/$SYMLINK_NAME" ]]; then
    echo "Removing existing installation..."
    rm "$INSTALL_DIR/$SYMLINK_NAME"
fi

echo "Creating symlink: $INSTALL_DIR/$SYMLINK_NAME -> $SCRIPT_DIR/ai-guardrails"
ln -s "$SCRIPT_DIR/ai-guardrails" "$INSTALL_DIR/$SYMLINK_NAME"

# Check if install directory is in PATH
if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
    echo ""
    echo "⚠️  Note: $INSTALL_DIR is not in your PATH"
    echo "Add this to your shell profile (~/.bashrc, ~/.zshrc, etc.):"
    echo "    export PATH=\"$INSTALL_DIR:\$PATH\""
    echo ""
    echo "Or run: echo 'export PATH=\"$INSTALL_DIR:\$PATH\"' >> ~/.zshrc"
else
    echo "✅ $INSTALL_DIR is already in your PATH"
fi

echo ""
echo "✅ Installation complete!"
echo "Usage examples:"
echo "  ai-guardrails list-components"
echo "  ai-guardrails list-profiles"
echo "  ai-guardrails install standard"
echo "  ai-guardrails component demo-harness"
