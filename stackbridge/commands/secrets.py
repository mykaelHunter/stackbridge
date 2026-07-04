import click

from stackbridge.core.eso import install_eso, apply_eso_manifests, EsoError


@click.command(name="bootstrap-secrets")
@click.option(
    "--eso-dir",
    default="eso",
    show_default=True,
    help="Path to the Terraform-rendered eso/ manifests for this environment.",
)
@click.option(
    "--skip-operator-install",
    is_flag=True,
    help="Skip installing the External Secrets Operator (use if it's "
         "already installed cluster-wide).",
)
def bootstrap_secrets(eso_dir, skip_operator_install):
    """
    One-time, per-cluster bootstrap: installs the External Secrets
    Operator (if not already present) and applies this environment's
    eso/ manifests, so the ExternalSecret can sync DB_PASS (and other
    secrets) from AWS Secrets Manager into a real k8s Secret.

    Run this AFTER `terraform apply` has generated eso/, and BEFORE
    `stackbridge service deploy` for the same environment.
    """

    try:
        if not skip_operator_install:
            install_eso()

        apply_eso_manifests(eso_dir)

    except EsoError as exc:
        raise click.ClickException(str(exc))

    click.echo("✓ Secrets bootstrap complete")
