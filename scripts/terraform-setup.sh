#!/bin/bash

OUTPUT_FILE="trust-policy.json"

# Create the state bucket
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


