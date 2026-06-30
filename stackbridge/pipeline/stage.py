from abc import ABC, abstractmethod


class PipelineStage(ABC):
    """
    Base class for all pipeline stages.
    """

    name = "Unnamed Stage"

    @abstractmethod
    def execute(self, context):
        """Execute the stage."""
        pass
