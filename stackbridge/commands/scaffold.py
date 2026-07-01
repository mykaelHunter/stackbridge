import click
from pathlib import Path

from stackbridge.core.scaffold import render
from stackbridge.core.paths import REPO_ROOT


@click.command(name="scaffold")
@click.argument("service_name")
def scaffold(service_name):
    """
    Bootstrap a new service from StackBridge templates.
    """

    root = REPO_ROOT / "services" / service_name

    already_existed = root.exists()
    if already_existed:
        click.echo(
            f"Service '{service_name}' already exists — "
            f"checking for missing files to backfill..."
        )
        # Deliberately NOT returning here. The old behavior
        # bailed out entirely the moment the service directory
        # existed, which meant a service scaffolded under an
        # older template layout (e.g. before app/app.py replaced
        # a root-level app.py) could never be brought up to date
        # by re-running scaffold — it would silently no-op
        # forever while validate() kept failing on files that
        # were never created. The per-file existence check
        # further down (target.exists() -> "Exists: ...") already
        # made this safe to do; the only thing missing was not
        # returning before reaching it.

    # --------------------------------------------------
    # Create directory structure
    # --------------------------------------------------
    # 'app' added here — core/validator.py checks for
    # app/app.py and app/requirements.txt, not service-root
    # app.py. This was a real mismatch: a freshly scaffolded
    # service used to fail validate() immediately because the
    # files existed but in the wrong place.

    directories = [
        "app",
        "k8s",
        "helm",
        "helm/templates",
        "argocd",
        ".github/workflows",
    ]

    for directory in directories:
        (root / directory).mkdir(
            parents=True,
            exist_ok=True,
        )

    # --------------------------------------------------
    # Template variables
    # --------------------------------------------------

    values = {
        "SERVICE_NAME": service_name,
        "PORT": 8000,

        # Docker image configuration
        "IMAGE_REPOSITORY": "{{IMAGE_REPOSITORY}}",
        "IMAGE_TAG": "{{IMAGE_TAG}}",

        # GitOps repository
        "REPO_URL": "https://github.com/mykaelHunter/stackbridge.git",
    }

    # --------------------------------------------------
    # Template mapping
    # --------------------------------------------------

    files = {
        # Application — now under app/ to match core/validator.py
        "app/app.py":
            REPO_ROOT / "stackbridge/templates/app.py.tpl",

        "app/requirements.txt":
            REPO_ROOT / "stackbridge/templates/requirements.txt.tpl",

        "app/Dockerfile":
            REPO_ROOT / "stackbridge/templates/Dockerfile.tpl",

        "README.md":
            REPO_ROOT / "stackbridge/templates/README.md.tpl",

        # Kubernetes
        "k8s/deployment.yaml":
            REPO_ROOT / "stackbridge/templates/deployment.yaml.tpl",

        "k8s/service.yaml":
            REPO_ROOT / "stackbridge/templates/service.yaml.tpl",

        "k8s/ingress.yaml":
            REPO_ROOT / "stackbridge/templates/ingress.yaml.tpl",

        "k8s/configmap.yaml":
            REPO_ROOT / "stackbridge/templates/configmap.yaml.tpl",

        # Helm
        "helm/Chart.yaml":
            REPO_ROOT / "stackbridge/templates/helm/Chart.yaml.tpl",

        "helm/values.yaml":
            REPO_ROOT / "stackbridge/templates/helm/values.yaml.tpl",

        "helm/templates/deployment.yaml":
            REPO_ROOT / "stackbridge/templates/helm/templates/deployment.yaml.tpl",

        "helm/templates/service.yaml":
            REPO_ROOT / "stackbridge/templates/helm/templates/service.yaml.tpl",

        "helm/templates/ingress.yaml":
            REPO_ROOT / "stackbridge/templates/helm/templates/ingress.yaml.tpl",

        # ArgoCD
        "argocd/application.yaml":
            REPO_ROOT / "stackbridge/templates/argocd/application.yaml.tpl",

        # GitHub Actions
        ".github/workflows/deploy.yaml":
            REPO_ROOT / "stackbridge/templates/github/deploy.yaml.tpl",
    }

    # --------------------------------------------------
    # Render templates
    # --------------------------------------------------

    for output, template in files.items():

        target = root / output

        if target.exists():
            click.echo(f"✓ Exists: {output}")
            continue

        template_path = Path(template)

        if not template_path.exists():
            raise FileNotFoundError(
                f"Missing template: {template_path}"
            )

        content = render(
            template_path,
            values,
        )

        target.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        target.write_text(
            content,
            encoding="utf-8",
        )

        click.echo(f"Generated {output}")

    if already_existed:
        click.echo(f"\n✓ Backfilled missing files for {service_name}")
    else:
        click.echo(f"\n✓ Bootstrapped {service_name}")
