# ============================================================
# Remote State Backend
# One S3 bucket + one DynamoDB table, shared across all
# environments. Each environment uses a different state key.
#
# Bootstrap (run once before any terraform init):
#   aws s3 mb s3://stackbridge-tf-state --region us-east-1
#   aws s3api put-bucket-versioning \
#     --bucket stackbridge-tf-state \
#     --versioning-configuration Status=Enabled
#   aws s3api put-bucket-encryption \
#     --bucket stackbridge-tf-state \
#     --server-side-encryption-configuration \
#     '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'
#   aws dynamodb create-table \
#     --table-name stackbridge-tf-lock \
#     --attribute-definitions AttributeName=LockID,AttributeType=S \
#     --key-schema AttributeName=LockID,KeyType=HASH \
#     --billing-mode PAY_PER_REQUEST \
#     --region us-east-1
# ============================================================

# This file is used as a partial backend config.
# Each environment passes its own key:
#
#   terraform init \
#     -backend-config="key=environments/dev/terraform.tfstate"
#
# See environments/dev/backend.hcl and environments/staging/backend.hcl

# The actual backend block lives in each environment's main.tf:
#
#   terraform {
#     backend "s3" {
#       bucket         = "stackbridge-tf-state"
#       key            = "environments/dev/terraform.tfstate"
#       region         = "us-east-1"
#       dynamodb_table = "stackbridge-tf-lock"
#       encrypt        = true
#     }
#   }
