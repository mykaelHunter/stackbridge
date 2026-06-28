import subprocess


def build(service_name):

    image = f"stackbridge/{service_name}:latest"

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
