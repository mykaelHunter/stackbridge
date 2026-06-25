import click
from stackbridge.core.catalog_loader import load_catalog


@click.command(name="list")
def list_services():
    """List services"""

    data = load_catalog()

    for svc in data["services"]:
        click.echo(svc["name"])
