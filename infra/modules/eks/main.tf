# ============================================================
# Module: eks
# Creates an EKS cluster with a single managed node group,
# sized to stay inside (or very close to) AWS Free Tier limits.
#
# Free tier reality check:
#   - EKS control plane is NOT free tier eligible.
#     As of writing it costs ~$0.10/hour (~$73/month) regardless
#     of size. There is no way around this via Terraform —
#     it's an AWS pricing model decision, not a config setting.
#   - Worker nodes (EC2) DO benefit from free tier:
#     750 hrs/month of t2.micro or t3.micro is covered.
#   - t3.micro is technically schedulable for EKS nodes but is
#     tight — kubelet, kube-proxy, and the CNI plugin alone use
#     a meaningful slice of a micro's 1GB RAM. t3.small
#     (2GB RAM) is the realistic free-tier-adjacent minimum for
#     anything beyond a "hello world" pod.
#   - This module defaults to a SINGLE t3.small node to keep
#     monthly EC2 cost near zero while keeping the cluster usable.
#
# What this module hides from the caller:
#   - OIDC provider setup (required for IRSA — pod-level IAM)
#   - Cluster + node IAM roles and policy attachments
#   - Security group wiring between control plane and nodes
#   - aws-auth / access entries for kubectl access
# ============================================================

# ── IAM: Cluster role ──────────────────────────────────────────
resource "aws_iam_role" "cluster" {
  name = "${var.name}-${var.environment}-eks-cluster"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "eks.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })

  tags = merge(var.tags, {
    Name        = "${var.name}-${var.environment}-eks-cluster-role"
    Environment = var.environment
    Module      = "eks"
  })
}

resource "aws_iam_role_policy_attachment" "cluster_policy" {
  role       = aws_iam_role.cluster.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
}

# ── IAM: Node group role ───────────────────────────────────────
resource "aws_iam_role" "node" {
  name = "${var.name}-${var.environment}-eks-node"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })

  tags = merge(var.tags, {
    Name        = "${var.name}-${var.environment}-eks-node-role"
    Environment = var.environment
    Module      = "eks"
  })
}

resource "aws_iam_role_policy_attachment" "node_worker_policy" {
  role       = aws_iam_role.node.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
}

resource "aws_iam_role_policy_attachment" "node_cni_policy" {
  role       = aws_iam_role.node.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
}

resource "aws_iam_role_policy_attachment" "node_ecr_policy" {
  role       = aws_iam_role.node.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}

# Required for SSM Session Manager access to nodes (no SSH needed)
resource "aws_iam_role_policy_attachment" "node_ssm_policy" {
  role       = aws_iam_role.node.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

# ── Security group: cluster control plane ──────────────────────
resource "aws_security_group" "cluster" {
  name        = "${var.name}-${var.environment}-eks-cluster-sg"
  description = "EKS control plane security group"
  vpc_id      = var.vpc_id

  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, {
    Name        = "${var.name}-${var.environment}-eks-cluster-sg"
    Environment = var.environment
    Module      = "eks"
  })
}

# ── Security group: worker nodes ────────────────────────────────
# EKS managed node groups need their own SG. Nodes must be able to
# reach the control plane on 443, and the control plane must be
# able to reach the kubelet on nodes (10250) for exec/logs/metrics.
resource "aws_security_group" "node" {
  name        = "${var.name}-${var.environment}-eks-node-sg"
  description = "EKS worker node security group"
  vpc_id      = var.vpc_id

  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, {
    Name                                            = "${var.name}-${var.environment}-eks-node-sg"
    Environment                                     = var.environment
    Module                                          = "eks"
    "kubernetes.io/cluster/${var.name}-${var.environment}" = "owned"
  })
}

# Node -> node-group internal traffic (pod-to-pod, kube-proxy, CNI)
resource "aws_security_group_rule" "node_self_ingress" {
  type                     = "ingress"
  from_port                = 0
  to_port                  = 65535
  protocol                 = "-1"
  security_group_id        = aws_security_group.node.id
  source_security_group_id = aws_security_group.node.id
  description              = "Allow nodes to communicate with each other"
}

# Control plane -> nodes (kubelet API: exec, logs, port-forward, metrics)
resource "aws_security_group_rule" "cluster_to_node_kubelet" {
  type                     = "ingress"
  from_port                = 1025
  to_port                  = 65535
  protocol                 = "tcp"
  security_group_id        = aws_security_group.node.id
  source_security_group_id = aws_security_group.cluster.id
  description              = "Allow control plane to reach kubelet on nodes"
}

# Control plane -> nodes (webhook/admission controller ports, common addons)
resource "aws_security_group_rule" "cluster_to_node_https" {
  type                     = "ingress"
  from_port                = 443
  to_port                  = 443
  protocol                 = "tcp"
  security_group_id        = aws_security_group.node.id
  source_security_group_id = aws_security_group.cluster.id
  description              = "Allow control plane to reach HTTPS webhooks on nodes"
}

# Nodes -> control plane (this is the rule that was missing —
# without it, nodes cannot reach the API server to register,
# which is the direct cause of "Instances failed to join the
# kubernetes cluster")
resource "aws_security_group_rule" "node_to_cluster_https" {
  type                     = "ingress"
  from_port                = 443
  to_port                  = 443
  protocol                 = "tcp"
  security_group_id        = aws_security_group.cluster.id
  source_security_group_id = aws_security_group.node.id
  description              = "Allow nodes to reach the control plane API server"
}

