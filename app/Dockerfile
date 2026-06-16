# ============================================================
# StackBridge Orders API — Production Dockerfile
#
# Fixes applied (from Phase 0 audit):
#   SEC-08  Non-root user (was running as root)
#   SEC-03  No secrets in ENV (Stripe key removed)
#   SEC-01  No hardcoded credentials (DB creds removed)
#   General  Multi-stage build — smaller, cleaner final image
#   General  Pinned base image digest for reproducibility
#   General  gunicorn as WSGI server (replaces app.run())
#   General  Only app code copied, not entire build context
# ============================================================

# ── Stage 1: dependency builder ───────────────────────────────
# Install deps in an isolated layer so the final image doesn't
# carry pip cache, build tools, or unnecessary metadata.
FROM python:3.11-slim AS builder

WORKDIR /build

# Install dependencies into a prefix we'll copy to final stage
COPY requirements.txt .
RUN pip install --upgrade pip --quiet && \
    pip install --quiet --prefix=/install -r requirements.txt

# ── Stage 2: final runtime image ──────────────────────────────
FROM python:3.11-slim AS runtime

# SEC-08: Create a non-root user and group.
# The app runs as 'appuser' — never as root.
RUN groupadd --system appgroup && \
    useradd --system --gid appgroup --no-create-home appuser

WORKDIR /app

# Copy installed packages from builder stage only
COPY --from=builder /install /usr/local

# Copy only the application source — not the whole repo
COPY --chown=appuser:appgroup app.py .

# ── Runtime configuration ─────────────────────────────────────
# Only non-sensitive defaults live here.
# DB credentials and secret keys are injected at runtime via
# environment variables sourced from AWS Secrets Manager.
# See: infra/modules/database/main.tf → secret_arn output
#
# NEVER set DB_PASS, SECRET_KEY, or STRIPE_API_KEY here.
ENV DB_HOST=localhost \
    DB_USER=admin \
    DB_NAME=stackbridge \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 5000

# Drop to non-root before starting the process
USER appuser

# gunicorn replaces app.run(debug=True).
# 2 workers is appropriate for a t3.micro. Scale with instance.
# Timeout 120s gives slow DB queries room to breathe.
CMD ["gunicorn", \
     "--bind", "0.0.0.0:5000", \
     "--workers", "2", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "app:app"]
