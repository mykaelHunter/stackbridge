#!bin/bash

set -euo pipefail

# Set up Python environment
echo "Setting up python environment"

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip

echo ""

# Destroying platform architecture
echo "Destroying staging environment"

echo ""

stackbridge destroy --env staging --force

echo "Successful"

