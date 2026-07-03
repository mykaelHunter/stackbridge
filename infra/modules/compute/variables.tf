variable "name" {
  description = "Name prefix for compute resources"
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
  description = "VPC ID to place the instance in"
  type        = string
}

variable "subnet_id" {
  description = "Subnet ID for the instance. Use a private subnet."
  type        = string
}

variable "ami_id" {
  description = "AMI ID. Use the latest Amazon Linux 2023 or Ubuntu 22.04 LTS."
  type        = string
}

variable "instance_type" {
  description = "EC2 instance type. OPA policy enforces the allowed list."
  type        = string
  default     = "t3.micro"
}

variable "root_volume_size_gb" {
  description = "Root EBS volume size in GB"
  type        = number
  default     = 20
}

variable "iam_instance_profile" {
  description = "IAM instance profile name for SSM access. Must include AmazonSSMManagedInstanceCore."
  type        = string
  default     = null
}

variable "user_data" {
  description = "EC2 user data script. Runs as root on first boot — use it to set up a non-root service user."
  type        = string
  default     = null
}

variable "ingress_rules" {
  description = <<-EOT
    List of ingress rules to allow. Only define what you need.
    Example: [{ description = "HTTP from LB", from_port = 80, to_port = 80, protocol = "tcp", cidr_blocks = [], security_groups = ["sg-123"] }]
  EOT
  type = list(object({
    description     = string
    from_port       = number
    to_port         = number
    protocol        = string
    cidr_blocks     = list(string)
  }))
  default = []
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}
