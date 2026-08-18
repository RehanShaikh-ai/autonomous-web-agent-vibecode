#!/usr/bin/env bash

# Setup script for Autonomous Web Agent engineering environment
set -euo pipefail

echo "🚀 Setting up Autonomous Web Agent local development environment..."

# 1. Create python virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment 'venv'..."
    python3 -m venv venv
else
    echo "Virtual environment 'venv' already exists."
fi

# 2. Activate and install dependencies
source venv/bin/activate
echo "Installing dependencies..."
pip install --upgrade pip
pip install pydantic pytest fastapi uvicorn ruff playwright markitdown

# 3. Install Playwright binaries
echo "Installing Playwright browser binaries..."
playwright install chromium

echo "✅ Environment setup complete. Run 'source venv/bin/activate' to get started."
