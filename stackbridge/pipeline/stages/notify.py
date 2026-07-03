from stackbridge.pipeline.stage import PipelineStage
from stackbridge.core.slack import SlackNotifier


class NotifyStage(PipelineStage):

    name = "Notify"

    def execute(self, context):

        cfg = context.config

        slack = cfg.get("notifications", {}).get("slack", {})

        if not slack.get("enabled"):

            return

        SlackNotifier(

            slack["webhook"]

        ).send(context.report)
