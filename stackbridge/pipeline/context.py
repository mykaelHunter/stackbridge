from dataclasses import dataclass, field

from stackbridge.core.eventbus import EventBus
from stackbridge.core.logger import Logger, get_logger
from stackbridge.core.metrics import Timer

@dataclass
class PipelineContext:

    service: str
    environment: str

    image: str | None = None
    config: dict | None = None

    logger: Logger = field(default_factory=get_logger)
    timer: Timer = field(default_factory=Timer)
    eventbus: EventBus = field(default_factory=EventBus)
