import subprocess
import click


def commit(service, version):
    """
    Commit and push deployment manifests.
    """

    click.echo("Committing GitOps changes...")

    subprocess.run(
        ["git", "add", "."],
        check=True,
    )

    subprocess.run(
        [
            "git",
            "commit",
            "-m",
            f"Deploy {service} {version}",
        ],
        check=True,
    )

    subprocess.run(
        ["git", "push"],
        check=True,
    )

    click.echo("✓ Git changes pushed")


def sync(service):
    """
    Synchronize ArgoCD application.
    """

    click.echo("Syncing ArgoCD...")

    subprocess.run(
        [
            "argocd",
            "app",
            "sync",
            service,
        ],
        check=True,
    )

    click.echo("✓ ArgoCD synchronized")
