variable "name" {
  description = "Name prefix for database resources"
  type        = string
}

variable "environment" {
  description = "Deployment environment"
  type        = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be one of: dev, staging, prod"
  }
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "private_subnet_ids" {
  description = "List of private subnet IDs for the DB subnet group. Requires at least 2 (different AZs)."
  type        = list(string)
}

variable "app_security_group_id" {
  description = "Security group ID of the app tier. Only this SG can reach port 5432."
  type        = string
}

variable "db_name" {
  description = "Name of the database to create"
  type        = string
  default     = "stackbridge"
}

variable "db_username" {
  description = "Master username for the RDS instance"
  type        = string
  default     = "sbadmin"
}

variable "postgres_version" {
  description = "PostgreSQL engine version"
  type        = string
  default     = "15.4"
}

variable "instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "allocated_storage_gb" {
  description = "Allocated storage in GB"
  type        = number
  default     = 20
}

variable "backup_retention_days" {
  description = "Number of days to retain automated backups. Minimum 7 for production."
  type        = number
  default     = 7

  validation {
    condition     = var.backup_retention_days >= 1
    error_message = "backup_retention_days must be at least 1. Set to 7 for prod."
  }
}

variable "multi_az" {
  description = "Enable Multi-AZ deployment. Always true in prod."
  type        = bool
  default     = false
}

variable "deletion_protection" {
  description = "Prevent the database from being deleted. Always true in prod."
  type        = bool
  default     = true
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}
