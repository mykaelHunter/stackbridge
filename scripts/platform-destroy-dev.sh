#!bin/bash

set -euo pipefail

# Set up Python environment
echo "Setting up python environment"

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip

echo ""

# Destroying platform architecture
echo "Destroying dev environment"

echo ""

stackbridge destroy --env dev --force

echo ""

echo "Deleting kops bucket"
echo "Press q when you see the : prompt"
aws s3api delete-objects \
    --bucket stackbridge-tf-state \
    --delete "$(aws s3api list-object-versions \
    --bucket stackbridge-tf-state \
    --output json \
    --query '{Objects: Versions[].{Key:Key,VersionId:VersionId}}')"

aws s3api delete-objects \
    --bucket stackbridge-tf-state \
    --delete "$(aws s3api list-object-versions \
    --bucket stackbridge-tf-state \
    --output json \
    --query '{Objects: DeleteMarkers[].{Key:Key,VersionId:VersionId}}')"

aws s3 rb s3://stackbridge-tf-state

echo ""

echo "Successful"

