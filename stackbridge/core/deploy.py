import subprocess

from stackbridge.core.validator import validate
from stackbridge.core.docker import build
from stackbridge.core.registry import push


def deploy_service(service_name, environment):

    print("Validating service...")
    validate(service_name)

    print("Building Docker image...")
    image = build(service_name)

    print("Pushing Docker image...")
    push(image)

    print("Deploying Kubernetes manifests...")

    subprocess.run(
        [
            "kubectl",
            "apply",
            "-f",
            f"services/{service_name}/k8s",
        ],
        check=True,
    )

    print("Waiting for rollout...")

    subprocess.run(
        [
            "kubectl",
            "rollout",
            "status",
            "deployment",
            service_name,
        ],
        check=True,
    )

    print("Deployment successful!")
