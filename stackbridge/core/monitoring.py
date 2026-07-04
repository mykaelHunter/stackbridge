"""
Bootstrap helpers for cluster-wide monitoring (kube-prometheus-stack).

Same shape as core/eso.py: this is a cluster-level, one-time install —
it is NOT part of the per-service deploy pipeline. A given cluster
only needs the stack installed once. Call it explicitly via
`stackbridge environment bootstrap-monitoring`.

kube-prometheus-stack bundles Prometheus, Alertmanager, Grafana, and
the operator/CRDs (ServiceMonitor, PodMonitor, PrometheusRule) that
services use to expose their own scrape configs — so, like ESO, this
needs to exist before any service-level ServiceMonitor manifests can
be applied.
"""
import shutil
import subprocess

import click

MONITORING_NAMESPACE = "monitoring"
MONITORING_HELM_REPO_NAME = "prometheus-community"
MONITORING_HELM_REPO_URL = "https://prometheus-community.github.io/helm-charts"
MONITORING_RELEASE_NAME = "kube-prometheus-stack"
MONITORING_CHART_NAME = "prometheus-community/kube-prometheus-stack"


class MonitoringError(Exception):
    pass


def _require_binaries():
    for binary in ("helm", "kubectl"):
        if shutil.which(binary) is None:
            raise MonitoringError(f"{binary} is not installed.")


REQUIRED_CRDS = (
    "prometheuses.monitoring.coreos.com",
    "servicemonitors.monitoring.coreos.com",
    "alertmanagers.monitoring.coreos.com",
)


def monitoring_installed():
    """
    Return True only if BOTH the operator pods AND its CRDs are
    present — same false-positive guard as eso.eso_installed(): a
    prior crashed/partial install can leave pods without CRDs
    registered, which produces "no matches for kind ServiceMonitor
    ... ensure CRDs are installed first" when services later apply
    their own ServiceMonitor manifests.
    """

    pods = subprocess.run(
        ["kubectl", "get", "pods", "-n", MONITORING_NAMESPACE],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if pods.returncode != 0:
        return False

    for crd in REQUIRED_CRDS:
        crd_check = subprocess.run(
            ["kubectl", "get", "crd", crd],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if crd_check.returncode != 0:
            return False

    return True


def install_monitoring(values_file=None, timeout="10m"):
    """
    Install or update kube-prometheus-stack via Helm (idempotent).

    Unlike eso.install_eso() (which really is call-once — ESO itself
    never takes per-environment config), this deliberately does NOT
    skip when already installed: `helm upgrade --install` is already
    idempotent and near-instant with no diff, and skipping outright
    would silently ignore any --values-file passed on a later call
    (e.g. to turn on LoadBalancer services for Prometheus/Grafana/
    Alertmanager) with no error — it would just look like the flag
    did nothing.
    """

    _require_binaries()

    already_installed = monitoring_installed()

    if already_installed:
        click.echo("kube-prometheus-stack already installed — applying update...")
    else:
        click.echo("Installing kube-prometheus-stack...")

    subprocess.run(
        ["helm", "repo", "add", MONITORING_HELM_REPO_NAME, MONITORING_HELM_REPO_URL],
        check=True,
    )
    subprocess.run(["helm", "repo", "update"], check=True)

    # upgrade --install (not plain install), same rationale as ESO:
    # repairs a cluster left in a half-installed state instead of
    # erroring on "release already exists".
    #
    # --timeout is raised from Helm's 5m default because this chart's
    # post-install hook (Job/kube-prometheus-stack-admission-patch,
    # which patches the operator's admission webhook CA bundle) can
    # legitimately take longer than 5m on a slow image pull or under
    # node scheduling pressure — the default timeout expiring looks
    # identical to a genuinely stuck/failed job ("context deadline
    # exceeded"), so if it's still failing at 10m, that's a real
    # problem with the job (check `kubectl describe pod` in the
    # monitoring namespace for ImagePullBackOff / Pending), not
    # something a longer timeout will fix.
    cmd = [
        "helm", "upgrade", "--install", MONITORING_RELEASE_NAME,
        MONITORING_CHART_NAME,
        "--namespace", MONITORING_NAMESPACE,
        "--create-namespace",
        "--timeout", timeout,
    ]

    if values_file is not None:
        cmd.extend(["--values", str(values_file)])

    subprocess.run(cmd, check=True)

    if already_installed:
        click.echo("✓ kube-prometheus-stack updated")
        return

    click.echo("Waiting for monitoring CRDs to become available...")
    for crd in REQUIRED_CRDS:
        subprocess.run(
            [
                "kubectl", "wait", "--for", "condition=Established",
                f"crd/{crd}", "--timeout", "120s",
            ],
            check=True,
        )

    click.echo("✓ kube-prometheus-stack installed")
