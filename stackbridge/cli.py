import click

from stackbridge.commands.create import create
from stackbridge.commands.destroy import destroy
from stackbridge.commands.status import status
from stackbridge.commands.service import service

@click.group()
def cli():
    pass


cli.add_command(create)
cli.add_command(destroy)
cli.add_command(status)
cli.add_command(service)
