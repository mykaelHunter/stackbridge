import subprocess
import click


def wait_rollout(service, namespace):
    """
    Wait for a Kubernetes Deployment rollout to complete.
    namespace must match what was passed to helm deploy_chart —
    without this, kubectl defaults to 'default' regardless of
    where Helm actually deployed the release, which causes a
    NotFound error even when the deployment exists and is healthy.
    """

    click.echo("Waiting for rollout...")

    subprocess.run(
        [
            "kubectl",
            "rollout",
            "status",
            f"deployment/{service}",
            "--namespace",
            namespace,
        ],
        check=True
    )

    click.echo("✓ Rollout successful")
