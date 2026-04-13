#!/bin/bash

INSTALL_DIR="$HOME/.local/bin"
SCRIPT_NAME="addpath"
SOURCE="addpath.py"

echo ""
echo "  addpath installer"
echo "  -------------------"

if [ ! -f "$SOURCE" ]; then
    echo "  [ERROR] $SOURCE not found in current directory."
    echo "  Make sure you run this script from the same folder as addpath.py"
    exit 1
fi

mkdir -p "$INSTALL_DIR"

cp "$SOURCE" "$INSTALL_DIR/$SCRIPT_NAME"
chmod +x "$INSTALL_DIR/$SCRIPT_NAME"

echo "  [+] Installed to $INSTALL_DIR/$SCRIPT_NAME"

if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
    echo ""
    echo "  [!] $INSTALL_DIR is not in your PATH."
    echo "  Add this to your ~/.bashrc or ~/.zshrc:"
    echo ""
    echo "      export PATH=\"\$PATH:$INSTALL_DIR\""
    echo ""
    echo "  Then run: source ~/.bashrc"
else
    echo "  [+] $INSTALL_DIR is already in PATH. You're good to go."
    echo ""
    echo "  Run 'addpath' to get started."
fi

echo ""
