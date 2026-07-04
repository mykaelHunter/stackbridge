
from stackbridge.pipeline.context import PipelineContext
from stackbridge.pipeline.pipeline import Pipeline
from stackbridge.pipeline.stages.validate import ValidationStage
from stackbridge.core.stages import Stage
from stackbridge.core.logger import get_logger
from stackbridge.pipeline.context import PipelineContext
from stackbridge.pipeline.pipeline import Pipeline

from stackbridge.pipeline.stages.validate import ValidationStage
from stackbridge.pipeline.stages.cluster import ClusterStage
from stackbridge.pipeline.stages.build import BuildStage
from stackbridge.pipeline.stages.scan import ScanStage
from stackbridge.pipeline.stages.push import PushStage
from stackbridge.pipeline.stages.deploy import DeployStage
from stackbridge.pipeline.stages.rollout import RolloutStage
from stackbridge.pipeline.stages.health import HealthStage
from stackbridge.pipeline.stages.gitops import GitOpsStage
from stackbridge.pipeline.stages.report import ReportStage
from stackbridge.pipeline.stages.notify import NotifyStage

from stackbridge.core.config import load_config
from stackbridge.core.report import DeploymentReport

def deploy_service(service_name, environment):

    context = PipelineContext(
        service=service_name,
        environment=environment,
    )

    context.config = load_config()

    context.report = DeploymentReport(
        service=service_name,
        environment=environment,
        image="",
        started_at=context.started_at,
    )

    pipeline = Pipeline([
        ValidationStage(),
        ClusterStage(),
        BuildStage(),
        ScanStage(),
        PushStage(),
        DeployStage(),
        RolloutStage(),
        HealthStage(),
        GitOpsStage(),
        ReportStage(),
        NotifyStage(),
    ])

    pipeline.execute(context)

