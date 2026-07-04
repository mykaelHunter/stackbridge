variable "service_name" {
  description = "Service these manifests target — must match the Deployment's envFrom secretRef/configMapRef names (e.g. {{SERVICE_NAME}}-db-secret in k8s/deployment.yaml)"
  type        = string
  default     = "stackbridge"
}

variable "environment" {
  description = "Deployment environment — used to build the Secrets Manager key (stackbridge/<environment>/db-password)"
  type        = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be one of: dev, staging, prod"
  }
}

variable "aws_region" {
  description = "AWS region the SecretStore should read Secrets Manager from"
  type        = string
}

variable "role_arn" {
  description = "IRSA role ARN for external-secrets (module.eks.external_secrets_role_arn)"
  type        = string
}

variable "output_dir" {
  description = "Directory the rendered manifests are written to, e.g. \"$${path.root}/../../../services/stackbridge/eso\". Must already exist or be creatable — Terraform's local provider creates it if missing."
  type        = string
}

variable "namespace" {
  description = "Kubernetes namespace these manifests are applied into — must match the app Deployment's namespace (get_namespace(environment) in stackbridge/core/config.py) and the external_secrets_namespace passed to the eks module's IRSA trust policy. Without this, kubectl apply falls back to the caller's default context namespace, which silently breaks the ExternalSecret -> Secret sync."
  type        = string
}
