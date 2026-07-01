#!bin/bash

set -euo pipefail

# Create the state bucket
echo "Creating backend s3 bucket for state locking"

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

# Set up Python environment
echo "Setting up python environment"

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip

# Creating Stackbridge environment
echo "Creating stackbridge dev environment"
echo "Make sure you have a tfvars file for the Amazon Linux AMI_ID"

sleep 10

stackbridge create --env dev

# Connecting kubectl to cluster
echo "Linking kubectl to eks cluster"

aws eks update-kubeconfig --name stackbridge-dev --region us-east-1

# Create service scaffold
echo "Creating and checking service scaffold list"

stackbridge service scaffold stackbridge
stackbridge service list

# Deploy service 
echo "Deploying services"

pip uninstall stackbridge-platform -y
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete 2>/dev/null
find . -name "*.egg-info" -type d -exec rm -rf {} + 2>/dev/null
pip install -e .
stackbridge service deploy stackbridge

echo "Successful"


