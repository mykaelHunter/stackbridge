import click

from stackbridge.core.deploy import deploy_service


@click.command(name="deploy")
@click.argument("service_name")
@click.option(
    "--env",
    default="dev",
    help="Deployment environment",
)
def deploy(service_name, env):
    """
    Deploy a service.
    """
    deploy_service(service_name, env)
