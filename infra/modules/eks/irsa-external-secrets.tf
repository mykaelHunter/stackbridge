# ============================================================
# IRSA role for external-secrets
#
# Lets the external-secrets-operator pod assume an IAM role scoped
# to read-only access on the app's Secrets Manager secret, via the
# OIDC provider set up above — no static AWS keys anywhere in the
# cluster. Trust is conditioned on the exact ServiceAccount subject,
# so only that one SA (not every pod in the cluster) can assume it.
# ============================================================

data "aws_iam_policy_document" "external_secrets_trust" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.eks.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "${replace(aws_eks_cluster.this.identity[0].oidc[0].issuer, "https://", "")}:sub"
      values   = ["system:serviceaccount:${var.external_secrets_namespace}:${var.external_secrets_service_account}"]
    }

    condition {
      test     = "StringEquals"
      variable = "${replace(aws_eks_cluster.this.identity[0].oidc[0].issuer, "https://", "")}:aud"
      values   = ["sts.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "external_secrets" {
  name               = "${var.name}-${var.environment}-external-secrets"
  assume_role_policy = data.aws_iam_policy_document.external_secrets_trust.json

  tags = merge(var.tags, {
    Name        = "${var.name}-${var.environment}-external-secrets"
    Environment = var.environment
    Module      = "eks"
  })
}

# Read-only, and scoped to just the one secret this role exists for —
# not secretsmanager:* on *, which would let a compromised ESO pod
# read every other secret in the account.
data "aws_iam_policy_document" "external_secrets_secrets_access" {
  statement {
    effect = "Allow"
    actions = [
      "secretsmanager:GetSecretValue",
      "secretsmanager:DescribeSecret",
    ]
    resources = [var.db_secret_arn]
  }
}

resource "aws_iam_role_policy" "external_secrets_secrets_access" {
  name   = "${var.name}-${var.environment}-external-secrets-secrets-access"
  role   = aws_iam_role.external_secrets.id
  policy = data.aws_iam_policy_document.external_secrets_secrets_access.json
}
