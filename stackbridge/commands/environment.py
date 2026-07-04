import click

from stackbridge.commands.create import create
from stackbridge.commands.destroy import destroy
from stackbridge.commands.status import status
from stackbridge.commands.secrets import bootstrap_secrets
from stackbridge.commands.monitoring import bootstrap_monitoring


@click.group()
def environment():
    """Provision, tear down, and inspect Terraform-managed environments."""
    pass


environment.add_command(create)
environment.add_command(destroy)
environment.add_command(status)
environment.add_command(bootstrap_secrets)
environment.add_command(bootstrap_monitoring)
