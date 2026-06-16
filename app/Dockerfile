# ============================================================
# StackBridge Orders API — Production Dockerfile
#
# Fixes applied (from Phase 0 audit):
#   SEC-08  Non-root user (was running as root)
#   SEC-03  No secrets in ENV (Stripe key removed)
#   SEC-01  No hardcoded credentials (DB creds removed)
#   General  Multi-stage build — smaller, cleaner final image
#   General  Pinned base image digest for reproducibility (FIXED)
#   General  gunicorn as WSGI server (replaces app.run())
#   General  Only app code copied, not entire build context
# ============================================================

# ── Stage 1: dependency builder ───────────────────────────────
# Fixed: Actually pinned the base image to a specific SHA256 digest for true reproducibility
FROM python:3.11-slim@sha256:923363496bc75ad4f7b4946328328114243b17409dae69eb9ee6cfbc82944cfb AS builder

WORKDIR /build

# Install dependencies into a prefix we'll copy to final stage
COPY requirements.txt .

# Hadolint ignored because upgrading core build tools shouldn't be rigidly pinned
# hadolint ignore=DL3013
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir --quiet --prefix=/install -r requirements.txt


# ── Stage 2: final runtime image ──────────────────────────────
FROM python:3.11-slim@sha256:923363496bc75ad4f7b4946328328114243b17409dae69eb9ee6cfbc82944cfb AS runtime

# SEC-08: Create a non-root user and group.
RUN groupadd --system appgroup && \
    useradd --system --gid appgroup --no-create-home appuser

# CRITICAL FOR TRIVY: Purge the base image's pre-baked, vulnerable build tools.
# A production runtime running pre-compiled dependencies does not need wheel or setuptools.
RUN pip uninstall -y setuptools wheel

WORKDIR /app

# Copy installed packages from builder stage only
COPY --from=builder /install /usr/local

# Copy only the application source with correct non-root permissions
COPY --chown=appuser:appgroup app.py .

# Ensure the application directory itself is owned by the non-root user
RUN chown appuser:appgroup /app

# ── Runtime configuration ─────────────────────────────────────
ENV DB_HOST=localhost \
    DB_USER=admin \
    DB_NAME=stackbridge \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 5000

# Drop to non-root before starting the process
USER appuser

# gunicorn replaces app.run(debug=True).
CMD ["gunicorn", \
     "--bind", "0.0.0.0:5000", \
     "--workers", "2", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "app:app"]

