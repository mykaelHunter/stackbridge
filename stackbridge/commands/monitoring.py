import click

from stackbridge.core.monitoring import install_monitoring, MonitoringError


@click.command(name="bootstrap-monitoring")
@click.option(
    "--values-file",
    default=None,
    help="Path to a Helm values file to pass to kube-prometheus-stack "
         "(e.g. to configure Grafana ingress, retention, resource "
         "requests). Optional — installs with chart defaults if omitted.",
)
def bootstrap_monitoring(values_file):
    """
    One-time, per-cluster bootstrap: installs kube-prometheus-stack
    (Prometheus, Alertmanager, Grafana, and the ServiceMonitor/
    PodMonitor/PrometheusRule CRDs) via Helm.

    Run this once per cluster, same as `bootstrap-secrets` for ESO —
    it is not part of `stackbridge service deploy` and won't run
    automatically, since installing/upgrading a cluster-wide operator
    on every deploy is unsafe and unnecessary.

    Services that want to be scraped should ship their own
    ServiceMonitor manifest (e.g. services/<name>/monitoring/) applied
    the same way ESO's eso/<env>/ manifests are — this command only
    provisions the operator and CRDs that manifest depends on.
    """

    try:
        install_monitoring(values_file=values_file)
    except MonitoringError as exc:
        raise click.ClickException(str(exc))

    click.echo("✓ Monitoring bootstrap complete")
