#!/bin/bash
set -e

echo "Setting up Token-Efficient Search API for AI..."

# Check Python version
python3 --version

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

echo "Setup complete!"
echo ""
echo "Usage:"
echo "  source venv/bin/activate"
echo "  python -m src.cli --help"
