from stackbridge.pipeline.stage import PipelineStage

from stackbridge.core.validator import validate
from stackbridge.core.stages import Stage


class ValidationStage(PipelineStage):

    name = Stage.VALIDATION.value

    def execute(self, context):

        context.logger.stage(self.name)

        validate(context.service)

        context.logger.success("Service validated")
