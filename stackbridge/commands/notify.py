import click
from datetime import datetime

from stackbridge.core.config import load_config
from stackbridge.core.events import Event, DeploymentEvent
from stackbridge.core.report import DeploymentReport
from stackbridge.core.slack import SlackNotifier


@click.group()
def notify():
    """Notification commands."""
    pass


@notify.command()
def test():
    """Send a test Slack notification."""

    cfg = load_config()

    slack_cfg = cfg["notifications"]["slack"]

    if not slack_cfg["enabled"]:
        click.echo("Slack notifications are disabled.")
        return

    report = DeploymentReport(
        service="stackbridge",
        environment="dev",
        image="docker.io/stackbridge:latest",
        started_at=datetime.utcnow(),
    )

    report.success = True
    report.duration = 4.25

    report.events = [
        Event(
            type=DeploymentEvent.VALIDATION,
            service="stackbridge",
            status="SUCCESS",
            message="Validation successful",
        ),
        Event(
            type=DeploymentEvent.BUILD,
            service="stackbridge",
            status="SUCCESS",
            message="Image built",
        ),
        Event(
            type=DeploymentEvent.DEPLOY,
            service="stackbridge",
            status="SUCCESS",
            message="Deployment completed",
        ),
    ]

    SlackNotifier(
        slack_cfg["webhook"]
    ).send(report)

    click.secho(
        "✓ Slack notification sent.",
        fg="green",
    )
