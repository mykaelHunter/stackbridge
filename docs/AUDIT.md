# StackBridge Platform Audit
**Auditor:** Hunter (Platform Engineer, Hire #1)  
**Date:** 2026-06-08  
**Scope:** Full repository audit — all 8 source files  
**Purpose:** Phase 0 baseline — document every resource, inconsistency, and manual step before any remediation begins

---

## Executive Summary

StackBridge has no platform layer. What exists is a collection of individually authored files that grew organically over 18 months with no standards, no review process, and no single owner. The primary institutional knowledge holder (Jake) has left the company. Every critical operational dependency — credentials, server access, backup schedule, deployment process — was held in one person's head and is now partially or fully lost.

This audit identifies **34 distinct findings** across 6 categories: Security, Infrastructure, Database, Application, Operations, and Process. Every finding is assigned a severity and a backlog reference for remediation tracking.

---

## Severity Definitions

| Severity | Meaning |
|----------|---------|
| **CRITICAL** | Active security risk or data loss risk; must be remediated immediately |
| **HIGH** | Reliability or safety risk; must be resolved before any new work proceeds |
| **MEDIUM** | Operational debt; must be addressed in Phase 1–2 |
| **LOW** | Quality debt; address in Phase 3+ or alongside related work |

---

## 1. Security Findings

### SEC-01 — Hardcoded database credentials in application source code
**File:** `app/app.py` (lines 16–20)  
**Severity:** CRITICAL  
**Detail:** Production database password `admin1234` is hardcoded directly in Python source. Any developer with repo access has the production DB password. Any code leak exposes it.  
**Evidence:**
```python
DB_PASS = "admin1234"   # do not change, prod uses this
```
**Remediation:** Remove hardcoded values. Inject credentials via environment variables at runtime, sourced from a secrets manager (AWS Secrets Manager, Vault, or GitHub Actions secrets).

---

### SEC-02 — Live debug endpoint exposes database password in HTTP response
**File:** `app/app.py` (lines 77–83)  
**Severity:** CRITICAL  
**Detail:** The `/internal/debug` route returns `db_host`, `db_user`, `db_pass`, and the full `os.environ` dictionary in a JSON response. This endpoint is live in production. Any unauthenticated HTTP request to `/internal/debug` returns the production database password.  
**Evidence:**
```python
@app.route("/internal/debug", methods=["GET"])
def debug():
    return {
        "db_host": DB_HOST,
        "db_user": DB_USER,
        "db_pass": DB_PASS,
        "env": dict(os.environ)
    }
```
**Remediation:** Delete this endpoint immediately. It must not exist in any environment.

---

### SEC-03 — Stripe live API key baked into Docker image
**File:** `app/Dockerfile` (line 12)  
**Severity:** CRITICAL  
**Detail:** A Stripe live API key is set as a build-time `ENV` variable in the Dockerfile. This key is baked into every Docker image layer and is visible to anyone who can pull the image or read the Dockerfile.  
**Evidence:**
```dockerfile
ENV STRIPE_API_KEY=sk_live_abc123xyz_this_is_a_real_key_do_not_share
```
**Remediation:** Remove from Dockerfile immediately. Rotate the key at Stripe. Inject at runtime via environment variable injection, never build-time.

---

### SEC-04 — AWS access keys hardcoded in Terraform configuration
**File:** `infra/legacy/main.tf` (lines 3–6)  
**Severity:** CRITICAL  
**Detail:** AWS `access_key` and `secret_key` are hardcoded in the provider block. These are committed to the repository and are available to any person with repo read access.  
**Evidence:**
```hcl
provider "aws" {
  access_key = "AKIAIOSFODNN7EXAMPLE"
  secret_key = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
}
```
**Remediation:** Remove keys from all Terraform files. Use IAM instance profiles or OIDC-based authentication. Rotate both keys. Add `*.tfvars` and `terraform.tfstate` to `.gitignore`.

---

### SEC-05 — Terraform state stored locally with DB password in plaintext output
**File:** `infra/legacy/main.tf` (lines 93–95)  
**Severity:** CRITICAL  
**Detail:** Terraform state is stored in a local file (`main.tfstate`). The `db_password` output returns `"admin1234"` in plaintext, which is written into state. Anyone with access to the state file (shared drive, per the README) has the production DB password.  
**Evidence:**
```hcl
output "db_password" {
  value = "admin1234"
}
```
**Remediation:** Migrate to remote state with encryption (S3 + DynamoDB). Mark sensitive outputs with `sensitive = true`. Never output passwords.

---

### SEC-06 — Database passwords stored as MD5 hashes
**File:** `database/schema.sql` (line 12, seed data lines 45–48)  
**Severity:** CRITICAL  
**Detail:** User passwords are stored using MD5 hashing. MD5 is cryptographically broken; rainbow tables for common passwords are publicly available. The seed data confirms this pattern is in active use.  
**Evidence:**
```sql
-- note: passwords stored as md5, we know it's bad but migration is scary
password VARCHAR(255),  -- md5 hash
INSERT INTO users VALUES ('admin@stackbridge.io', md5('admin123'), ...)
```
**Remediation:** Migrate to `bcrypt` or `argon2`. This requires a one-time re-hashing migration — users will need to reset passwords or re-authenticate.

---

### SEC-07 — API keys stored in plaintext in the database
**File:** `database/schema.sql` (line 16, seed data lines 45–47)  
**Severity:** CRITICAL  
**Detail:** The `users` table has an `api_key` column containing plaintext internal API keys. These are stored unencrypted in the database and seeded with real-looking values (`sk_internal_abc123`, `sk_internal_xyz789`).  
**Remediation:** API keys should be stored as hashed values (SHA-256 of the token). Return the plaintext value only at creation time.

---

### SEC-08 — Application container runs as root
**File:** `app/Dockerfile`  
**Severity:** HIGH  
**Detail:** No `USER` instruction is present, so the container runs as UID 0 (root). A container escape or RCE exploit would have full host-level privileges.  
**Remediation:** Add a non-root user to the Dockerfile:
```dockerfile
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser
USER appuser
```

---

### SEC-09 — Redis exposed with no authentication
**File:** `docker-compose.yml` (line 29); `docs/incident_log.txt` (2024-03-01)  
**Severity:** HIGH  
**Detail:** Redis is started with no password. Port 6379 is bound to all interfaces. The incident log explicitly notes this as a known issue ("jake said it was internal only").  
**Remediation:** Add `--requirepass` or a `redis.conf` with `requirepass` set. Restrict port binding to `127.0.0.1` in compose.

---

### SEC-10 — Adminer (database UI) exposed publicly in compose
**File:** `docker-compose.yml` (lines 33–35)  
**Severity:** HIGH  
**Detail:** Adminer is mapped to port 8080 with no authentication layer. Anyone who can reach the host can access the database UI and attempt to log in with the known credentials.  
**Remediation:** Remove Adminer from docker-compose entirely for any environment that faces a network. Use it only in isolated local dev with explicit opt-in.

---

### SEC-11 — Python dependencies pinned to versions with known CVEs
**File:** `app/requirements.txt`  
**Severity:** HIGH  
**Detail:** All dependencies are pinned to versions from 2021. Several have published CVEs:
- `Flask==2.0.1` — multiple CVEs fixed in later versions
- `Werkzeug==2.0.1` — CVE-2023-25577 (ReDoS), fixed in 2.2.3+
- `Jinja2==2.11.3` — CVE-2020-28493 (ReDoS), fixed in 2.11.3+ (borderline), more fixes in 3.x
- `PyYAML==5.3.1` — CVE-2020-14343 (arbitrary code execution), fixed in 5.4
- `requests==2.25.1` — CVE-2023-32681 (header leakage), fixed in 2.31.0  
**Remediation:** Upgrade all dependencies to current stable versions. Add `pip-audit` or Dependabot to catch future CVEs.

---

### SEC-12 — SQL injection vulnerability in orders endpoint
**File:** `app/app.py` (lines 37–40)  
**Severity:** CRITICAL  
**Detail:** The `GET /orders/<id>` route constructs SQL via string concatenation rather than parameterized queries. The comment in the code acknowledges parameterized queries were tried and abandoned.  
**Evidence:**
```python
# was getting errors with parameterized queries, this works
query = "SELECT * FROM orders WHERE id = " + str(order_id)
```
**Remediation:** Replace with parameterized query: `cur.execute("SELECT * FROM orders WHERE id = %s", (order_id,))`. The "errors" with parameterized queries were almost certainly a syntax issue that should have been debugged, not bypassed.

---

### SEC-13 — `internal_cost` column risk of data exposure via API
**File:** `database/schema.sql` (line 25); `app/app.py`  
**Severity:** MEDIUM  
**Detail:** The `products` table includes an `internal_cost` column marked `DO NOT EXPOSE IN API`. The `/orders` endpoint uses `SELECT *`, which would return all columns including this field if products were joined.  
**Remediation:** Never use `SELECT *` in API queries. Explicitly list columns. Consider a separate read model or view that excludes sensitive columns.

---

## 2. Infrastructure Findings

### INF-01 — Database placed in a public subnet
**File:** `infra/legacy/main.tf` (line 74)  
**Severity:** CRITICAL  
**Detail:** The RDS instance is placed in a public subnet with `publicly_accessible = true`. The production database is directly reachable from the internet.  
**Remediation:** Move database to a private subnet. Set `publicly_accessible = false`. Access only via application subnet or VPN/bastion.

---

### INF-02 — Security group allows all traffic from 0.0.0.0/0
**File:** `infra/legacy/main.tf` (lines 52–63)  
**Severity:** CRITICAL  
**Detail:** The application security group permits all inbound and outbound traffic from any IP on any port. Every port on every instance is publicly reachable.  
**Remediation:** Replace with least-privilege rules: allow 443/80 inbound from internet, allow application port from load balancer only, allow DB port only from application security group.

---

### INF-03 — Database backups disabled
**File:** `infra/legacy/main.tf` (line 80)  
**Severity:** CRITICAL  
**Detail:** `backup_retention_period = 0` disables automated RDS backups entirely. Combined with `skip_final_snapshot = true` and `deletion_protection = false`, the database can be deleted with no recovery path.  
**Evidence (confirmed by incident log):** 2024-03-28 — 3 weeks of order data lost because Jake's manual backups had stopped.  
**Remediation:** Set `backup_retention_period = 7` (minimum). Enable `deletion_protection = true`. Configure point-in-time recovery.

---

### INF-04 — Storage not encrypted at rest
**File:** `infra/legacy/main.tf` (line 82)  
**Severity:** HIGH  
**Detail:** `storage_encrypted = false` on the RDS instance. All data at rest is unencrypted.  
**Remediation:** Enable `storage_encrypted = true`. For existing instances, this requires a snapshot + restore cycle.

---

### INF-05 — No multi-AZ deployment
**File:** `infra/legacy/main.tf` (line 83)  
**Severity:** HIGH  
**Detail:** `multi_az = false`. Single-AZ RDS means any AZ failure or instance maintenance causes downtime.  
**Remediation:** Enable `multi_az = true` for production.

---

### INF-06 — S3 bucket is publicly readable
**File:** `infra/legacy/main.tf` (lines 87–91)  
**Severity:** HIGH  
**Detail:** The uploads S3 bucket has `acl = "public-read"`. All uploaded files are publicly accessible to anyone with the URL.  
**Remediation:** Remove the public ACL. Use pre-signed URLs for time-limited access to specific objects.

---

### INF-07 — No Terraform modules; all resources in one flat file
**File:** `infra/legacy/main.tf`  
**Severity:** MEDIUM  
**Detail:** All infrastructure is defined inline in a single file with no modules, no separation of concerns, and no reuse. Provisioning dev, staging, and prod requires copy-pasting and manual editing.  
**Remediation:** Phase 1 deliverable — design and build a module library (network, compute, database, storage).

---

### INF-08 — Terraform state stored locally; location depends on Jake
**File:** `README.md` ("ask jake for the state file")  
**Severity:** HIGH  
**Detail:** State is stored in `main.tfstate` in the repo folder. The README acknowledges "ask Jake" as the recovery procedure. Jake has left.  
**Remediation:** Migrate to S3 remote state with DynamoDB locking immediately.

---

### INF-09 — No resource tagging standards
**File:** `infra/legacy/main.tf`  
**Severity:** MEDIUM  
**Detail:** Only the `Name` tag is present on some resources. No `Environment`, `Owner`, `CostCenter`, or `Project` tags exist. Cost allocation and resource ownership are invisible.  
**Remediation:** Define a mandatory tagging schema. Enforce via OPA policy in Phase 1.

---

### INF-10 — Staging and production share identical configuration
**File:** `infra/legacy/main.tf` (staging server definition); `docs/incident_log.txt` (2024-02-19)  
**Severity:** HIGH  
**Detail:** Staging server is a copy of the production EC2 instance in the same subnet. The incident log confirms staging and prod shared the same database at one point, causing accidental data deletion.  
**Remediation:** Enforce environment isolation at the infrastructure level. Separate state per environment.

---

## 3. Database Findings

### DB-01 — No migration history; schema applied manually
**File:** `database/schema.sql` header comment  
**Severity:** HIGH  
**Detail:** The schema file begins with `DROP TABLE IF EXISTS ... CASCADE` and a note saying "do not run on prod." There is no versioned migration history. Schema changes are run directly against production (confirmed: April 2024 incident).  
**Remediation:** Phase 3 deliverable — implement Flyway or Liquibase. All schema changes version-controlled from this point forward.

---

### DB-02 — Schema resets drop all data
**File:** `database/schema.sql` (lines 4–8)  
**Severity:** HIGH  
**Detail:** The schema file drops all tables with CASCADE before recreating them. Running this file against any live database destroys all data. It has been run against production accidentally twice (incident log: 2024-02-19, 2024-03-28).  
**Remediation:** Remove destructive statements from the canonical schema file. Replace with additive migration scripts only.

---

### DB-03 — Seed data has been applied to production
**File:** `database/schema.sql` seed section; `docs/incident_log.txt` (2024-02-19)  
**Severity:** HIGH  
**Detail:** Seed data (including fake users and test orders) has been run against production at least twice. Seed data should never be applied to a production database.  
**Remediation:** Separate seed scripts into a clearly named `seeds/` directory. Gate their execution on environment checks.

---

### DB-04 — No connection pooling
**File:** `app/app.py` — `get_db()` function  
**Severity:** MEDIUM  
**Detail:** Every request opens a new database connection and closes it on completion. Under load, this exhausts the PostgreSQL connection limit. The incident log notes the app "leaks memory" — this pattern is a likely contributing factor.  
**Remediation:** Phase 3 deliverable — implement PgBouncer.

---

### DB-05 — No backup procedure after Jake left
**File:** `docs/incident_log.txt` (2024-03-28)  
**Severity:** CRITICAL  
**Detail:** Backups were entirely manual ("jake takes a manual dump every friday"). Jake left in March 2024. The 2024-03-28 incident confirms 3 weeks of production data was lost. As of the last incident log entry, there is no backup procedure.  
**Remediation:** Phase 3 deliverable — automated daily backups with verified restore drill.

---

### DB-06 — Marketing team has direct production database access
**File:** `docs/incident_log.txt` (2024-04-15)  
**Severity:** HIGH  
**Detail:** The marketing team was granted direct read access to the production database to run analytics queries. Ad-hoc queries against production create performance risk and schema coupling.  
**Remediation:** Create a read replica for analytics. Grant read-only access to the replica, never production primary.

---

## 4. Application Findings

### APP-01 — Flask debug mode enabled in production
**File:** `app/app.py` (line 88)  
**Severity:** HIGH  
**Detail:** `app.run(debug=True)` is set with the comment "we need the reloader." Debug mode in production enables the interactive Werkzeug debugger, which allows arbitrary Python code execution via the browser if an exception occurs.  
**Remediation:** Set `debug=False`. Use `gunicorn` or `uvicorn` as the production WSGI server, not `app.run()`.

---

### APP-02 — No database connection pooling; new connection per request
**File:** `app/app.py` — `get_db()`  
**Severity:** MEDIUM  
**Detail:** Covered in DB-04. Also: connections are not closed if an exception occurs before `conn.close()`, leading to connection leaks.  
**Remediation:** Use a connection pool (via `psycopg2.pool` or PgBouncer). Use context managers to ensure connections are always released.

---

### APP-03 — No input validation on POST /orders
**File:** `app/app.py` (lines 55–63)  
**Severity:** MEDIUM  
**Detail:** `create_order()` accesses `data["customer_id"]`, `data["product"]`, and `data["quantity"]` directly with no validation. Missing keys cause an unhandled `KeyError`; unexpected types cause downstream failures.  
**Remediation:** Add request schema validation (e.g. `marshmallow` or `pydantic`). Return 400 on invalid input.

---

### APP-04 — No error handling; exceptions surface as 500s
**File:** `app/app.py`  
**Severity:** MEDIUM  
**Detail:** No try/except blocks exist anywhere in the application. Any database error, missing key, or unexpected input produces an unhandled exception and a 500 response. In debug mode, this also renders the Werkzeug debugger.  
**Remediation:** Add error handlers. Log exceptions with context. Return structured error responses.

---

## 5. Operations & Deployment Findings

### OPS-01 — Deployment is a manual bash script run from a developer's laptop
**File:** `deploy.sh`  
**Severity:** HIGH  
**Detail:** Production deployment requires a developer to run a shell script from their local machine, using a PEM file stored in `~/.ssh/`. There is no CI/CD pipeline, no deployment record, and no approval process. The script's own comment says "if it is broken, SSH in and check app.log."  
**Remediation:** Phase 2 deliverable — replace with a CI/CD pipeline (GitHub Actions). No human should be SSHing into production to deploy.

---

### OPS-02 — No rollback mechanism
**File:** `deploy.sh` (final comment: "SSH in and run the previous version manually")  
**Severity:** HIGH  
**Detail:** Rollback is an entirely manual, undocumented process requiring SSH access and knowledge of what the previous version was.  
**Remediation:** Phase 2 deliverable — implement canary deployments with automated rollback.

---

### OPS-03 — Container restart policy disabled
**File:** `docker-compose.yml` (line 21, commented out)  
**Severity:** MEDIUM  
**Detail:** `restart: always` is commented out "because it hid crashes." This means the app does not automatically restart after a crash. A workaround cron job restarts the process nightly (incident log: 2024-03-14).  
**Remediation:** Fix the memory leak (APP-02, APP-04). Re-enable restart policy. Remove the cron workaround.

---

### OPS-04 — No health check on the database container
**File:** `docker-compose.yml` (line 16: "no health check, it usually just works")  
**Severity:** LOW  
**Detail:** The `app` service starts immediately after `db` starts, but PostgreSQL may not be ready to accept connections at that point. This causes startup race conditions.  
**Remediation:** Add a `healthcheck` to the `db` service and use `depends_on: condition: service_healthy` in the app service.

---

### OPS-05 — No monitoring, alerting, or observability
**File:** `docs/incident_log.txt` ("no monitoring except 'check if the site loads'")  
**Severity:** HIGH  
**Detail:** There is no Prometheus, no Grafana, no uptime monitoring, no alerting. Incidents are discovered by users or by someone checking manually. Every incident in the log was discovered reactively.  
**Remediation:** Phase 3 deliverable — deploy Prometheus + Grafana. Define SLOs. Set up alerting.

---

### OPS-06 — No runbook; no on-call process
**File:** `README.md` ("if something breaks, message #dev channel, jake usually responds")  
**Severity:** HIGH  
**Detail:** Jake is no longer here. There is no documented recovery procedure for any failure scenario. The entire on-call process was one person's phone number.  
**Remediation:** Phase 3 deliverable — write operational runbooks. Define on-call rotation and escalation path.

---

### OPS-07 — Server IP is unstable and undocumented
**File:** `deploy.sh` (line 5: "update this if it changes (it changes)"); `README.md` ("Server IP: ask jake (it changes sometimes)")  
**Severity:** MEDIUM  
**Detail:** The production server IP changes, is hardcoded in the deploy script, and its current value is unknown ("ask jake"). Using an Elastic IP or DNS-based reference would eliminate this entirely.  
**Remediation:** Assign an Elastic IP or use Route 53 DNS. Never hardcode IPs in scripts.

---

## 6. Process Findings

### PROC-01 — All institutional knowledge was a single person
**File:** `README.md`, `docs/incident_log.txt`  
**Severity:** HIGH  
**Detail:** Jake was the single point of failure for: server access, database password, backup schedule, Terraform state, server IP, and on-call response. He left in March 2024. The fallout is still ongoing.  
**Remediation:** Platform work must be documented as it is built. No process should require asking a specific person.

---

### PROC-02 — No CI/CD; no branch protection; direct pushes to main
**File:** `docs/incident_log.txt` (2024-02-03: "someone pushed directly to main")  
**Severity:** HIGH  
**Detail:** A syntax error deployed directly to production because there is no pipeline to catch it and no branch protection to prevent direct pushes.  
**Remediation:** Enable branch protection on `main`. Require PR + CI pass before merge. Set up GitHub Actions pipeline.

---

### PROC-03 — No service catalogue; no ownership registry
**File:** All files  
**Severity:** MEDIUM  
**Detail:** There is no documented list of services, their owners, SLO targets, health endpoints, or runbooks. The README is the only documentation and it references Jake for most answers.  
**Remediation:** Phase 1 deliverable — build a service catalogue with schema: `name`, `owner`, `SLO target`, `runbook link`, `health endpoint`.

---

## Summary Table

| ID | Category | Severity | File | One-line Summary |
|----|----------|----------|------|-----------------|
| SEC-01 | Security | CRITICAL | app/app.py | Hardcoded DB password in source |
| SEC-02 | Security | CRITICAL | app/app.py | Debug endpoint returns DB password |
| SEC-03 | Security | CRITICAL | app/Dockerfile | Stripe live key in Docker image |
| SEC-04 | Security | CRITICAL | infra/legacy/main.tf | AWS keys in Terraform |
| SEC-05 | Security | CRITICAL | infra/legacy/main.tf | DB password in Terraform state output |
| SEC-06 | Security | CRITICAL | database/schema.sql | Passwords hashed with MD5 |
| SEC-07 | Security | CRITICAL | database/schema.sql | API keys in plaintext in DB |
| SEC-08 | Security | HIGH | app/Dockerfile | Container runs as root |
| SEC-09 | Security | HIGH | docker-compose.yml | Redis has no password |
| SEC-10 | Security | HIGH | docker-compose.yml | Adminer exposed publicly |
| SEC-11 | Security | HIGH | app/requirements.txt | Dependencies with known CVEs |
| SEC-12 | Security | CRITICAL | app/app.py | SQL injection in /orders/<id> |
| SEC-13 | Security | MEDIUM | database/schema.sql | internal_cost leak risk via SELECT * |
| INF-01 | Infrastructure | CRITICAL | infra/legacy/main.tf | Database in public subnet |
| INF-02 | Infrastructure | CRITICAL | infra/legacy/main.tf | Security group allows all traffic |
| INF-03 | Infrastructure | CRITICAL | infra/legacy/main.tf | DB backups disabled |
| INF-04 | Infrastructure | HIGH | infra/legacy/main.tf | Storage not encrypted |
| INF-05 | Infrastructure | HIGH | infra/legacy/main.tf | No multi-AZ |
| INF-06 | Infrastructure | HIGH | infra/legacy/main.tf | S3 bucket is public-read |
| INF-07 | Infrastructure | MEDIUM | infra/legacy/main.tf | No Terraform modules |
| INF-08 | Infrastructure | HIGH | README.md | Terraform state stored locally |
| INF-09 | Infrastructure | MEDIUM | infra/legacy/main.tf | No resource tagging |
| INF-10 | Infrastructure | HIGH | infra/legacy/main.tf | Staging shares prod configuration |
| DB-01 | Database | HIGH | database/schema.sql | No migration history |
| DB-02 | Database | HIGH | database/schema.sql | Schema resets destroy data |
| DB-03 | Database | HIGH | database/schema.sql | Seed data applied to production |
| DB-04 | Database | MEDIUM | app/app.py | No connection pooling |
| DB-05 | Database | CRITICAL | incident_log.txt | No backup procedure |
| DB-06 | Database | HIGH | incident_log.txt | Marketing has direct prod DB access |
| APP-01 | Application | HIGH | app/app.py | Flask debug mode in production |
| APP-02 | Application | MEDIUM | app/app.py | Connection leak risk |
| APP-03 | Application | MEDIUM | app/app.py | No input validation |
| APP-04 | Application | MEDIUM | app/app.py | No error handling |
| OPS-01 | Operations | HIGH | deploy.sh | Manual laptop-based deployment |
| OPS-02 | Operations | HIGH | deploy.sh | No rollback mechanism |
| OPS-03 | Operations | MEDIUM | docker-compose.yml | Restart policy disabled |
| OPS-04 | Operations | LOW | docker-compose.yml | No DB container health check |
| OPS-05 | Operations | HIGH | — | No monitoring or alerting |
| OPS-06 | Operations | HIGH | README.md | No runbook or on-call process |
| OPS-07 | Operations | MEDIUM | deploy.sh | Unstable hardcoded server IP |
| PROC-01 | Process | HIGH | README.md | All knowledge was one person |
| PROC-02 | Process | HIGH | incident_log.txt | No CI/CD, direct pushes to main |
| PROC-03 | Process | MEDIUM | — | No service catalogue |

---

## Remediation Priority Order

### Immediate (before any other work)
These must be addressed before Phase 1 begins. They are active security risks.

1. **SEC-02** — Take `/internal/debug` offline now. It is returning the production DB password to unauthenticated HTTP requests.
2. **SEC-03** — Rotate the Stripe API key. Remove it from the Dockerfile and all image layers.
3. **SEC-04** — Rotate the AWS keys. Remove from Terraform. Switch to IAM roles or OIDC.
4. **SEC-01 / SEC-12** — Audit whether the debug endpoint or SQL injection has been exploited. Treat as an active incident until confirmed otherwise.

### Phase 1 Backlog (Infrastructure Foundation)
INF-01, INF-02, INF-03, INF-04, INF-05, INF-06, INF-07, INF-08, INF-09, INF-10, SEC-04, SEC-05

### Phase 2 Backlog (Release Engineering)
OPS-01, OPS-02, OPS-03, PROC-02

### Phase 3 Backlog (Database & SRE)
DB-01, DB-02, DB-03, DB-04, DB-05, DB-06, SEC-06, SEC-07, OPS-05, OPS-06

### Phase 4 Backlog (Hardening)
APP-01, APP-02, APP-03, APP-04, SEC-08, SEC-09, SEC-10, SEC-11, SEC-13, OPS-04, OPS-07, PROC-01, PROC-03

---

## Manual Steps Still in Use (Toil Register)

The following manual steps exist in the current operational process. Every one is a future automation target.

| # | Manual Step | Risk | Owner |
|---|-------------|------|-------|
| T-01 | Deploy to prod by running deploy.sh from a laptop | Inconsistent, no audit trail, requires PEM file | OPS-01 |
| T-02 | Database backups run manually by Jake (now nobody) | Active data loss risk — already materialized | DB-05 |
| T-03 | Schema changes run directly against production via psql | Caused 8-minute outage in April 2024 | DB-01 |
| T-04 | Provision new environments by copy-pasting Terraform | Error-prone, slow, no standards | INF-07 |
| T-05 | Rollback by SSHing in and running previous version manually | Slow, undocumented, requires access | OPS-02 |
| T-06 | Incident discovery by users or checking if the site loads | Zero alerting coverage | OPS-05 |
| T-07 | Get server IP by asking Jake (Jake is gone) | Deployment currently blocked | OPS-07 |
| T-08 | Marketing analytics run against production database | Performance and security risk | DB-06 |

---

*End of audit. This document is the starting backlog for all platform work at StackBridge.*
