import subprocess
import click


def wait_rollout(service):

    click.echo("Waiting for rollout...")

    subprocess.run(
        [
            "kubectl",
            "rollout",
            "status",
            f"deployment/{service}"
        ],
        check=True
    )

    click.echo("✓ Rollout successful")
