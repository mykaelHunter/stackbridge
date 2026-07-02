from stackbridge.pipeline.stage import PipelineStage

from stackbridge.core.report import report
from stackbridge.core.stages import Stage


class ReportStage(PipelineStage):

    name = Stage.REPORT.value

    def run(self, context):

        context.logger.stage(self.name)

        report(
            context.service,
            context.image,
        )

        context.logger.success("Deployment report generated")

        context.logger.success(
            f"Deployment completed in {context.timer.elapsed()} seconds"
        )
