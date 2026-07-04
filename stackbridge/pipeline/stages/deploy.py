from stackbridge.pipeline.stage import PipelineStage

from stackbridge.core.stages import Stage
from stackbridge.core.helm import deploy_chart
from stackbridge.core.config import get_namespace


class DeployStage(PipelineStage):

    name = Stage.DEPLOY.value

    def execute(self, context):

        context.logger.stage(self.name)

        context.namespace = get_namespace(context.environment)

        deploy_chart(
            context.service,
            context.namespace,
            context.image,
            context.environment,
        )

        context.logger.success("Helm deployment completed")
