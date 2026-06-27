import click
import subprocess
from pathlib import Path


@click.command(name="deploy")
@click.argument("service_name")
def deploy(service_name):

    service_dir = Path("services") / service_name

    if not service_dir.exists():
        click.echo(
            f"Service '{service_name}' not found"
        )
        return

    click.echo(
        f"Deploying {service_name}..."
    )

    subprocess.run(
        [
            "kubectl",
            "apply",
            "-f",
            str(service_dir / "k8s")
        ]
    )
