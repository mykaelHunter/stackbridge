# Phase 1 — Platform Foundation

## What was built

This phase builds the ground layer everything else stands on.
The audit (Phase 0) identified the problems. This phase fixes the infrastructure ones
and introduces the abstractions that prevent them from coming back.

---

## Directory Structure

```
infra/
├── modules/
│   ├── network/      VPC, public/private subnets, IGW, NAT gateway
│   ├── compute/      EC2, security groups (least-privilege)
│   ├── database/     RDS PostgreSQL, private subnet, encryption, backups, Secrets Manager
│   └── storage/      S3, public access blocked, encryption, versioning
├── environments/
│   ├── dev/          Calls modules — provisions a complete dev environment
│   └── staging/      Calls modules — provisions a complete staging environment
├── policies/
│   ├── tagging.rego  OPA: required tags, valid environment values
│   └── security.rego OPA: no public DB, no open SGs, encrypted storage, backups on
├── BACKEND.md        Remote state setup instructions
cli/
└── sb.py             Internal CLI: env create / destroy / status
catalogue/
├── schema.json       JSON Schema for service catalogue entries
└── services.yaml     3 services registered: orders-api, postgres-db, redis-cache
```

---

## How to use the CLI

Install dependencies:
```bash
pip install -r cli/requirements.txt   # none currently — stdlib only
brew install terraform
brew install conftest                 # optional, for OPA policy checks
```

Bootstrap remote state (one-time, requires AWS credentials):
```bash
# See infra/BACKEND.md for the full bootstrap commands
aws s3 mb s3://stackbridge-tf-state --region us-east-1
aws dynamodb create-table \
  --table-name stackbridge-tf-lock \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST
```

Provision environments:
```bash
# Set your AMI ID first (find latest Amazon Linux 2023):
aws ssm get-parameter \
  --name /aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64 \
  --query Parameter.Value --output text

# Create dev
python cli/sb.py env create dev

# Check status
python cli/sb.py env status dev

# Create staging
python cli/sb.py env create staging

# Destroy dev (prompts for confirmation)
python cli/sb.py env destroy dev

# Destroy without prompt
python cli/sb.py env destroy dev --force
```

---

## OPA Policy Enforcement

Every `env create` automatically runs OPA checks before applying.
The policies enforce:

| Policy | What it blocks |
|--------|---------------|
| `tagging.rego` | Resources missing Environment, Owner, ManagedBy, CostCenter, or Project tags |
| `tagging.rego` | Environment tags that aren't `dev`, `staging`, or `prod` |
| `security.rego` | RDS instances with `publicly_accessible = true` |
| `security.rego` | RDS instances with `storage_encrypted = false` |
| `security.rego` | RDS instances with `backup_retention_period = 0` |
| `security.rego` | Security groups with `0.0.0.0/0` open on all ports |
| `security.rego` | S3 buckets with public-read or public-read-write ACLs |
| `security.rego` | Instance types outside the allowed list per environment |

Run policies manually:
```bash
cd infra/environments/dev
terraform plan -out tfplan.binary
terraform show -json tfplan.binary > tfplan.json
conftest test tfplan.json --policy ../../policies/
```

---

## Audit Findings Addressed

| Finding | Resolution |
|---------|-----------|
| INF-01 Database in public subnet | Database module places RDS in private subnets only |
| INF-02 Security group allows all traffic | Compute module requires explicit ingress rules; default is deny |
| INF-03 DB backups disabled | Database module sets backup_retention_days ≥ 1; OPA blocks 0 |
| INF-04 Storage not encrypted | Database module sets storage_encrypted = true; OPA blocks false |
| INF-05 No multi-AZ | Database module exposes multi_az variable; true in prod |
| INF-06 S3 bucket public-read | Storage module blocks all public access; OPA blocks public ACLs |
| INF-07 No Terraform modules | Full module library: network, compute, database, storage |
| INF-08 Local Terraform state | Remote S3 backend with DynamoDB locking |
| INF-09 No tagging standards | OPA tagging policy; required tags enforced on every plan |
| INF-10 Staging shares prod config | Separate environment directories, separate state keys, separate VPC CIDRs |
| SEC-04 AWS keys in Terraform | Provider block uses no hardcoded credentials — IAM/OIDC only |
| SEC-05 DB password in state output | Password in Secrets Manager; no password output in database module |
| PROC-03 No service catalogue | catalogue/schema.json + catalogue/services.yaml (3 services) |

---

## Manual Steps Still Remaining (Toil Register Update)

The following steps still require manual intervention after Phase 1.
Each one is a backlog item for a later phase.

| # | Step | Phase |
|---|------|-------|
| 1 | Bootstrap S3 + DynamoDB for remote state (one-time) | Done manually once |
| 2 | Fetch current AMI ID and pass to CLI | Phase 2 — automate via SSM parameter lookup |
| 3 | Configure OIDC trust between GitHub Actions and AWS | Phase 2 |
| 4 | Rotate leaked AWS keys from infra/legacy/main.tf | Immediate — manual AWS console action |
| 5 | Rotate leaked Stripe key from app/Dockerfile | Immediate — manual Stripe dashboard action |
| 6 | Remove /internal/debug endpoint from app.py | Phase 2 — fix in app, redeploy via CI |

---

## Service Catalogue

Three services are registered in `catalogue/services.yaml`.
All three use the schema defined in `catalogue/schema.json`.

| Service | ID | Tier | Availability SLO | Latency SLO (p95) |
|---------|----|------|-----------------|-------------------|
| Orders API | orders-api | tier-1 | 99.5% | 500ms |
| PostgreSQL DB | postgres-db | tier-1 | 99.9% | 50ms |
| Redis Cache | redis-cache | tier-3 | 99.0% | 10ms |

The runbook URLs reference `docs/runbooks/` — these are Phase 3 deliverables.
