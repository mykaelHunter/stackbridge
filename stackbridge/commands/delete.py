import click
import shutil

from stackbridge.core.paths import REPO_ROOT


@click.command(name="delete")
@click.argument("service_name")
def delete_service(service_name):

    # Resolved via the shared repo-root finder — same fix as
    # every other command that touches services/<name>.
    path = REPO_ROOT / "services" / service_name

    if not path.exists():
        click.echo("Service not found")
        return

    shutil.rmtree(path)

    click.echo(
        f"Deleted {service_name}"
    )
