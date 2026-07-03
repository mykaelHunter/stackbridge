import click

from stackbridge.catalog.registry import ServiceRegistry
from stackbridge.catalog.validator import validate


@click.group()
def catalog():
    pass


@catalog.command()
def list():

    registry = ServiceRegistry()

    for svc in registry.list():

        click.echo(
            f"{svc['name']:20} {svc['owner']}"
        )


@catalog.command()
@click.argument("service")
def describe(service):

    registry = ServiceRegistry()

    svc = registry.get(service)

    if not svc:

        click.echo("Service not found")

        return

    for key, value in svc.items():

        click.echo(f"{key}: {value}")


@catalog.command()
def validate_catalog():

    validate()

    click.echo("Catalog valid")
