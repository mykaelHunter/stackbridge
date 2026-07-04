# StackBridge

Internal platform for orders and users.

## Overview

This repository contains:

- `app/` — production Flask application source and Dockerfile
- `database/` — local PostgreSQL schema used by development compose
- `infra/` — Terraform modules, environment configs, and policy checks
- `stackbridge/` — Python CLI and platform engine
- `scripts/` — operational helper scripts for environment creation, teardown, and chaos testing
- `docs/` — project documentation, including runbook and architecture guides

## Local development

Start the local developer environment:

```bash
docker-compose up
```

- app: `http://localhost:5000`
- db: PostgreSQL on `localhost:5432`
- redis: `localhost:6379`
- adminer: `http://localhost:8080`

Reset the local database:

```bash
docker-compose down -v
docker-compose up
```

The local compose stack is for development and validation only.

## Infrastructure

The current infrastructure is defined under `infra/`.
The project includes:

- `infra/modules/` — reusable Terraform modules for network, compute, database, storage, EKS, and ESO manifests
- `infra/environments/` — per-environment Terraform configuration for `dev` and `staging`
- `infra/policies/` — OPA security and tagging policies

> Note: `infra/legacy/` exists as older Terraform material, but the active environment provisioning workflow is under `infra/environments/`.

## Scripts

The `scripts/` directory contains helper scripts for common platform workflows:

- `platform-create-dev.sh`
- `platform-create-staging.sh`
- `platform-destroy-dev.sh`
- `platform-destroy-staging.sh`
- `chaos-engineering-tests.sh`

Use these scripts to bootstrap and tear down temporary dev/staging environments and to exercise built-in chaos scenarios.

## CLI

Install the repository locally and use the `stackbridge` CLI:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .
```

Primary commands:

- `stackbridge environment create --env dev`
- `stackbridge environment create --env staging`
- `stackbridge environment destroy --env dev --force`
- `stackbridge environment destroy --env staging --force`
- `stackbridge environment status --env dev`
- `stackbridge environment bootstrap-secrets stackbridge --env dev`
- `stackbridge service scaffold <service_name>`
- `stackbridge service deploy <service_name> --env dev`
- `stackbridge service chaos run <service_name> <experiment> --env dev`

## Documentation

The detailed operational docs are located in `docs/`:

- `docs/AUDIT.md` — initial platform audit and findings summary
- `docs/runbook.md` — operational runbook for platform workflows
- `docs/architecture.md` — system architecture and design overview

## Known issues and warnings

- Do not run Terraform destroy against production from this repo.
- The local `docker-compose.yml` stack uses hardcoded local credentials and is not suitable for production.
- The repository uses AWS Secrets Manager / External Secrets Operator for deployed secret management.
- Production deployment workflows are intentionally separated from local environment provisioning.
