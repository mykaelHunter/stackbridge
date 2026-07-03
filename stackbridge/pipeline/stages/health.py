from stackbridge.pipeline.stage import PipelineStage

from stackbridge.core.health import check_health
from stackbridge.core.stages import Stage


class HealthStage(PipelineStage):

    name = Stage.HEALTH.value

    def execute(self, context):

        context.logger.stage(self.name)

        check_health(context.service)

        context.logger.success("Health checks passed")
