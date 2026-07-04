from stackbridge.pipeline.stage import PipelineStage

from stackbridge.core.gitops import register, sync
from stackbridge.core.stages import Stage


class GitOpsStage(PipelineStage):

    name = Stage.GITOPS.value

    def execute(self, context):

        context.logger.stage(self.name)

        # Registration is separate from the gitops.enabled flag:
        # this just makes sure ArgoCD knows the Application exists
        # (kubectl apply on a CRD, idempotent, no argocd CLI/login
        # needed) so the app is visible in the ArgoCD UI regardless
        # of whether CLI-driven sync is turned on.
        register(context.service, context.environment)

        if not context.config["gitops"]["enabled"]:
            return

        sync(context.service)

        context.logger.success("GitOps synchronized")
