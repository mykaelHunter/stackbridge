#!bin/bash

set -euo pipefail

# 1. Locate the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 2. Check and source the file
if [ -f "$SCRIPT_DIR/.env" ]; then
    source "$SCRIPT_DIR/.env"
else
    echo "Error: .env file missing from $SCRIPT_DIR" >&2
    exit 1
fi

# 3. Safe-guard check for set -u
# This syntax checks if the variable is set without triggering the unbound error
if [ -z "${SLACK_WEBHOOK:-}" ]; then
    echo "Error: SLACK_WEBHOOK_URL is empty or not defined in your .env file." >&2
    exit 1
fi

curl -X POST -H 'Content-type: application/json' \
     --data "$payload" \
     "$SLACK_WEBHOOK"

# Create the state bucket
echo "Creating backend s3 bucket for state locking"

echo ""

aws s3 mb s3://stackbridge-tf-state --region us-east-1

# Enable versioning (so you can recover from bad state)
aws s3api put-bucket-versioning \
  --bucket stackbridge-tf-state \
  --versioning-configuration Status=Enabled

# Enable encryption
aws s3api put-bucket-encryption \
  --bucket stackbridge-tf-state \
  --server-side-encryption-configuration \
  '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'

echo ""

# Set up Python environment
echo "Setting up python environment"

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install e .

echo ""

# Creating Stackbridge environment
echo "Creating stackbridge staging environment"
echo "Make sure you have a tfvars file for the Amazon Linux AMI_ID"
sleep 10

echo ""

stackbridge environment create --env staging
sleep 10

echo ""

# Connecting kubectl to cluster
echo "Linking kubectl to eks cluster"

echo ""

aws eks update-kubeconfig --name stackbridge-staging --region us-east-1

echo ""

# Create service scaffold
echo "Creating and checking service scaffold list"

echo ""

stackbridge service scaffold stackbridge

echo ""

# Deploy service 
echo "Deploying services"

echo ""

pip uninstall stackbridge-platform -y
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete 2>/dev/null
find . -name "*.egg-info" -type d -exec rm -rf {} + 2>/dev/null
pip install -e .

echo ""

stackbridge environment bootstrap-secrets stackbridge --env staging   # → eso/staging
stackbridge service deploy stackbridge --env staging
stackbridge environment bootstrap-monitoring --values-file monitoring-values.yaml

echo ""

echo "Successful"

