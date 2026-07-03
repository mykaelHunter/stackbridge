from stackbridge.pipeline.stage import PipelineStage

from stackbridge.core.stages import Stage
from stackbridge.core.helm import deploy_chart


class DeployStage(PipelineStage):

    name = Stage.DEPLOY.value

    def execute(self, context):

        context.logger.stage(self.name)

        deploy_chart(
            context.service,
            context.environment,
            context.image,
        )

        context.logger.success("Helm deployment completed")
