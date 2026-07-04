"""
stackbridge.core.chaos
=======================
Applies, follows, and tears down the chaos experiment manifests that
`stackbridge service scaffold` renders into services/<name>/chaos/.

The manifests themselves are self-contained: each is a single Pod
that runs its own experiment logic (kill pods, stress CPU, inject
latency, cordon a node) and exits on its own. This module just
drives kubectl against them — apply, optionally follow logs, delete.

The manifests are rendered with a {{NAMESPACE}} placeholder still
in place (scaffold.py deliberately does not substitute it). That's
because a chaos experiment should be able to target whichever
environment's namespace is passed with --env (dev/staging/prod),
the same way `stackbridge service deploy --env` does — so the real
namespace is substituted here, at apply/delete time, via
stackbridge.core.config.get_namespace(), not baked into the file
once at scaffold time.
"""

import subprocess
from pathlib import Path

from stackbridge.core.paths import REPO_ROOT
from stackbridge.core.config import get_namespace
from stackbridge.core.kubernetes import (
    check_cluster,
    ensure_namespace,
    ensure_chaos_rbac,
    ensure_argo_rollouts_installed,
    KubernetesError,
)
from stackbridge.core.logger import get_logger

logger = get_logger()

# Must match the filenames scaffold.py renders into chaos/ (see
# stackbridge/commands/scaffold.py's `files` mapping) and the
# metadata.name pattern "{{SERVICE_NAME}}-<experiment>" baked into
# each template.
EXPERIMENTS = [
    "pod-kill",
    "cpu-stress",
    "network-latency",
    "az-failure",
]

DEFAULT_ENVIRONMENT = "dev"


class ChaosError(Exception):
    pass


def _chaos_dir(service_name):
    return REPO_ROOT / "services" / service_name / "chaos"


def _manifest_path(service_name, experiment):
    if experiment not in EXPERIMENTS:
        raise ChaosError(
            f"Unknown experiment '{experiment}'. "
            f"Valid experiments: {', '.join(EXPERIMENTS)}"
        )

    path = _chaos_dir(service_name) / f"{experiment}.yaml"

    if not path.exists():
        raise ChaosError(
            f"No chaos manifest found at {path}. "
            f"Run `stackbridge service scaffold {service_name}` first."
        )

    return path


def _rendered_manifest(service_name, experiment, namespace):
    """Read the manifest and substitute {{NAMESPACE}} for the
    resolved namespace of the target environment."""
    manifest = _manifest_path(service_name, experiment)
    return manifest.read_text().replace("{{NAMESPACE}}", namespace)


def list_experiments(service_name):
    """Experiment ids that have a rendered manifest for this service."""
    chaos_dir = _chaos_dir(service_name)

    if not chaos_dir.exists():
        return []

    return sorted(
        p.stem for p in chaos_dir.glob("*.yaml") if p.stem in EXPERIMENTS
    )


def run_experiment(service_name, experiment, follow=True, environment=DEFAULT_ENVIRONMENT):
    """
    Apply a chaos experiment manifest to the cluster, against the
    namespace for `environment` (dev/staging/prod, per
    stackbridge.yaml's `environments` section).

    If follow=True, waits for the pod to become Ready (best-effort —
    cpu-stress and network-latency have no readiness probe, so a
    timeout there doesn't fail the run) and tails its logs. The
    experiment keeps running in the cluster even if log-following is
    interrupted; call cleanup_experiment to tear it down explicitly.
    """
    namespace = get_namespace(environment)
    manifest = _manifest_path(service_name, experiment)
    rendered = _rendered_manifest(service_name, experiment, namespace)

    try:
        check_cluster()
        ensure_namespace(namespace)
        ensure_chaos_rbac(namespace)
        ensure_argo_rollouts_installed()
    except KubernetesError as exc:
        raise ChaosError(str(exc)) from exc

    logger.info(
        f"Applying {manifest.relative_to(REPO_ROOT)} "
        f"to namespace '{namespace}' ({environment})..."
    )

    pod_name = f"{service_name}-{experiment}"

    # These are one-shot Pods (restartPolicy: Never). If a previous
    # run's Pod is still around (completed or failed), the manifest
    # is byte-identical, so `kubectl apply` is a no-op and the old,
    # already-finished Pod is left in place — `wait --for=Ready`
    # then times out, and `logs` shows the *previous* run's output
    # instead of actually re-running the experiment. Delete any
    # existing Pod first so apply always creates a fresh one.
    subprocess.run(
        ["kubectl", "delete", "pod", pod_name,
         "--namespace", namespace, "--ignore-not-found",
         "--wait=true"],
        check=True,
    )

    subprocess.run(
        ["kubectl", "apply", "-f", "-"],
        input=rendered,
        text=True,
        check=True,
    )

    logger.success(f"Experiment '{experiment}' started ({pod_name} in {namespace})")

    if not follow:
        return

    logger.info("Waiting for pod to start...")
    subprocess.run(
        [
            "kubectl", "wait",
            f"pod/{pod_name}",
            "--namespace", namespace,
            "--for=condition=Ready",
            "--timeout=60s",
        ],
        check=False,
    )

    logger.info("Tailing logs (Ctrl+C stops following — the experiment keeps running)...")
    subprocess.run(
        [
            "kubectl", "logs",
            f"pod/{pod_name}",
            "--namespace", namespace,
            "--follow",
        ],
        check=False,
    )


def cleanup_experiment(service_name, experiment, environment=DEFAULT_ENVIRONMENT):
    """Delete a chaos experiment's Pod from the cluster, in the
    namespace for `environment`."""
    namespace = get_namespace(environment)
    manifest = _manifest_path(service_name, experiment)
    rendered = _rendered_manifest(service_name, experiment, namespace)

    logger.info(
        f"Deleting {manifest.relative_to(REPO_ROOT)} "
        f"from namespace '{namespace}' ({environment})..."
    )

    subprocess.run(
        ["kubectl", "delete", "-f", "-", "--ignore-not-found"],
        input=rendered,
        text=True,
        check=True,
    )

    logger.success(f"Experiment '{experiment}' cleaned up")
