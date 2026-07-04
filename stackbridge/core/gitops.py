import subprocess
import click

from stackbridge.core.paths import REPO_ROOT
from stackbridge.core.config import get_namespace, get_registry


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

    # values.yaml's image.repository/image.tag are literal placeholder
    # strings ("{{IMAGE_REPOSITORY}}" / "{{IMAGE_TAG}}") by design — they
    # are always meant to be overridden at render time, the same way
    # `env` is. core/helm.py's deploy_chart() does this via
    # `--set image.repository=... --set image.tag=...`, but ArgoCD
    # renders the chart itself and has no equivalent unless it's baked
    # into source.helm.parameters here. Without it, the deployment gets
    # the literal placeholder text as its image and pods fail with
    # InvalidImageName.
    registry = get_registry()
    image_repository = (
        f"{registry.get('server', '')}/"
        f"{registry.get('organization', '')}/{service}"
    )
    image_tag = registry.get("tag", "latest")

    rendered = (
        manifest_path.read_text()
        .replace("{{NAMESPACE}}", namespace)
        # Chart's configmap.yaml requires .Values.env via `required(...)`,
        # and unlike `stackbridge service deploy` (which passes
        # --set env=<environment> via core/helm.py), ArgoCD renders the
        # chart itself and has no way to know this value unless it's
        # baked into source.helm.parameters here. Without it, `argocd
        # app sync` fails with "env is required — pass --set env=
        # <environment> at deploy time" even though the Application
        # looks correctly configured otherwise.
        .replace("{{ENVIRONMENT}}", environment)
        .replace("{{IMAGE_REPOSITORY}}", image_repository)
        .replace("{{IMAGE_TAG}}", image_tag)
    )

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
