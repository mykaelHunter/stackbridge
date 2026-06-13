output "bucket_id" {
  description = "S3 bucket name"
  value       = aws_s3_bucket.this.id
}

output "bucket_arn" {
  description = "S3 bucket ARN"
  value       = aws_s3_bucket.this.arn
}

output "presigned_url_policy_arn" {
  description = "IAM policy ARN for pre-signed URL generation. Attach to application role."
  value       = aws_iam_policy.presigned_url.arn
}
