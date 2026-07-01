
from stackbridge.pipeline.context import DeploymentContext
from stackbridge.pipeline.pipeline import Pipeline
from stackbridge.pipeline.stages.validate import ValidationStage
from stackbridge.core.stages import Stage
from stackbridge.core.logger import get_logger
from stackbridge.core.metrics import Timer
from stackbridge.core.kubernetes import check_cluster
from stackbridge.core.validator import validate
from stackbridge.core.config import load_config

from stackbridge.core.docker import build
from stackbridge.core.scanner import scan_image
from stackbridge.core.registry import push

from stackbridge.core.helm import deploy_chart
from stackbridge.core.rollout import wait_rollout
from stackbridge.core.health import check_health

from stackbridge.core.gitops import sync

from stackbridge.core.report import report

logger = get_logger()

def deploy_service(service_name, environment):
    
    logger = get_logger()

    timer = Timer()

    cfg = load_config()

    context = DeploymentContext(
        service_name,
        environment,
    )

    context.logger = logger
    context.timer = timer
    context.config = cfg

    pipeline = Pipeline([
    ValidationStage(),
    ])

    pipeline.run(context)

    logger.stage(Stage.CLUSTER.value)
    check_cluster()
    logger.success("Kubernetes cluster reachable")

    logger.stage(Stage.BUILD.value)
    image = build(service_name)
    logger.success("Docker image built")

    logger.stage(Stage.SCAN.value)
    scan_image(image)
    logger.success("Image scan completed")

    logger.stage(Stage.PUSH.value)
    push(image)
    logger.success("Image pushed")

    logger.stage(Stage.DEPLOY.value)

    deploy_chart(
        service_name,
        environment,
        image,
    ) 

    logger.success("Helm deployment completed")

    logger.stage(Stage.ROLLOUT.value)
    wait_rollout(service_name, environment)
    logger.success("Rollout completed")

    logger.stage(Stage.HEALTH.value)
    check_health(service_name)
    logger.success("Health checks passed")

    if cfg["gitops"]["enabled"]:
        logger.stage(Stage.GITOPS.value)
        sync(service_name)
        logger.success("GitOps synchronized")

    logger.stage(Stage.REPORT.value)
    report(service_name, image)
    logger.stage(Stage.REPORT.value)

    report(service_name, image)

    logger.success("Deployment report generated")    

    logger.success("Deployment successful")

    logger.success(
    f"Deployment completed in {timer.elapsed()} seconds"
    )
