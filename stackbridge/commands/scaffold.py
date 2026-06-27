import click
from pathlib import Path

from stackbridge.core.scaffold import render


@click.command(name="scaffold")
@click.argument("service_name")
def scaffold(service_name):

    root = Path("services") / service_name

    if root.exists():
        click.echo(
            f"Service '{service_name}' already exists"
        )
        return

    for directory in [
        "k8s",
        "helm",
        "argocd",
        ".github/workflows"
    ]:
        (root / directory).mkdir(
            parents=True,
            exist_ok=True
        )

    values = {
        "SERVICE_NAME": service_name,
        "PORT": 8000
    }

    files = {
        "app.py":
            "stackbridge/templates/app.py.tpl",

        "requirements.txt":
            "stackbridge/templates/requirements.txt.tpl",

        "Dockerfile":
            "stackbridge/templates/Dockerfile.tpl",

        "README.md":
            "stackbridge/templates/README.md.tpl",

        "k8s/deployment.yaml":
            "stackbridge/templates/deployment.yaml.tpl",

        "k8s/service.yaml":
            "stackbridge/templates/service.yaml.tpl",

        "helm/Chart.yaml":
            "stackbridge/templates/helm/Chart.yaml.tpl",

        "helm/values.yaml":
            "stackbridge/templates/helm/values.yaml.tpl",

        "argocd/application.yaml":
            "stackbridge/templates/argocd/application.yaml.tpl",

        ".github/workflows/deploy.yaml":
            "stackbridge/templates/github/deploy.yaml.tpl",
    }

    for output, template in files.items():

        content = render(template, values)

        target = root / output

        target.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        target.write_text(content)

    click.echo(
        f"Created service scaffold: {service_name}"
    )
