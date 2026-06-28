import subprocess


def push(image):

    subprocess.run(
        [
            "docker",
            "push",
            image,
        ],
        check=True,
    )
