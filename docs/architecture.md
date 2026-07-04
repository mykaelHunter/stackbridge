# StackBridge Architecture

## Purpose

This document describes the StackBridge platform architecture, including the local development stack, deployed environment flow, and the main repository components.

## Architecture overview

StackBridge is built as a platform for internal orders and user services. It has two primary execution modes:

- Local development using `docker-compose`
- Environment provisioning and deployment using Terraform, EKS, and the StackBridge CLI

The project also includes chaos engineering support and a platform audit that documents the system's initial risk profile.

## Key components

### app/

- Flask application source code for the orders and users API
- Uses `psycopg2` to connect to PostgreSQL
- Health endpoints:
  - `/health`
  - `/ready`
- Production container built with a non-root runtime and gunicorn process manager
- Runtime secrets are injected via environment variables; `DB_PASS` must be set or the app fails to start

### database/

- `schema.sql` defines the local PostgreSQL schema
- Used by the local Compose `db` service for initialization

### docker-compose.yml

Local developer stack:

- `db` — PostgreSQL 13
- `app` — Flask service built from `app/Dockerfile`
- `redis` — Redis cache
- `adminer` — database UI for debugging

This stack is for local development only and does not represent deployed production infrastructure.

### infra/

Terraform infrastructure for provisioning platform environments.

- `infra/modules/` — reusable modules for network, compute, database, storage, EKS, and ESO manifests
- `infra/environments/` — per-environment provisioned stacks for `dev` and `staging`
- `infra/policies/` — OPA rules to enforce security, encryption, and tagging standards
- `infra/BACKEND.md` — remote state bootstrap guidance

### stackbridge/ CLI

- Provides the `stackbridge` command-line interface
- Main entrypoint: `stackbridge.cli:cli`
- CLI groups:
  - `environment` — create, destroy, status, bootstrap-secrets
  - `service` — scaffold, bootstrap, deploy, chaos, delete
  - `catalog` — service catalog management
  - `notify` — notifications and alert hooks

### scripts/

Operational helper scripts for the repository:

- `platform-create-dev.sh`
- `platform-create-staging.sh`
- `platform-destroy-dev.sh`
- `platform-destroy-staging.sh`
- `chaos-engineering-tests.sh`

These scripts automate environment bootstrap, teardown, and chaos experiment execution.

## Deployment flow

### Environment provisioning

1. Bootstrap remote state bucket and DynamoDB lock table (shared state for all environments)
2. Run `stackbridge environment create --env <dev|staging>`
   - Terraform init
   - Terraform plan
   - Policy check via `conftest` against `infra/policies/`
   - Terraform apply
3. Update Kubernetes context with `aws eks update-kubeconfig`
4. Install the External Secrets Operator if needed
5. Apply Terraform-generated `eso/` manifests for service secrets
6. Deploy the service with `stackbridge service deploy <service_name> --env <env>`

### Service scaffolding and deployment

- `stackbridge service scaffold <service_name>` generates manifests and service structure from templates
- The `stackbridge` service uses the actual source files in the root `app/` directory for parity with the production app
- Each scaffolded service includes a `chaos/` directory with predefined chaos experiment manifests
- `stackbridge service deploy` installs or updates the service in the target environment namespace

## Chaos engineering

- Supported experiments: `cpu-stress`, `pod-kill`, `network-latency`, `az-failure`
- Chaos manifests are rendered with a placeholder namespace and then applied to the target environment at runtime
- The CLI supports `stackbridge service chaos run` and `stackbridge service chaos clean`

## Security and policy guardrails

- The project uses environment variables for deployed secret injection
- `DB_PASS` is intentionally required at runtime with no fallback default in `app/app.py`
- OPA policies enforce:
  - encrypted storage
  - no public RDS
  - required resource tagging
  - no open security group exposure
  - backup retention for databases
- The root README and `docs/AUDIT.md` document the repository's initial security and operational risk profile

## Audit context

- `docs/AUDIT.md` is the Phase 0 audit of the repository
- It documents critical findings such as hardcoded credentials, exposed debug endpoints, local Terraform state, and insecure infrastructure
- The active architecture reflects remediation work to move infrastructure into modules, migrate state to remote storage, and add OPA policy enforcement

## Operational boundaries

- `dev` and `staging` are the supported CLI-managed environments
- `prod` is intentionally not provisioned or destroyed by the local CLI
- The `infra/legacy/` directory contains older Terraform material and should not be used for the active platform workflow
- The shared state bucket is `stackbridge-tf-state`

## Useful paths

- `README.md` — project overview and local development quick start
- `docs/AUDIT.md` — audit findings and project risk summary
- `docs/runbook.md` — operational runbook for platform workflows
- `docs/architecture.md` — this architecture reference
- `scripts/` — bootstrap and chaos automation scripts
- `infra/environments/` — active Terraform deployment directories
- `stackbridge/` — CLI and core implementation
