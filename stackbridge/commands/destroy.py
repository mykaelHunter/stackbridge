import click

@click.command()
@click.option("--env", required=True)
def destroy(env):
    click.echo(f"Destroying environment: {env}")
