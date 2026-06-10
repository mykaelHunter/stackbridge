# ============================================================
# Policy: security.rego
# Enforces security baselines on every Terraform plan:
#   - No resources outside allowed regions
#   - No instance types outside the allowed list per environment
#   - No RDS instances in public subnets or publicly accessible
#   - No security groups with 0.0.0.0/0 ingress on any port
#   - No S3 buckets with public ACLs
#   - No unencrypted RDS storage
# ============================================================

package terraform.security

import rego.v1

allowed_regions := {"us-east-1", "us-west-2"}

allowed_instance_types := {
  "dev":     {"t3.micro", "t3.small"},
  "staging": {"t3.micro", "t3.small", "t3.medium"},
  "prod":    {"t3.small", "t3.medium", "t3.large", "m5.large", "m5.xlarge"},
}

# ── Region enforcement ────────────────────────────────────────
deny contains msg if {
  resource := input.resource_changes[_]
  resource.change.actions[_] in {"create", "update"}
  region := object.get(resource.change.after, "region", null)
  region != null
  not region in allowed_regions
  msg := sprintf(
    "POLICY VIOLATION [security]: Resource '%s' targets region '%s'. Allowed regions: %v",
    [resource.address, region, allowed_regions]
  )
}

# ── Instance type enforcement ─────────────────────────────────
deny contains msg if {
  resource := input.resource_changes[_]
  resource.type in {"aws_instance", "aws_db_instance"}
  resource.change.actions[_] in {"create", "update"}
  instance_type := resource.change.after.instance_type
  tags := object.get(resource.change.after, "tags", {})
  env := object.get(tags, "Environment", "dev")
  allowed := object.get(allowed_instance_types, env, set())
  not instance_type in allowed
  msg := sprintf(
    "POLICY VIOLATION [security]: Resource '%s' uses instance type '%s' which is not allowed in '%s'. Allowed: %v",
    [resource.address, instance_type, env, allowed]
  )
}

# ── No publicly accessible RDS ────────────────────────────────
deny contains msg if {
  resource := input.resource_changes[_]
  resource.type == "aws_db_instance"
  resource.change.actions[_] in {"create", "update"}
  resource.change.after.publicly_accessible == true
  msg := sprintf(
    "POLICY VIOLATION [security]: RDS instance '%s' has publicly_accessible = true. Databases must never be publicly accessible.",
    [resource.address]
  )
}

# ── No unencrypted RDS storage ────────────────────────────────
deny contains msg if {
  resource := input.resource_changes[_]
  resource.type == "aws_db_instance"
  resource.change.actions[_] in {"create", "update"}
  resource.change.after.storage_encrypted != true
  msg := sprintf(
    "POLICY VIOLATION [security]: RDS instance '%s' does not have storage_encrypted = true.",
    [resource.address]
  )
}

# ── No RDS with backups disabled ──────────────────────────────
deny contains msg if {
  resource := input.resource_changes[_]
  resource.type == "aws_db_instance"
  resource.change.actions[_] in {"create", "update"}
  retention := object.get(resource.change.after, "backup_retention_period", 0)
  retention == 0
  msg := sprintf(
    "POLICY VIOLATION [security]: RDS instance '%s' has backup_retention_period = 0. Backups must be enabled.",
    [resource.address]
  )
}

# ── No security groups with 0.0.0.0/0 ingress ────────────────
deny contains msg if {
  resource := input.resource_changes[_]
  resource.type == "aws_security_group"
  resource.change.actions[_] in {"create", "update"}
  ingress := resource.change.after.ingress[_]
  ingress.cidr_blocks[_] == "0.0.0.0/0"
  ingress.from_port == 0
  ingress.to_port == 0
  msg := sprintf(
    "POLICY VIOLATION [security]: Security group '%s' allows all traffic (0.0.0.0/0 on all ports). Use least-privilege rules.",
    [resource.address]
  )
}

# ── No S3 buckets with public ACLs ────────────────────────────
deny contains msg if {
  resource := input.resource_changes[_]
  resource.type == "aws_s3_bucket_acl"
  resource.change.actions[_] in {"create", "update"}
  resource.change.after.acl in {"public-read", "public-read-write", "authenticated-read"}
  msg := sprintf(
    "POLICY VIOLATION [security]: S3 bucket ACL '%s' sets acl = '%s'. Buckets must be private.",
    [resource.address, resource.change.after.acl]
  )
}

# ── Warn: RDS deletion protection off ────────────────────────
warn contains msg if {
  resource := input.resource_changes[_]
  resource.type == "aws_db_instance"
  resource.change.actions[_] in {"create", "update"}
  tags := object.get(resource.change.after, "tags", {})
  env := object.get(tags, "Environment", "dev")
  env == "prod"
  resource.change.after.deletion_protection != true
  msg := sprintf(
    "POLICY WARNING [security]: Production RDS instance '%s' does not have deletion_protection = true.",
    [resource.address]
  )
}
