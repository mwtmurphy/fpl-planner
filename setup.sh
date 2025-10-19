#!/bin/bash

# FPL Optimiser Setup Script
# This script sets up the complete Poetry environment for the FPL project

set -e  # Exit on any error

echo "🚀 Setting up FPL Multi-GW Optimiser..."

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "📦 Installing Poetry..."
    curl -sSL https://install.python-poetry.org | python3 -

    # Add Poetry to PATH for this session
    export PATH="$HOME/.local/bin:$PATH"

    echo "✅ Poetry installed successfully!"
else
    echo "✅ Poetry is already installed"
fi

# Verify Poetry installation
poetry --version

# Install dependencies from pyproject.toml
echo "📚 Installing project dependencies..."
poetry install --no-root

echo "🏗️ Setting up project structure..."
poetry run make setup

echo "🔍 Verifying installation..."
poetry run python -c "
import requests
import pandas as pd
import numpy as np
import sklearn
import pulp
import duckdb
import typer
print('✅ All core dependencies imported successfully!')
"

echo ""
echo "🎉 Setup complete! Next steps:"
echo ""
echo "1. Activate Poetry shell:"
echo "   poetry shell"
echo ""
echo "2. Run the data collection:"
echo "   make data"
echo ""
echo "3. See all available commands:"
echo "   make help"
echo ""
echo "Happy optimising! 🏆"
