"""
stackbridge.core.chaos
=======================
Applies, follows, and tears down the chaos experiment manifests that
`stackbridge service scaffold` renders into services/<name>/chaos/.

The manifests themselves are self-contained: each is a single Pod
that runs its own experiment logic (kill pods, stress CPU, inject
latency, cordon a node) and exits on its own. This module just
drives kubectl against them — apply, optionally follow logs, delete.
"""

import subprocess
from pathlib import Path

from stackbridge.core.paths import REPO_ROOT
from stackbridge.core.kubernetes import check_cluster, KubernetesError
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

# All chaos Pods are rendered into this fixed namespace — see the
# `namespace: stackbridge` hardcoded in each chaos/*.yaml.tpl.
CHAOS_NAMESPACE = "stackbridge"


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


def list_experiments(service_name):
    """Experiment ids that have a rendered manifest for this service."""
    chaos_dir = _chaos_dir(service_name)

    if not chaos_dir.exists():
        return []

    return sorted(
        p.stem for p in chaos_dir.glob("*.yaml") if p.stem in EXPERIMENTS
    )


def run_experiment(service_name, experiment, follow=True):
    """
    Apply a chaos experiment manifest to the cluster.

    If follow=True, waits for the pod to become Ready (best-effort —
    cpu-stress and network-latency have no readiness probe, so a
    timeout there doesn't fail the run) and tails its logs. The
    experiment keeps running in the cluster even if log-following is
    interrupted; call cleanup_experiment to tear it down explicitly.
    """
    manifest = _manifest_path(service_name, experiment)

    try:
        check_cluster()
    except KubernetesError as exc:
        raise ChaosError(str(exc)) from exc

    logger.info(f"Applying {manifest.relative_to(REPO_ROOT)}...")

    subprocess.run(
        ["kubectl", "apply", "-f", str(manifest)],
        check=True,
    )

    pod_name = f"{service_name}-{experiment}"

    logger.success(f"Experiment '{experiment}' started ({pod_name})")

    if not follow:
        return

    logger.info("Waiting for pod to start...")
    subprocess.run(
        [
            "kubectl", "wait",
            f"pod/{pod_name}",
            "--namespace", CHAOS_NAMESPACE,
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
            "--namespace", CHAOS_NAMESPACE,
            "--follow",
        ],
        check=False,
    )


def cleanup_experiment(service_name, experiment):
    """Delete a chaos experiment's Pod from the cluster."""
    manifest = _manifest_path(service_name, experiment)

    logger.info(f"Deleting {manifest.relative_to(REPO_ROOT)}...")

    subprocess.run(
        ["kubectl", "delete", "-f", str(manifest), "--ignore-not-found"],
        check=True,
    )

    logger.success(f"Experiment '{experiment}' cleaned up")
