from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
import json

from stackbridge.core.events import Event


@dataclass
class DeploymentReport:

    service: str

    environment: str

    image: str

    started_at: datetime

    finished_at: datetime | None = None

    duration: float = 0

    success: bool = False

    events: list[Event] = field(default_factory=list)

    def add_event(self, event: Event):

        self.events.append(event)

    def finish(self, success: bool):

        self.finished_at = datetime.utcnow()

        self.success = success

        self.duration = (
            self.finished_at - self.started_at
        ).total_seconds()

    def save(self):

        report_dir = Path(".stackbridge")

        report_dir.mkdir(exist_ok=True)

        output = report_dir / "deployment.json"

        output.write_text(
            json.dumps(
                asdict(self),
                default=str,
                indent=2,
            )
        )
