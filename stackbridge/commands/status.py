import click

from stackbridge.core.terraform import (
    terraform_init,
    terraform_outputs,
    terraform_resources,
    TerraformError,
)


@click.command()
@click.option("--env", required=True, help="Environment to inspect (dev, staging)")
def status(env):
    """Show outputs and provisioned resources for an environment."""
    click.echo(f"Status of environment: {env}\n")

    try:
        terraform_init(env)
        outputs = terraform_outputs(env)
        resources = terraform_resources(env)
    except TerraformError as e:
        click.echo(f"Failed: {e}", err=True)
        raise SystemExit(1)

    if outputs:
        click.echo("Outputs:")
        for key, val in outputs.items():
            click.echo(f"  {key} = {val.get('value', 'N/A')}")
    else:
        click.echo("No outputs found — environment may not be provisioned yet.")

    click.echo()

    if resources:
        click.echo(f"Resources ({len(resources)}):")
        for r in resources:
            click.echo(f"  {r}")
    else:
        click.echo("No resources in state — run 'stackbridge create --env "
                    f"{env}' to provision.")
