import subprocess

from stackbridge.core.config import get_registry


def build(service_name):

    registry = get_registry()

    server = registry.get("server", "docker.io")
    organization = registry.get("organization", "mykaelhunter")
    tag = registry.get("tag", "latest")

    image = f"{server}/{organization}/{service_name}:{tag}"

    subprocess.run(
        [
            "docker",
            "build",
            "-t",
            image,
            f"services/{service_name}",
        ],
        check=True,
    )

    return image
