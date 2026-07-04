import subprocess
import click

from stackbridge.core.paths import REPO_ROOT
from stackbridge.core.config import get_namespace


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


def register(service, environment):
    """
    Apply the scaffolded argocd/application.yaml for `service` so
    ArgoCD actually knows this Application exists.

    `stackbridge service scaffold` generates this manifest, but
    nothing previously applied it — so services deployed via
    `stackbridge service deploy` were running (via the Helm-based
    DeployStage) without ArgoCD ever being aware of them, and
    `sync()` below (`argocd app sync <service>`) would fail against
    an Application that was never created.

    An ArgoCD Application is just a CRD, so this only needs plain
    `kubectl apply` — no `argocd` CLI login required. Safe to call
    on every deploy: apply is idempotent.
    """

    manifest_path = (
        REPO_ROOT / "services" / service / "argocd" / "application.yaml"
    )

    if not manifest_path.exists():
        raise FileNotFoundError(
            f"No ArgoCD Application manifest found at {manifest_path}. "
            f"Run `stackbridge service scaffold {service}` first."
        )

    namespace = get_namespace(environment)
    rendered = manifest_path.read_text().replace("{{NAMESPACE}}", namespace)

    click.echo(f"Registering '{service}' with ArgoCD (namespace: {namespace})...")

    # Application CRs must live in ArgoCD's own namespace (argocd)
    # to be picked up by the controller and shown in the UI — this
    # is separate from `spec.destination.namespace` above, which is
    # where the *deployed workload* lands, not where the Application
    # object itself is stored. Without -n argocd here, kubectl falls
    # back to the current kubeconfig context's default namespace,
    # and the Application silently never appears in ArgoCD at all.
    subprocess.run(
        ["kubectl", "apply", "-n", "argocd", "-f", "-"],
        input=rendered,
        text=True,
        check=True,
    )

    click.echo("✓ ArgoCD Application registered")


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
