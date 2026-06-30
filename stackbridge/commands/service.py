import click

from stackbridge.commands.scaffold import scaffold
from stackbridge.commands.deploy import deploy
from stackbridge.commands.delete import delete_service
from stackbridge.commands.catalog import list_services
from stackbridge.commands.describe import describe
from stackbridge.commands.bootstrap import bootstrap
from stackbridge.commands.deploy import deploy

@click.group()
def service():
    """Manage platform services"""
    pass


service.add_command(scaffold)
service.add_command(deploy)
service.add_command(delete_service)
service.add_command(list_services)
service.add_command(describe)
service.add_command(bootstrap)
service.add_command(deploy)
