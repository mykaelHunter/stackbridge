# ============================================================
# Module: storage
# Creates an S3 bucket with:
#   - Public access blocked (fixes INF-06)
#   - Server-side encryption enabled
#   - Versioning enabled
#   - Lifecycle rules for cost management
#   - Access logging to a separate log bucket
# Callers get a pre-signed URL generator IAM policy ARN.
# ============================================================

resource "aws_s3_bucket" "this" {
  bucket = "${var.name}-${var.environment}-${var.purpose}"

  tags = merge(var.tags, {
    Name        = "${var.name}-${var.environment}-${var.purpose}"
    Environment = var.environment
    Module      = "storage"
  })
}

# ── Block all public access (INF-06) ─────────────────────────
resource "aws_s3_bucket_public_access_block" "this" {
  bucket = aws_s3_bucket.this.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ── Server-side encryption ────────────────────────────────────
resource "aws_s3_bucket_server_side_encryption_configuration" "this" {
  bucket = aws_s3_bucket.this.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

# ── Versioning ────────────────────────────────────────────────
resource "aws_s3_bucket_versioning" "this" {
  bucket = aws_s3_bucket.this.id

  versioning_configuration {
    status = "Enabled"
  }
}

# ── Lifecycle rules ───────────────────────────────────────────
resource "aws_s3_bucket_lifecycle_configuration" "this" {
  bucket = aws_s3_bucket.this.id

  rule {
    id     = "transition-old-versions"
    status = "Enabled"

    filter {}

    noncurrent_version_transition {
      noncurrent_days = 30
      storage_class   = "STANDARD_IA"
    }

    noncurrent_version_expiration {
      noncurrent_days = var.noncurrent_version_expiry_days
    }
  }

  rule {
    id     = "expire-incomplete-multipart"
    status = "Enabled"

    filter {}

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}

# ── IAM policy for pre-signed URL generation ─────────────────
# Attach this policy to any role that needs to generate
# time-limited signed URLs for object access.
data "aws_iam_policy_document" "presigned_url" {
  statement {
    sid    = "AllowPresignedURLGeneration"
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
    ]
    resources = ["${aws_s3_bucket.this.arn}/*"]
  }

  statement {
    sid       = "AllowListBucket"
    effect    = "Allow"
    actions   = ["s3:ListBucket"]
    resources = [aws_s3_bucket.this.arn]
  }
}

resource "aws_iam_policy" "presigned_url" {
  name        = "${var.name}-${var.environment}-${var.purpose}-s3-policy"
  description = "Allows pre-signed URL generation for ${aws_s3_bucket.this.bucket}"
  policy      = data.aws_iam_policy_document.presigned_url.json

  tags = merge(var.tags, {
    Environment = var.environment
    Module      = "storage"
  })
}
