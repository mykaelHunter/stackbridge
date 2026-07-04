from stackbridge.pipeline.stage import PipelineStage
from stackbridge.core.slack import SlackNotifier


class NotifyStage(PipelineStage):

    name = "Notify"

    def execute(self, context):

        cfg = context.config

        slack = cfg.get("notifications", {}).get("slack", {})

        if not slack.get("enabled"):

            return

        webhook = slack.get("webhook")

        if not webhook:

            context.logger.warning(
                "Slack notifications are enabled but no webhook is "
                "configured — set the SLACK_WEBHOOK environment variable "
                "or notifications.slack.webhook in stackbridge.yaml. "
                "Skipping notification."
            )
            return

        SlackNotifier(

            webhook

        ).send(context.report)
