output "cluster_name" {
  description = "EKS cluster name"
  value       = aws_eks_cluster.this.name
}

output "cluster_endpoint" {
  description = "EKS cluster API endpoint"
  value       = aws_eks_cluster.this.endpoint
}

output "cluster_certificate_authority_data" {
  description = "Base64-encoded cluster CA certificate. Needed for kubeconfig."
  value       = aws_eks_cluster.this.certificate_authority[0].data
}

output "cluster_security_group_id" {
  description = "Security group ID for the EKS control plane"
  value       = aws_security_group.cluster.id
}

output "oidc_provider_arn" {
  description = "ARN of the OIDC provider — needed for IRSA role trust policies"
  value       = aws_iam_openid_connect_provider.eks.arn
}

output "oidc_provider_url" {
  description = "OIDC issuer URL without the https:// prefix — used in IRSA trust policy conditions"
  value       = replace(aws_eks_cluster.this.identity[0].oidc[0].issuer, "https://", "")
}

output "node_group_role_arn" {
  description = "IAM role ARN used by worker nodes"
  value       = aws_iam_role.node.arn
}

output "external_secrets_role_arn" {
  description = "IAM role ARN for the external-secrets IRSA ServiceAccount — annotate the SA with eks.amazonaws.com/role-arn set to this value"
  value       = aws_iam_role.external_secrets.arn
}

output "kubeconfig_command" {
  description = "Run this to configure kubectl for this cluster"
  value       = "aws eks update-kubeconfig --name ${aws_eks_cluster.this.name} --region ${var.aws_region}"
}
