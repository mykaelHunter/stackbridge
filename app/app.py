"""
StackBridge Internal Orders API
================================
Production-grade Flask app connecting to PostgreSQL.

DB credentials are injected at runtime from environment variables
sourced from AWS Secrets Manager (see infra/modules/database/main.tf
-> secret_arn output). No credentials should ever appear in this file
or in any Docker image layer.

SEC-01 fix: DB_PASS has NO fallback value. If the env var is missing
the application refuses to start rather than silently using a default
password (the original 'admin1234' fallback was the Phase 0 SEC-01
audit finding — hardcoded credential in source).
"""
import os
import logging
import time
from contextlib import contextmanager

import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, request, jsonify, Response
from prometheus_client import (
    Counter, Histogram, CONTENT_TYPE_LATEST,
    CollectorRegistry, multiprocess, generate_latest,
)

# ── Logging ───────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ── Metrics ───────────────────────────────────────────────────
# PROMETHEUS_MULTIPROC_DIR must be set (see Dockerfile ENV) because
# gunicorn runs multiple worker processes per pod (--workers 2).
# Without multiprocess mode, each worker keeps its own independent
# in-memory counters, and a single /metrics scrape only ever sees
# whichever one worker happened to handle that request — silently
# undercounting request totals rather than erroring, which is worse
# than a crash because it looks like real, self-consistent data.
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "path"],
)


@app.before_request
def _start_timer():
    request._metrics_start_time = time.time()


@app.after_request
def _record_metrics(response):
    # request.path (not request.url_rule) is intentional here to keep
    # the stub simple, but note this means unmatched/404 paths each
    # get their own label value — fine at this app's current size,
    # but would need to switch to request.url_rule.rule (falling back
    # to "unmatched") if routes ever take path parameters at scale,
    # to avoid unbounded cardinality in Prometheus.
    latency = time.time() - getattr(request, "_metrics_start_time", time.time())
    REQUEST_LATENCY.labels(request.method, request.path).observe(latency)
    REQUEST_COUNT.labels(request.method, request.path, response.status_code).inc()
    return response


@app.route("/metrics")
def metrics():
    registry = CollectorRegistry()
    multiprocess.MultiProcessCollector(registry)
    return Response(generate_latest(registry), mimetype=CONTENT_TYPE_LATEST)


# ── Database configuration ────────────────────────────────────
# All values injected via environment variables.
# DB_PASS has no default — the app will raise a clear error at
# startup if it is not set, rather than using a fallback password.
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = int(os.environ.get("DB_PORT", 5432))
DB_NAME = os.environ.get("DB_NAME", "stackbridge")
DB_USER = os.environ.get("DB_USER", "admin")
DB_PASS = os.environ.get("DB_PASS")

if not DB_PASS:
    raise RuntimeError(
        "DB_PASS environment variable is not set. "
        "Inject this at runtime from AWS Secrets Manager — "
        "do not add a default value here."
    )


@contextmanager
def get_db():
    """
    Context manager for database connections.

    Guarantees the connection is always closed, even if an
    exception is raised mid-route. The original pattern opened
    a connection and called conn.close() at the end of each
    route — if any code between open and close raised an exception,
    the connection leaked permanently until the process ran out
    of available connections (fixes DB-04 from the Phase 0 audit).

    Using RealDictCursor so rows are returned as dicts rather
    than tuples, which prevents accidental column-order coupling
    and makes the JSON serialisation explicit about which fields
    are returned.
    """
    conn = None
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            cursor_factory=RealDictCursor,
            connect_timeout=5,
        )
        yield conn
    except psycopg2.OperationalError as e:
        logger.error("Database connection failed: %s", e)
        raise
    finally:
        if conn is not None:
            conn.close()


# ── Health / readiness ────────────────────────────────────────

@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/ready")
def ready():
    """
    Readiness probe — verifies the DB connection is reachable.
    Kubernetes will not route traffic until this returns 200.
    """
    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT 1")
        return jsonify({"status": "ready", "db": "connected"}), 200
    except Exception:
        return jsonify({"status": "not ready", "db": "unreachable"}), 503


# ── Orders ────────────────────────────────────────────────────

@app.route("/orders", methods=["GET"])
def list_orders():
    try:
        with get_db() as conn:
            cur = conn.cursor()
            # Explicit column list — never SELECT *.
            # Avoids exposing columns added in future migrations
            # (e.g. internal_cost equivalent) without a deliberate
            # API change.
            cur.execute(
                "SELECT id, customer_id, product, quantity, status, total, created_at "
                "FROM orders ORDER BY created_at DESC"
            )
            rows = cur.fetchall()
        return jsonify([dict(r) for r in rows]), 200
    except psycopg2.Error as e:
        logger.error("list_orders failed: %s", e)
        return jsonify({"error": "Failed to retrieve orders"}), 500


@app.route("/orders", methods=["POST"])
def create_order():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    required = ["customer_id", "product", "quantity"]
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Missing required fields: {missing}"}), 400

    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO orders (customer_id, product, quantity, status) "
                "VALUES (%s, %s, %s, 'pending') RETURNING id",
                (data["customer_id"], data["product"], data["quantity"])
            )
            order_id = cur.fetchone()["id"]
            conn.commit()
        return jsonify({"id": order_id}), 201
    except psycopg2.Error as e:
        logger.error("create_order failed: %s", e)
        return jsonify({"error": "Failed to create order"}), 500


# ── Users ─────────────────────────────────────────────────────

@app.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    try:
        with get_db() as conn:
            cur = conn.cursor()
            # Explicit column list — api_key and password are
            # intentionally excluded. These must never be returned
            # via the API (SEC-07 from Phase 0 audit).
            cur.execute(
                "SELECT id, email, full_name, role, created_at "
                "FROM users WHERE id = %s",
                (user_id,)
            )
            row = cur.fetchone()
        if row:
            return jsonify(dict(row)), 200
        return jsonify({"error": "User not found"}), 404
    except psycopg2.Error as e:
        logger.error("get_user failed: %s", e)
        return jsonify({"error": "Failed to retrieve user"}), 500


# ── Entry point ───────────────────────────────────────────────
# This block is only used for local development.
# In all deployed environments, gunicorn is the process runner
# (see Dockerfile CMD). debug=False is enforced here regardless.

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
