from stackbridge.pipeline.stage import PipelineStage

from stackbridge.core.stages import Stage
from stackbridge.core.docker import build

from stackbridge.core.events import (
    Event,
    DeploymentEvent,
)

from stackbridge.core.eventbus import EventBus


class BuildStage(PipelineStage):

    name = Stage.BUILD.value

    def execute(self, context):

        context.logger.stage(self.name)

        image = build(context.service)

        context.image = image
        
        context.report.image = image

        context.logger.success("Docker image built")

        bus = EventBus()

        bus.emit(
            Event(
                type=DeploymentEvent.BUILD,
                service=context.service,
                status="SUCCESS",
                message="Docker image built",
            )
        )
