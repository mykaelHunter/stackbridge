import click

from stackbridge.commands.scaffold import scaffold
from stackbridge.commands.deploy import deploy
from stackbridge.commands.bootstrap import bootstrap
from stackbridge.commands.chaos import chaos
from stackbridge.commands.delete import delete_service


@click.group()
def service():
    """Manage platform services"""
    pass


service.add_command(scaffold)
service.add_command(bootstrap)
service.add_command(chaos)
service.add_command(deploy)
service.add_command(delete_service)
