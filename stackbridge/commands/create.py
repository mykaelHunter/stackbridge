import click

@click.command()
@click.option("--env", required=True)
def create(env):
    click.echo(f"Creating environment: {env}")