# ── EKS Cluster ─────────────────────────────────────────────────
resource "aws_eks_cluster" "this" {
  name     = "${var.name}-${var.environment}"
  role_arn = aws_iam_role.cluster.arn
  version  = var.kubernetes_version

  # Required for aws_eks_access_entry to work. Without this,
  # the cluster defaults to CONFIG_MAP-only auth and access
  # entries are rejected with InvalidRequestException.
  access_config {
    authentication_mode = "API_AND_CONFIG_MAP"
  }

  vpc_config {
    subnet_ids              = concat(var.private_subnet_ids, var.public_subnet_ids)
    security_group_ids      = [aws_security_group.cluster.id]
    endpoint_private_access = true
    # Public endpoint stays enabled in dev/staging so the CLI
    # and CI runners can reach the cluster without a VPN/bastion.
    # Restrict cidrs in prod via endpoint_public_access_cidrs.
    endpoint_public_access  = true
    public_access_cidrs     = var.public_access_cidrs
  }

  # Control plane logging — off by default to avoid CloudWatch
  # ingestion costs in dev/staging. Enable selectively in prod.
  enabled_cluster_log_types = var.enabled_log_types

  tags = merge(var.tags, {
    Name        = "${var.name}-${var.environment}-eks"
    Environment = var.environment
    Module      = "eks"
  })

  depends_on = [
    aws_iam_role_policy_attachment.cluster_policy
  ]
}

# ── OIDC provider (required for IRSA) ──────────────────────────
# Allows Kubernetes service accounts to assume IAM roles directly,
# instead of giving every pod the node's broad IAM permissions.
# This is what lets e.g. the AWS Load Balancer Controller or
# external-secrets operate with least-privilege.
data "tls_certificate" "eks" {
  url = aws_eks_cluster.this.identity[0].oidc[0].issuer
}

resource "aws_iam_openid_connect_provider" "eks" {
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [data.tls_certificate.eks.certificates[0].sha1_fingerprint]
  url             = aws_eks_cluster.this.identity[0].oidc[0].issuer

  tags = merge(var.tags, {
    Name        = "${var.name}-${var.environment}-eks-oidc"
    Environment = var.environment
    Module      = "eks"
  })
}

# ── Launch template ─────────────────────────────────────────────
# EKS managed node groups don't expose a security_group_ids
# argument directly — a launch template is required to attach
# the custom node security group defined above. Without this,
# nodes only get the EKS-created default SG, which (combined
# with the cluster SG having zero ingress rules) is the direct
# cause of "Instances failed to join the kubernetes cluster".
resource "aws_launch_template" "node" {
  name_prefix = "${var.name}-${var.environment}-eks-node-"

  vpc_security_group_ids = [aws_security_group.node.id]

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required" # IMDSv2 only
    http_put_response_hop_limit = 2          # EKS bootstrap needs hop 2, not 1
  }

  tag_specifications {
    resource_type = "instance"
    tags = merge(var.tags, {
      Name        = "${var.name}-${var.environment}-eks-node"
      Environment = var.environment
      Module      = "eks"
    })
  }

  tags = merge(var.tags, {
    Environment = var.environment
    Module      = "eks"
  })
}

# ── Managed Node Group ──────────────────────────────────────────
# Single node by default — see file header for free tier rationale.
resource "aws_eks_node_group" "default" {
  cluster_name    = aws_eks_cluster.this.name
  node_group_name = "${var.name}-${var.environment}-default"
  node_role_arn   = aws_iam_role.node.arn
  subnet_ids      = var.private_subnet_ids

  launch_template {
    id      = aws_launch_template.node.id
    version = aws_launch_template.node.latest_version
  }

  instance_types = [var.node_instance_type]
  ami_type       = "AL2_x86_64"
  capacity_type  = var.capacity_type # ON_DEMAND or SPOT

  scaling_config {
    desired_size = var.desired_node_count
    min_size     = var.min_node_count
    max_size     = var.max_node_count
  }

  update_config {
    max_unavailable = 1
  }

  labels = {
    Environment = var.environment
  }

  tags = merge(var.tags, {
    Name        = "${var.name}-${var.environment}-eks-node-group"
    Environment = var.environment
    Module      = "eks"
  })

  depends_on = [
    aws_iam_role_policy_attachment.node_worker_policy,
    aws_iam_role_policy_attachment.node_cni_policy,
    aws_iam_role_policy_attachment.node_ecr_policy,
    aws_security_group_rule.node_self_ingress,
    aws_security_group_rule.cluster_to_node_kubelet,
    aws_security_group_rule.cluster_to_node_https,
    aws_security_group_rule.node_to_cluster_https,
  ]

  lifecycle {
    # Node group size is often managed by cluster-autoscaler or
    # Karpenter once installed — don't fight it from Terraform.
    ignore_changes = [scaling_config[0].desired_size]
  }
}

# ── EKS access entry for the caller's IAM identity ──────────────
# Grants whoever runs `sb env create` cluster-admin via the
# modern EKS access entry API (replaces the old aws-auth ConfigMap).
data "aws_caller_identity" "current" {}

resource "aws_eks_access_entry" "admin" {
  cluster_name  = aws_eks_cluster.this.name
  principal_arn = data.aws_caller_identity.current.arn
  type          = "STANDARD"

  tags = merge(var.tags, {
    Environment = var.environment
    Module      = "eks"
  })
}

resource "aws_eks_access_policy_association" "admin" {
  cluster_name  = aws_eks_cluster.this.name
  principal_arn = data.aws_caller_identity.current.arn
  policy_arn    = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy"

  access_scope {
    type = "cluster"
  }

  depends_on = [aws_eks_access_entry.admin]
}
