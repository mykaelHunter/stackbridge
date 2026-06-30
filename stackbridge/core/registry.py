import subprocess
import click


def push(image):

    click.echo("Pushing image...")

    subprocess.run(
        [
            "docker",
            "push",
            image
        ],
        check=True
    )

    click.echo("✓ Image pushed")
