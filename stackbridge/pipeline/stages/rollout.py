from stackbridge.pipeline.stage import PipelineStage

from stackbridge.core.rollout import wait_rollout
from stackbridge.core.stages import Stage


class RolloutStage(PipelineStage):

    name = Stage.ROLLOUT.value

    def execute(self, context):

        context.logger.stage(self.name)

        wait_rollout(context.service)

        context.logger.success("Rollout completed")
