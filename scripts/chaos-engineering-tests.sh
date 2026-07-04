#!bin/bash

set -euo pipefail

ENV=$1

# Set up Python environment
echo "Setting up python environment"

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install e .

echo ""

# Running the scaffolding of the services
stackbridge service scaffold az-failure 
stackbridge service scaffold stress
stackbridge service scaffold network-latency

# Running tests
echo "Running cpu-stress tests"
stackbridge service chaos run stress cpu-stress --env $ENV
stackbridge service chaos run stress az-failure --env $ENV
stackbridge service chaos run stress network-latency --env $ENV


