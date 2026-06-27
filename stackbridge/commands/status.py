import click

@click.command()
@click.option("--env", required=True)
def status(env):
    click.echo(f"Status of environment: {env}")
