from pathlib import Path

<<<<<<< HEAD
required = [
    "app/app.py",
    "app/requirements.txt",
    "app/Dockerfile",
=======
REQUIRED_FILES  = [
    "app.py",
    "requirements.txt",
    "Dockerfile",
>>>>>>> 75c212b (refactor: introduce deployment pipeline framework)
    "README.md",

    "k8s/deployment.yaml",
    "k8s/service.yaml",
    "k8s/ingress.yaml",
    "k8s/configmap.yaml",

    "helm/Chart.yaml",
    "helm/values.yaml",

    "argocd/application.yaml",

    ".github/workflows/deploy.yaml",
]


def validate(service_name):

    root = Path("services") / service_name

    if not root.exists():
        raise FileNotFoundError(
            f"Service '{service_name}' does not exist."
        )

    for file in REQUIRED_FILES:
        if not (root / file).exists():
            raise FileNotFoundError(
                f"Missing required file: {file}"
            )

    return root
