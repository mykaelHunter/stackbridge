# ============================================================
# Environment: staging
# Closer to prod than dev: NAT gateway on, larger instances,
# longer backup retention. Still no multi-AZ (cost).
# Staging and prod NEVER share a database — fixed from audit.
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
    key          = "environments/staging/terraform.tfstate"
    region       = "us-east-1"
    use_lockfile = true   # native S3 locking (replaces deprecated dynamodb_table)
    encrypt      = true
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = local.common_tags
  }
}

locals {
  environment = "staging"
  name        = "stackbridge"

  common_tags = {
    Environment = local.environment
    Project     = local.name
    Owner       = var.owner
    ManagedBy   = "terraform"
    CostCenter  = var.cost_center
  }
}

module "network" {
  source = "../../modules/network"

  name                = local.name
  environment         = local.environment
  vpc_cidr            = "10.2.0.0/16"
  availability_zones  = ["us-east-1a", "us-east-1b"]
  nat_gateway_enabled = true
  tags                = local.common_tags
}

module "compute" {
  source = "../../modules/compute"

  name          = local.name
  environment   = local.environment
  vpc_id        = module.network.vpc_id
  subnet_id     = module.network.private_subnet_ids[0]
  ami_id        = var.ami_id
  instance_type = "t3.small"
  tags          = local.common_tags

  ingress_rules = [
    {
      description = "HTTP from within VPC only"
      from_port   = 5000
      to_port     = 5000
      protocol    = "tcp"
      cidr_blocks = [module.network.vpc_cidr]
    }
  ]
}

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
  deletion_protection   = true
  tags                  = local.common_tags
}

module "storage" {
  source = "../../modules/storage"

  name        = local.name
  environment = local.environment
  purpose     = "uploads"
  tags        = local.common_tags
}

# ── EKS ───────────────────────────────────────────────────────
# Same free-tier-adjacent sizing as dev. Staging gets 2 nodes by
# default since canary/rollout testing (Argo Rollouts) needs at
# least 2 schedulable nodes to demonstrate a real rolling update.
module "eks" {
  source = "../../modules/eks"

  name                = local.name
  environment         = local.environment
  aws_region          = var.aws_region
  vpc_id              = module.network.vpc_id
  private_subnet_ids  = module.network.private_subnet_ids
  public_subnet_ids   = module.network.public_subnet_ids
  # Nodes stay in private subnets here because nat_gateway_enabled
  # is true for staging — there's a route to the internet via NAT,
  # so nodes don't need public IPs to bootstrap or pull images.
  # This is the recommended placement; dev only deviates from it
  # because NAT is disabled there for cost.
  node_subnet_ids     = module.network.private_subnet_ids
  node_instance_type  = "t3.small"
  desired_node_count  = 2
  min_node_count      = 1
  max_node_count      = 3
  capacity_type       = "ON_DEMAND"
  tags                = local.common_tags
}

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
  value = module.database.secret_arn
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
