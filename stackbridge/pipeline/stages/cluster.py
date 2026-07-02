from stackbridge.core.kubernetes import check_cluster
from stackbridge.core.stages import Stage

from stackbridge.pipeline.stage import PipelineStage


class ClusterStage(PipelineStage):

    name = Stage.CLUSTER.value

    def run(self, context):

        context.logger.stage(self.name)

        check_cluster()

        context.logger.success(
            "Kubernetes cluster reachable"
        )
