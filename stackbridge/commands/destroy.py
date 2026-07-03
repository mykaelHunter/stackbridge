import click

from stackbridge.core.terraform import terraform_destroy, TerraformError


@click.command()
@click.option("--env", required=True, help="Environment to destroy (dev, staging)")
@click.option("--force", is_flag=True, help="Skip the confirmation prompt")
def destroy(env, force):
    """Tear down an environment. Prompts for confirmation unless --force is passed."""

    if not force:
        click.echo(f"\nWARNING: this will destroy all resources in '{env}'.")
        click.echo("This action cannot be undone. All data will be lost.\n")
        if not click.confirm(f"Type 'y' to confirm destruction of '{env}'"):
            click.echo("Aborted.")
            return

    click.echo(f"Destroying environment: {env}")

    try:
        terraform_destroy(env)
    except TerraformError as e:
        click.echo(f"Failed: {e}", err=True)
        raise SystemExit(1)

    click.echo(f"Environment '{env}' destroyed.")
