variable "name" {
  description = "Name prefix for all resources in this network"
  type        = string
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be one of: dev, staging, prod"
  }
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of AZs to deploy subnets into. Must have at least 2 for RDS."
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

variable "nat_gateway_enabled" {
  description = "Whether to provision a NAT gateway for private subnets. Disable in dev to reduce cost."
  type        = bool
  default     = true
}

variable "tags" {
  description = "Tags to apply to all resources. Must include Owner and CostCenter."
  type        = map(string)
  default     = {}
}
