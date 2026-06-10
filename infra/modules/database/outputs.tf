output "db_endpoint" {
  description = "RDS instance endpoint (host:port)"
  value       = aws_db_instance.this.endpoint
}

output "db_name" {
  description = "Database name"
  value       = aws_db_instance.this.db_name
}

output "secret_arn" {
  description = "ARN of the Secrets Manager secret containing DB credentials. Pass to application IAM policy."
  value       = aws_secretsmanager_secret.db_password.arn
}

output "security_group_id" {
  description = "DB security group ID"
  value       = aws_security_group.db.id
}

# NOTE: db_password is intentionally NOT output here.
# Applications read credentials from Secrets Manager at runtime.
# See: secret_arn output above.
