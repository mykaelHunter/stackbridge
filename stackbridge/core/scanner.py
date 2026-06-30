import subprocess
import click


def scan_image(image):

    click.echo("Scanning image...")

    subprocess.run(
        [
            "trivy",
            "image",
            image
        ],
        check=True
    )

    click.echo("✓ Scan passed")
