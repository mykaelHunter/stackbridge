#!/bin/bash

OUTPUT_FILE="trust-policy.json"

# Create the state bucket
aws s3 mb s3://stackbridge-tf-state --region us-east-1

# Enable versioning (so you can recover from bad state)
aws s3api put-bucket-versioning \
  --bucket stackbridge-tfs-state \
  --versioning-configuration Status=Enabled

# Enable encryption
aws s3api put-bucket-encryption \
  --bucket stackbridge-tfs-state \
  --server-side-encryption-configuration \
  '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'

# Create the OIDC provider (one-time)
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1

cat << EOF > "$OUTPUT_FILE"
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::YOUR_ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:YOUR_GITHUB_ORG/stackbridge:*"
        }
      }
    }
  ]
}
EOF

aws iam create-role \
  --role-name stackbridge-terraform-role \
  --assume-role-policy-document file://trust-policy.json

aws iam attach-role-policy \
  --role-name stackbridge-terraform-role \
  --policy-arn arn:aws:iam::aws:policy/PowerUserAccess
