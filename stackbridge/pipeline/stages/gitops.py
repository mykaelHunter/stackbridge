from stackbridge.pipeline.stage import PipelineStage

from stackbridge.core.gitops import sync
from stackbridge.core.stages import Stage


class GitOpsStage(PipelineStage):

    name = Stage.GITOPS.value

    def run(self, context):

        if not context.config["gitops"]["enabled"]:
            return

        context.logger.stage(self.name)

        sync(context.service)

        context.logger.success("GitOps synchronized")
