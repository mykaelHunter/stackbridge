"""
Gunicorn config.

child_exit is required for prometheus_client's multiprocess mode
(see PROMETHEUS_MULTIPROC_DIR in the Dockerfile and app.py's /metrics
route). Without it, each worker's metric files under
PROMETHEUS_MULTIPROC_DIR are left behind after the worker exits —
gunicorn recycles workers periodically (crashes, --max-requests,
deploy restarts), so over the life of a long-running pod this leaks
files for workers that no longer exist. mark_process_dead() removes
that worker's files so the /metrics scrape only aggregates live
workers.
"""
from prometheus_client import multiprocess


def child_exit(server, worker):
    multiprocess.mark_process_dead(worker.pid)
