import click
from pathlib import Path

from stackbridge.core.scaffold import render


@click.command(name="scaffold")
@click.argument("service_name")
def scaffold(service_name):
    """
    Bootstrap a new service from StackBridge templates.
    """

    root = Path("services") / service_name

    if root.exists():
        click.echo(f"Service '{service_name}' already exists")
        return

    # --------------------------------------------------
    # Create directory structure
    # --------------------------------------------------

    directories = [
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
    "IMAGE_REPOSITORY": f"docker.io/stackbridge/{service_name}",
    "IMAGE_TAG": "latest",

    # GitOps repository
    "REPO_URL": "https://github.com/mykaelHunter/stackbridge.git",
    }

    # --------------------------------------------------
    # Template mapping
    # --------------------------------------------------

    files = {
        # Application
        "app.py":
            "stackbridge/templates/app.py.tpl",

        "requirements.txt":
            "stackbridge/templates/requirements.txt.tpl",

        "Dockerfile":
            "stackbridge/templates/Dockerfile.tpl",

        "README.md":
            "stackbridge/templates/README.md.tpl",

        # Kubernetes
        "k8s/deployment.yaml":
            "stackbridge/templates/deployment.yaml.tpl",

        "k8s/service.yaml":
            "stackbridge/templates/service.yaml.tpl",

        "k8s/ingress.yaml":
            "stackbridge/templates/ingress.yaml.tpl",

        "k8s/configmap.yaml":
            "stackbridge/templates/configmap.yaml.tpl",

        # Helm
        "helm/Chart.yaml":
            "stackbridge/templates/helm/Chart.yaml.tpl",

        "helm/values.yaml":
            "stackbridge/templates/helm/values.yaml.tpl",

        "helm/templates/deployment.yaml":
            "stackbridge/templates/helm/templates/deployment.yaml.tpl",

        "helm/templates/service.yaml":
            "stackbridge/templates/helm/templates/service.yaml.tpl",

        "helm/templates/ingress.yaml":
            "stackbridge/templates/helm/templates/ingress.yaml.tpl",

        # ArgoCD
        "argocd/application.yaml":
            "stackbridge/templates/argocd/application.yaml.tpl",

        # GitHub Actions
        ".github/workflows/deploy.yaml":
            "stackbridge/templates/github/deploy.yaml.tpl",
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

    click.echo(f"\n✓ Bootstrapped {service_name}")
