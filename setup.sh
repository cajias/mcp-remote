#!/bin/bash

# Exit on first error
set -e

# Change to project directory
cd "$(dirname "$0")"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install project in editable mode with dependencies
pip install -e .

# Install development dependencies
pip install pytest

# Run tests
pytest tests/
