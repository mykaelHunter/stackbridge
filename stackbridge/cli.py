import click

from commands.create import create
from commands.destroy import destroy
from commands.status import status


@click.group()
def cli():
    pass


cli.add_command(create)
cli.add_command(destroy)
cli.add_command(status)
