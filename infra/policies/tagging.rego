# ============================================================
# Policy: tagging.rego
# Enforces that every resource in a Terraform plan has the
# required tags before apply is permitted.
#
# Run with Conftest:
#   terraform plan -out tfplan.binary
#   terraform show -json tfplan.binary > tfplan.json
#   conftest test tfplan.json --policy infra/policies/
# ============================================================

package terraform.tagging

import rego.v1

# Tags that every resource must carry
required_tags := {"Environment", "Owner", "ManagedBy", "CostCenter", "Project"}

# Allowed environments — reject typos like "Dev" or "PROD"
allowed_environments := {"dev", "staging", "prod"}

# Allowed AWS regions — restrict blast radius
allowed_regions := {"us-east-1", "us-west-2"}

# Instance types allowed per environment
allowed_instance_types := {
  "dev":     {"t3.micro", "t3.small"},
  "staging": {"t3.micro", "t3.small", "t3.medium"},
  "prod":    {"t3.small", "t3.medium", "t3.large", "m5.large", "m5.xlarge"},
}

# ── Violations ────────────────────────────────────────────────

# Deny: resource is missing one or more required tags
deny contains msg if {
  resource := input.resource_changes[_]
  resource.change.actions[_] in {"create", "update"}
  tags := object.get(resource.change.after, "tags", {})
  missing := required_tags - {tag | tags[tag]}
  count(missing) > 0
  msg := sprintf(
    "POLICY VIOLATION [tagging]: Resource '%s' (%s) is missing required tags: %v",
    [resource.address, resource.type, missing]
  )
}

# Deny: Environment tag has an invalid value
deny contains msg if {
  resource := input.resource_changes[_]
  resource.change.actions[_] in {"create", "update"}
  tags := object.get(resource.change.after, "tags", {})
  env := tags.Environment
  not env in allowed_environments
  msg := sprintf(
    "POLICY VIOLATION [tagging]: Resource '%s' has invalid Environment tag '%s'. Allowed: %v",
    [resource.address, env, allowed_environments]
  )
}
