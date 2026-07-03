import click

from stackbridge.core.terraform import provision, TerraformError


@click.command()
@click.option("--env", required=True, help="Environment to create (dev, staging)")
def create(env):
    """Provision an environment: terraform init -> plan -> OPA policy check -> apply."""
    click.echo(f"Creating environment: {env}")

    try:
        outputs = provision(env)
    except TerraformError as e:
        click.echo(f"Failed: {e}", err=True)
        raise SystemExit(1)

    click.echo(f"\nEnvironment '{env}' created.\n")

    if outputs:
        click.echo("Outputs:")
        for key, val in outputs.items():
            click.echo(f"  {key} = {val.get('value', 'N/A')}")
    else:
        click.echo("(no outputs returned)")
