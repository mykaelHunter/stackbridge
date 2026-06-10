variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "ami_id" {
  description = "AMI ID for EC2 instances. Use latest Amazon Linux 2023."
  type        = string
  # Find the latest: aws ssm get-parameter \
  #   --name /aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64 \
  #   --query Parameter.Value --output text
}

variable "owner" {
  description = "Team or person responsible for this environment"
  type        = string
  default     = "platform"
}

variable "cost_center" {
  description = "Cost center for billing allocation"
  type        = string
  default     = "engineering"
}
