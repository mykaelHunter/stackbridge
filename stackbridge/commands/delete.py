import click
import shutil
from pathlib import Path


@click.command(name="delete")
@click.argument("service_name")
def delete_service(service_name):

    path = Path("services") / service_name

    if not path.exists():
        click.echo("Service not found")
        return

    shutil.rmtree(path)

    click.echo(
        f"Deleted {service_name}"
    )
