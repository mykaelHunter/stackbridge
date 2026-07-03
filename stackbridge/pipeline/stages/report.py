from stackbridge.pipeline.stage import PipelineStage

from stackbridge.core.stages import Stage


class ReportStage(PipelineStage):

    name = Stage.REPORT.value

    def execute(self, context):

        context.logger.stage(self.name)

        context.success = True

        context.report.finish(success=True)
        context.report.save()

        context.finished_at = context.report.finished_at

        context.logger.success("Deployment report generated")

        context.logger.success(
            f"Deployment completed in {context.timer.elapsed()} seconds"
        )
