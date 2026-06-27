import click
from pathlib import Path

from stackbridge.commands.scaffold import scaffold


@click.command(name="bootstrap")
@click.argument("service_name")
def bootstrap(service_name):

    ctx = click.get_current_context()

    ctx.invoke(
        scaffold,
        service_name=service_name
    )

    click.echo(
        f"Bootstrapped {service_name}"
    )
