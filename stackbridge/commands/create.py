import click

from stackbridge.core.terraform import provision, TerraformError
from stackbridge.core.kubernetes import (
    check_cluster,
    ensure_argocd_installed,
    KubernetesError,
)


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

    click.echo("\nChecking for ArgoCD...")
    try:
        check_cluster()
        ensure_argocd_installed()
    except KubernetesError as e:
        click.echo(f"Failed to install ArgoCD: {e}", err=True)
        raise SystemExit(1)

    click.echo(
        "✓ ArgoCD is installed. Get the initial admin password with:\n"
        "  kubectl -n argocd get secret argocd-initial-admin-secret "
        "-o jsonpath=\"{.data.password}\" | base64 -d"
    )
