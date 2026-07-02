from stackbridge.core.scanner import scan_image
from stackbridge.core.stages import Stage

from stackbridge.pipeline.stage import PipelineStage


class ScanStage(PipelineStage):

    name = Stage.SCAN.value

    def run(self, context):

        context.logger.stage(self.name)

        scan_image(context.image)

        context.logger.success(
            "Security scan completed"
        )
