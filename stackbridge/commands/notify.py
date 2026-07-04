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

    slack_cfg = cfg.get("notifications", {}).get("slack", {})

    if not slack_cfg.get("enabled"):
        click.echo("Slack notifications are disabled.")
        return

    webhook = slack_cfg.get("webhook")

    if not webhook:
        click.echo(
            "Slack notifications are enabled but no webhook is configured — "
            "set the SLACK_WEBHOOK environment variable or "
            "notifications.slack.webhook in stackbridge.yaml.",
            err=True,
        )
        raise SystemExit(1)

    report = DeploymentReport(
        service="stackbridge",
        environment="dev",
        image="docker.io/mykaelhunter/stackbridge:latest",
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
        webhook
    ).send(report)

    click.secho(
        "✓ Slack notification sent.",
        fg="green",
    )
