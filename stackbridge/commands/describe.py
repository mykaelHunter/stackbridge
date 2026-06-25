import click
from stackbridge.core.catalog_loader import load_catalog


@click.command(name="describe")
@click.argument("name")
def describe(name):

    data = load_catalog()

    service = next(
        (
            s for s in data["services"]
            if s["name"] == name
        ),
        None
    )

    if not service:
        click.echo(f"Service '{name}' not found")
        return

    click.echo(f"Name: {service['name']}")
    click.echo(f"Runtime: {service['runtime']}")
    click.echo(f"Port: {service['port']}")
    click.echo(
    f"Description: {service.get('description', 'N/A')}"
)
