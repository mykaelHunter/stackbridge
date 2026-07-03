import subprocess
import click
from pathlib import Path

from stackbridge.core.paths import REPO_ROOT


def deploy_chart(service_name, namespace, image):

    # Resolved path — same fix as core/docker.py and core/config.py.
    chart = REPO_ROOT / "services" / service_name / "helm"

    click.echo("Deploying Helm chart...")

    repository, tag = image.rsplit(":", 1)


    subprocess.run(
        [
            "helm",
            "upgrade",
            "--install",
            service_name,
            str(chart),
            "--namespace",
            namespace,
            "--create-namespace",
            "--set",
            f"image.repository={repository}",
            "--set",
            f"image.tag={tag}"
        ],
        check=True
    )

    click.echo("✓ Helm deployment complete")
