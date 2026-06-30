from enum import Enum


class DeploymentEvent(str, Enum):

    VALIDATION = "validation"

    BUILD = "build"

    SCAN = "scan"

    PUSH = "push"

    DEPLOY = "deploy"

    ROLLOUT = "rollout"

    HEALTH = "health"

    REPORT = "report"
