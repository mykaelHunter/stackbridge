from dataclasses import dataclass
from enum import Enum
from datetime import datetime


class DeploymentEvent(str, Enum):

    VALIDATION = "validation"
    CLUSTER = "cluster"

    BUILD = "build"

    SCAN = "scan"

    PUSH = "push"

    DEPLOY = "deploy"

    ROLLOUT = "rollout"

    HEALTH = "health"

    GITOPS = "gitops"

    REPORT = "report"

@dataclass
class Event:

    type: DeploymentEvent

    service: str

    status: str

    message: str

    timestamp: datetime = datetime.utcnow()
