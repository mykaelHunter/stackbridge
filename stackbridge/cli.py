import click

from stackbridge.commands.service import service
from stackbridge.commands.catalog import catalog
from stackbridge.commands.notify import notify

@click.group()
def cli():
    pass


cli.add_command(service)
cli.add_command(catalog)
cli.add_command(notify)
