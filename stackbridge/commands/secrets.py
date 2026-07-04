import click

from stackbridge.core.eso import install_eso, apply_eso_manifests, EsoError
from stackbridge.core.kubernetes import ensure_namespace, KubernetesError
from stackbridge.core.paths import REPO_ROOT


@click.command(name="bootstrap-secrets")
@click.argument("service_name")
@click.option(
    "--env",
    default="dev",
    show_default=True,
    help="Deployment environment. Used to locate the Terraform-rendered "
         "manifests at services/<service_name>/eso/<env>/ unless "
         "--eso-dir overrides it.",
)
@click.option(
    "--eso-dir",
    default=None,
    help="Path to the Terraform-rendered eso/ manifests for this "
         "environment. Defaults to services/<service_name>/eso/<env>/ "
         "(see --env), resolved from the repo root regardless of your "
         "current working directory. Only pass this to override the "
         "derived path.",
)
@click.option(
    "--skip-operator-install",
    is_flag=True,
    help="Skip installing the External Secrets Operator (use if it's "
         "already installed cluster-wide).",
)
def bootstrap_secrets(service_name, env, eso_dir, skip_operator_install):
    """
    One-time, per-cluster bootstrap: installs the External Secrets
    Operator (if not already present) and applies this environment's
    eso/ manifests, so the ExternalSecret can sync DB_PASS (and other
    secrets) from AWS Secrets Manager into a real k8s Secret.

    Run this AFTER `terraform apply` has generated
    services/<service_name>/eso/<env>/, and BEFORE
    `stackbridge service deploy <service_name> --env <env>` for the
    same environment.

    Can be run from anywhere inside the repo — the eso path is
    resolved from the repo root, not the current working directory
    (same convention as `deploy`'s helm chart path).
    """

    resolved_eso_dir = (
        eso_dir
        if eso_dir is not None
        else REPO_ROOT / "services" / service_name / "eso" / env
    )

    try:
        if not skip_operator_install:
            install_eso()

        # The eso/<env> manifests (SecretStore, ExternalSecret,
        # ServiceAccount) target the `env` namespace, but bootstrap-secrets
        # is meant to run BEFORE `service deploy`, so that namespace may
        # not exist yet. Ensure it does first (idempotent).
        ensure_namespace(env)

        apply_eso_manifests(resolved_eso_dir)

    except EsoError as exc:
        raise click.ClickException(str(exc))
    except KubernetesError as exc:
        raise click.ClickException(str(exc))

    click.echo(f"✓ Secrets bootstrap complete ({service_name}, {env})")
