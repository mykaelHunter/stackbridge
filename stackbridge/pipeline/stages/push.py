from stackbridge.core.registry import push
from stackbridge.core.stages import Stage

from stackbridge.pipeline.stage import PipelineStage


class PushStage(PipelineStage):

    name = Stage.PUSH.value

    def run(self, context):

        context.logger.stage(self.name)

        push(context.image)

        context.logger.success(
            "Image pushed"
        )
