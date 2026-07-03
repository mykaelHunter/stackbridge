from dataclasses import dataclass, field
from datetime import datetime

from stackbridge.core.eventbus import EventBus
from stackbridge.core.logger import Logger, get_logger
from stackbridge.core.metrics import Timer

from stackbridge.core.report import DeploymentReport


@dataclass
class PipelineContext:

    service: str

    environment: str

    image: str | None = None

    config: dict | None = None

    namespace: str | None = None

    success: bool = False

    started_at: datetime = field(default_factory=datetime.utcnow)

    finished_at: datetime | None = None

    error: str | None = None

    report: DeploymentReport | None = None
                                                     
    logger: Logger = field(default_factory=get_logger)

    timer: Timer = field(default_factory=Timer)

    eventbus: EventBus = field(default_factory=EventBus)
