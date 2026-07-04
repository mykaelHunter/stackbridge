# StackBridge Runbook

## Purpose

This runbook captures the key operational workflows for StackBridge platform engineering.
It is intended for developers and operators working with the repository's local development stack and the Terraform/EKS deployment model.

## Local development

### Start the developer environment

```bash
cd /home/mykaelhunter/Documents/stackbridge
docker-compose up
```

Services:

- `app` on port `5000`
- `db` (PostgreSQL 13) on port `5432`
- `redis` on port `6379`
- `adminer` on port `8080`

### Reset local database

```bash
docker-compose down -v
docker-compose up
```

### Local environment notes

The local Compose stack uses development defaults and hardcoded credentials:

- `DB_USER=admin`
- `DB_PASS=admin1234`
- `SECRET_KEY=supersecretkey123`

These are only for local development. Production credentials are injected at runtime via AWS Secrets Manager.

## Environment provisioning

### Supported environments

- `dev`
- `staging`

The repository intentionally excludes `prod` from CLI provisioning.

### Create dev environment

```bash
cd /home/mykaelhunter/Documents/stackbridge/scripts
./platform-create-dev.sh
```

### Create staging environment

```bash
cd /home/mykaelhunter/Documents/stackbridge/scripts
./platform-create-staging.sh
```

### Destroy dev environment

```bash
cd /home/mykaelhunter/Documents/stackbridge/scripts
./platform-destroy-dev.sh
```

### Destroy staging environment

```bash
cd /home/mykaelhunter/Documents/stackbridge/scripts
./platform-destroy-staging.sh
```

### What the create scripts do

- create or verify the shared Terraform remote state bucket `stackbridge-tf-state`
- enable versioning and encryption on the S3 bucket
- create a Python virtual environment and install the project package
- provision the target environment via `stackbridge environment create --env <env>`
- update `kubectl` config for the EKS cluster
- scaffold the `stackbridge` service
- bootstrap ESO secrets and deploy the service

### What the destroy scripts do

- destroy the target Terraform environment via `stackbridge environment destroy --env <env>`
- delete all object versions and delete the remote Terraform state bucket

> Warning: these scripts are destructive and should only be used for disposable environments.

## Audit context

The repository includes a platform audit in `docs/AUDIT.md`.
That audit documents the initial baseline findings for security, infrastructure, database, application, operations, and process risk.
Use it to understand why the current workflows were introduced and which legacy issues are still being addressed.

## Chaos engineering

### Run chaos tests

```bash
cd /home/mykaelhunter/Documents/stackbridge/scripts
./chaos-engineering-tests.sh dev
```

This script:

- scaffolds the chaos services `az-failure`, `stress`, and `network-latency`
- runs `cpu-stress`, `az-failure`, and `network-latency` experiments against the target environment

### Supported chaos experiments

- `cpu-stress`
- `pod-kill`
- `network-latency`
- `az-failure`

### Cleanup chaos experiments

```bash
stackbridge service chaos clean <service_name> <experiment> --env dev
```

## Deploying services

### Bootstrap a service

```bash
stackbridge service scaffold <service_name>
```

### Deploy a service

```bash
stackbridge service deploy <service_name> --env dev
```

### Bootstrap secrets

```bash
stackbridge environment bootstrap-secrets stackbridge --env dev
```

## Troubleshooting

### `kubectl` fails to connect

- Verify current cluster config with `kubectl config current-context`
- Confirm environment cluster name:
  - `stackbridge-dev` for dev
  - `stackbridge-staging` for staging
- Run `kubectl get namespaces`

### Terraform errors

- Make sure `terraform` is installed and on `PATH`
- Ensure `infra/environments/<env>` exists
- Check the remote state bucket and DynamoDB lock table for conflicts

### Chaos experiment issues

- If logs do not stream, the experiment pod may already be completed
- Use `kubectl get pods -n <namespace>` and `kubectl logs <pod> -n <namespace>` for diagnosis

## Contacts and escalation

- Internal channel: `#dev`
- Historical owner: Jake (left in March)

## Important operational notes

- Do not run Terraform destroy for production from this repository.
- The local compose stack is for development and not production.
- Production secrets are managed outside source control via AWS Secrets Manager and ESO.
