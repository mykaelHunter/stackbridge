import subprocess
import click
from pathlib import Path


def deploy_chart(service_name, environment, image):

    chart = Path("services") / service_name / "helm"

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
            environment,
            "--create-namespace",
            "--set",
            f"image.repository={repository}",
            "--set",
            f"image.tag={tag}"
        ],
        check=True
    )

    click.echo("✓ Helm deployment complete")
