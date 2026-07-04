from stackbridge.pipeline.stage import PipelineStage

from stackbridge.core.gitops import register, sync
from stackbridge.core.stages import Stage


class GitOpsStage(PipelineStage):

    name = Stage.GITOPS.value

    def execute(self, context):

        context.logger.stage(self.name)

        # Registration is gated by the same gitops.enabled flag as
        # sync(), not run unconditionally. Applying the Application
        # manifest (syncPolicy.automated: prune+selfHeal is baked
        # into argocd/application.yaml) hands ArgoCD's controller
        # ongoing ownership of these objects' fields — it starts
        # reconciling and self-healing independently of this CLI
        # from that point on, whether or not `argocd app sync` is
        # ever explicitly called. That collides with the Helm-based
        # DeployStage, which is a separate field manager applying
        # the same Deployment/ConfigMap: both "own" e.g. .spec.
        # template.spec.containers[].image, and server-side apply
        # correctly refuses to let one silently clobber the other's
        # field ("conflict occurred while applying object ... using
        # apps/v1: .spec.template.spec.containers[...].image").
        #
        # If you want ArgoCD to own deploys for an environment,
        # turn gitops.enabled on for it and stop calling
        # `stackbridge service deploy` there directly — running
        # both against the same objects will always produce this
        # conflict, gitops.enabled is what decides which one wins.
        if not context.config["gitops"]["enabled"]:
            return

        register(context.service, context.environment)

        sync(context.service)

        context.logger.success("GitOps synchronized")
