#!/bin/bash
# Run this ONCE to allow macOS to open the Essay Reviewer.
# After this, you can double-click "Start Essay Reviewer.command" in Finder.
#
# Usage: Open Terminal, then run:
#   cd /path/to/essay-reviewer
#   bash setup.sh

cd "$(dirname "$0")"

echo ""
echo "  Setting up Essay Reviewer..."
echo ""

# Remove macOS quarantine flags from all project files
xattr -cr . 2>/dev/null

# Make the start script executable
chmod +x "Start Essay Reviewer.command" 2>/dev/null

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "  ⚠  Python 3 not found. Install from https://python.org"
    exit 1
fi

# Install dependencies
echo "  Installing dependencies..."
pip3 install -r requirements.txt --quiet 2>/dev/null
if [ $? -ne 0 ]; then
    pip3 install -r requirements.txt --quiet --user 2>/dev/null
fi

echo ""
echo "  ✓ Setup complete!"
echo ""
echo "  You can now double-click 'Start Essay Reviewer.command' in Finder."
echo "  Or run: python3 server.py"
echo ""
