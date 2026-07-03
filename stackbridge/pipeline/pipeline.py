import time

from stackbridge.pipeline.context import PipelineContext


class Pipeline:

    def __init__(self, stages):

        self.stages = stages

    def execute(self, context: PipelineContext):

        start = time.perf_counter()

        for stage in self.stages:

            stage.execute(context)

        elapsed = time.perf_counter() - start

        context.logger.success(
            f"Pipeline completed in {elapsed:.2f}s"
        )
