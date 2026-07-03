# ============================================================
# Module: eso-manifests
#
# Renders the three ExternalSecrets Operator manifests
# (ServiceAccount, SecretStore, ExternalSecret) with real values
# baked in — role ARN, region, environment — and writes them
# straight to disk in the service's eso/ directory.
#
# This replaces the earlier approach of leaving {{ENVIRONMENT}},
# {{AWS_REGION}}, {{ESO_IRSA_ROLE_ARN}} as string placeholders in
# CLI-scaffolded YAML for some later pipeline step to substitute.
# Terraform is the only thing that knows the role ARN in the first
# place (it just created the role), so it renders the files itself.
# Nothing downstream needs to template these again — `kubectl apply
# -f eso/` works directly on Terraform's output.
#
# Trade-off: this couples the Terraform apply to the app repo's file
# layout (it writes into services/<name>/eso/ outside of infra/).
# Run `terraform apply` before `kubectl apply -f eso/`, and re-apply
# whenever the IRSA role changes (e.g. after renaming the
# ServiceAccount) so the files stay in sync.
# ============================================================

resource "local_file" "serviceaccount" {
  filename = "${var.output_dir}/serviceaccount.yaml"

  content = templatefile("${path.module}/templates/serviceaccount.yaml.tftpl", {
    service_name = var.service_name
    role_arn     = var.role_arn
  })
}

resource "local_file" "secretstore" {
  filename = "${var.output_dir}/secretstore.yaml"

  content = templatefile("${path.module}/templates/secretstore.yaml.tftpl", {
    service_name = var.service_name
    aws_region   = var.aws_region
  })
}

resource "local_file" "external_secret" {
  filename = "${var.output_dir}/external-secret.yaml"

  content = templatefile("${path.module}/templates/external-secret.yaml.tftpl", {
    service_name = var.service_name
    environment  = var.environment
  })
}
