from stackbridge.core.paths import REPO_ROOT

REQUIRED_FILES = [
    "app/app.py",
    "app/requirements.txt",
    "app/Dockerfile",
    "README.md",

    "k8s/deployment.yaml",
    "k8s/service.yaml",
    "k8s/ingress.yaml",
    "k8s/configmap.yaml",

    "helm/Chart.yaml",
    "helm/values.yaml",

    "argocd/application.yaml",

    ".github/workflows/deploy.yaml",

    # Chaos experiments — required as part of the standard
    # service contract so chaos testing is built-in to every
    # service, not added as an afterthought. Matches Phase 4
    # experiment set. scaffold creates these automatically.
    "chaos/cpu-stress.yaml",
    "chaos/pod-kill.yaml",
    "chaos/az-failure.yaml",
    "chaos/network-latency.yaml",
]


def validate(service_name):

    # Resolved path — same fix as elsewhere in core/. Without
    # this, validate() looked for services/<name> relative to
    # the caller's cwd, not the repo root.
    root = REPO_ROOT / "services" / service_name

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
