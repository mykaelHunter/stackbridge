# ============================================================
# Environment: dev
# Provisions a full dev environment by calling the module
# library. No resources are defined here directly.
#
# Notable dev-specific choices:
#   - NAT gateway disabled (saves ~$30/month)
#   - Multi-AZ disabled
#   - Smaller instance classes
#   - Deletion protection off (easier teardown)
#   - Backup retention: 1 day
# ============================================================

terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket       = "stackbridge-tf-state"
    key          = "environments/dev/terraform.tfstate"
    region       = "us-east-1"
    use_lockfile = true   # native S3 locking (replaces deprecated dynamodb_table)
    encrypt      = true
  }
}

provider "aws" {
  region = var.aws_region

  # No hardcoded credentials here — ever.
  # Auth via: IAM instance profile, OIDC (GitHub Actions),
  # or `aws sso login` for local dev.
  # See: https://registry.terraform.io/providers/hashicorp/aws/latest/docs#authentication

  default_tags {
    tags = local.common_tags
  }
}

locals {
  environment = "dev"
  name        = "stackbridge"

  common_tags = {
    Environment = local.environment
    Project     = local.name
    Owner       = var.owner
    ManagedBy   = "terraform"
    CostCenter  = var.cost_center
  }
}

# ── Network ───────────────────────────────────────────────────
module "network" {
  source = "../../modules/network"

  name                = local.name
  environment         = local.environment
  vpc_cidr            = "10.1.0.0/16"
  availability_zones  = ["us-east-1a", "us-east-1b"]
  nat_gateway_enabled = false # disabled in dev to save cost
  tags                = local.common_tags
}

# ── Compute ───────────────────────────────────────────────────
module "compute" {
  source = "../../modules/compute"

  name          = local.name
  environment   = local.environment
  vpc_id        = module.network.vpc_id
  subnet_id     = module.network.private_subnet_ids[0]
  ami_id        = var.ami_id
  instance_type = "t3.micro"
  tags          = local.common_tags

  ingress_rules = [
    {
      description     = "HTTP from within VPC only"
      from_port       = 5000
      to_port         = 5000
      protocol        = "tcp"
      cidr_blocks     = [module.network.vpc_cidr]
    }
  ]
}

# ── Database ──────────────────────────────────────────────────
module "database" {
  source = "../../modules/database"

  name                  = local.name
  environment           = local.environment
  vpc_id                = module.network.vpc_id
  private_subnet_ids    = module.network.private_subnet_ids
  app_security_group_id = module.compute.security_group_id
  instance_class        = "db.t3.micro"
  backup_retention_days = 1
  multi_az              = false
  deletion_protection   = false # allow easy teardown in dev
  tags                  = local.common_tags
}

# ── Storage ───────────────────────────────────────────────────
module "storage" {
  source = "../../modules/storage"

  name        = local.name
  environment = local.environment
  purpose     = "uploads"
  tags        = local.common_tags
}

# ── EKS ───────────────────────────────────────────────────────
# Single t3.small node by default — see modules/eks/main.tf header
# for the free tier cost breakdown. The control plane itself is
# NOT free tier eligible (~$0.10/hr regardless of size).
module "eks" {
  source = "../../modules/eks"

  name                = local.name
  environment         = local.environment
  aws_region          = var.aws_region
  vpc_id              = module.network.vpc_id
  private_subnet_ids  = module.network.private_subnet_ids
  public_subnet_ids   = module.network.public_subnet_ids
  node_instance_type  = "t3.small"
  desired_node_count  = 1
  min_node_count      = 1
  max_node_count      = 2
  capacity_type       = "ON_DEMAND"
  tags                = local.common_tags
}

# ── Outputs ───────────────────────────────────────────────────
output "vpc_id" {
  value = module.network.vpc_id
}

output "app_instance_id" {
  value = module.compute.instance_id
}

output "db_endpoint" {
  value = module.database.db_endpoint
}

output "db_secret_arn" {
  description = "Pass this to the application so it can read DB credentials from Secrets Manager"
  value       = module.database.secret_arn
}

output "uploads_bucket" {
  value = module.storage.bucket_id
}

output "eks_cluster_name" {
  value = module.eks.cluster_name
}

output "eks_cluster_endpoint" {
  value = module.eks.cluster_endpoint
}

output "eks_kubeconfig_command" {
  description = "Run this command to configure kubectl"
  value       = module.eks.kubeconfig_command
}
