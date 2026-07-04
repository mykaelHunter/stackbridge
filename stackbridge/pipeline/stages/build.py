from stackbridge.pipeline.stage import PipelineStage

from stackbridge.core.stages import Stage
from stackbridge.core.docker import build

from stackbridge.core.events import (
    Event,
    DeploymentEvent,
)


class BuildStage(PipelineStage):

    name = Stage.BUILD.value

    def execute(self, context):

        context.logger.stage(self.name)

        image = build(context.service)

        context.image = image
        
        context.report.image = image

        context.logger.success("Docker image built")

        event = Event(
            type=DeploymentEvent.BUILD,
            service=context.service,
            status="SUCCESS",
            message="Docker image built",
        )

        context.eventbus.publish(event)
        context.report.add_event(event)
