variable "name" {
  description = "Name prefix for EKS resources"
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
  description = "VPC ID to place the cluster in"
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet IDs — worker nodes live here"
  type        = list(string)
}

variable "public_subnet_ids" {
  description = "Public subnet IDs — needed for public-facing load balancers"
  type        = list(string)
}

variable "kubernetes_version" {
  description = "Kubernetes version for the EKS control plane"
  type        = string
  default     = "1.31"
}

variable "node_instance_type" {
  description = <<-EOT
    EC2 instance type for worker nodes.
    t3.small is the realistic free-tier-adjacent minimum — t3.micro
    technically works but leaves almost no room for actual workload
    pods after kubelet/kube-proxy/CNI overhead.
  EOT
  type    = string
  default = "t3a.medium"
}

variable "desired_node_count" {
  description = "Desired number of worker nodes"
  type        = number
  default     = 1
}

variable "min_node_count" {
  description = "Minimum number of worker nodes"
  type        = number
  default     = 1
}

variable "max_node_count" {
  description = "Maximum number of worker nodes"
  type        = number
  default     = 2
}

variable "capacity_type" {
  description = "ON_DEMAND or SPOT. SPOT is cheaper but nodes can be reclaimed."
  type        = string
  default     = "SPOT"

  validation {
    condition     = contains(["ON_DEMAND", "SPOT"], var.capacity_type)
    error_message = "capacity_type must be ON_DEMAND or SPOT"
  }
}

variable "public_access_cidrs" {
  description = "CIDRs allowed to reach the public Kubernetes API endpoint. Restrict in prod."
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "enabled_log_types" {
  description = <<-EOT
    EKS control plane log types to ship to CloudWatch.
    Empty by default to avoid ingestion cost in dev/staging.
    Example for prod: ["api", "audit", "authenticator"]
  EOT
  type    = list(string)
  default = []
}

variable "aws_region" {
  description = "AWS region the cluster is deployed in — used only to build the kubeconfig_command output"
  type        = string
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}
