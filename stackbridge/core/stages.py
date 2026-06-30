from enum import Enum


class Stage(str, Enum):

    VALIDATION = "Validate Service"

    CLUSTER = "Check Kubernetes"

    BUILD = "Build Docker Image"

    SCAN = "Security Scan"

    PUSH = "Push Image"

    DEPLOY = "Deploy Helm Chart"

    ROLLOUT = "Wait Rollout"

    HEALTH = "Health Check"

    GITOPS = "GitOps Sync"

    REPORT = "Deployment Report"
