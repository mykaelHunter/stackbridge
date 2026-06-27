import subprocess


def deploy_service(service_name):

    subprocess.run(
        [
            "kubectl",
            "apply",
            "-f",
            f"services/{service_name}/k8s"
        ]
    )
