import click
from pathlib import Path

from stackbridge.core.scaffold import render
from stackbridge.core.paths import REPO_ROOT


@click.command(name="scaffold")
@click.argument("service_name")
def scaffold(service_name):
    """
    Bootstrap a new service from StackBridge templates.

    For the 'stackbridge' service, the three application source
    files (app.py, Dockerfile, requirements.txt) are pulled from
    the repo root app/ directory rather than the generic stubs —
    they carry the same security fixes as the production application
    (non-root container, no hardcoded credentials, gunicorn, etc).

    All services receive a chaos/ directory pre-populated with the
    four Phase 4 experiments, rendered with the service name so
    each manifest targets the correct service and can be applied
    directly with kubectl.

    NOTE: this command does NOT populate eso/ (the External Secrets
    Operator manifests). Those are rendered by Terraform itself —
    see infra/modules/eso-manifests — because they need the IRSA
    role ARN that only exists after `terraform apply`. Run apply
    for the target environment before `kubectl apply -f eso/`.
    """

    root = REPO_ROOT / "services" / service_name

    already_existed = root.exists()
    if already_existed:
        click.echo(
            f"Service '{service_name}' already exists — "
            f"checking for missing files to backfill..."
        )

    # --------------------------------------------------
    # Create directory structure
    # --------------------------------------------------

    directories = [
        "app",
        "k8s",
        "helm",
        "helm/templates",
        "argocd",
        "chaos",
        "eso",
        ".github/workflows",
    ]

    for directory in directories:
        (root / directory).mkdir(parents=True, exist_ok=True)

    # --------------------------------------------------
    # Template variables
    # --------------------------------------------------

    values = {
        "SERVICE_NAME": service_name,
        "PORT": 8000,
        "IMAGE_REPOSITORY": "{{IMAGE_REPOSITORY}}",
        "IMAGE_TAG": "{{IMAGE_TAG}}",
        "REPO_URL": "https://github.com/mykaelHunter/stackbridge.git",
        # NAMESPACE is deliberately left unrendered here (see the
        # {{NAMESPACE}} placeholder surviving render() below) — chaos
        # manifests can run against any environment's namespace
        # (dev/staging/prod), so the real value is substituted at
        # `stackbridge service chaos run --env ...` time, not baked
        # in once at scaffold time. See core/chaos.py.
    }

    # --------------------------------------------------
    # Application source selection
    # --------------------------------------------------
    # For the 'stackbridge' service the real production files in
    # app/ are used as the template source instead of the generic
    # stubs. This ensures the scaffolded service has identical
    # source to what is deployed, including the DB connection fix
    # (context manager, no fallback password, explicit column
    # lists) and the Dockerfile security fixes from the audit.
    #
    # The generic stubs are still used for all other services so
    # they start from a working baseline they can customise.

    TPLS = REPO_ROOT / "stackbridge/templates"
    real_app = REPO_ROOT / "app"
    use_real_app = (service_name == "stackbridge" and real_app.exists())

    if use_real_app:
        click.echo("  Using production app/ source files for stackbridge service.")
        app_py_src      = real_app / "app.py"
        dockerfile_src  = real_app / "Dockerfile"
        requirements_src = real_app / "requirements.txt"
        gunicorn_conf_src = real_app / "gunicorn.conf.py"
    else:
        app_py_src      = TPLS / "app.py.tpl"
        dockerfile_src  = TPLS / "Dockerfile.tpl"
        requirements_src = TPLS / "requirements.txt.tpl"
        gunicorn_conf_src = TPLS / "gunicorn.conf.py.tpl"

    # --------------------------------------------------
    # Template mapping
    # --------------------------------------------------

    files = {
        # ── Application ──────────────────────────────────────
        "app/app.py":           app_py_src,
        "app/requirements.txt": requirements_src,
        "app/Dockerfile":       dockerfile_src,
        "app/gunicorn.conf.py": gunicorn_conf_src,

        # ── Documentation ────────────────────────────────────
        "README.md":            TPLS / "README.md.tpl",

        # ── Kubernetes manifests ──────────────────────────────
        "k8s/deployment.yaml":  TPLS / "deployment.yaml.tpl",
        "k8s/service.yaml":     TPLS / "service.yaml.tpl",
        "k8s/ingress.yaml":     TPLS / "ingress.yaml.tpl",
        "k8s/configmap.yaml":   TPLS / "configmap.yaml.tpl",

        # ── Helm chart ────────────────────────────────────────
        "helm/Chart.yaml":                      TPLS / "helm/Chart.yaml.tpl",
        "helm/values.yaml":                     TPLS / "helm/values.yaml.tpl",
        "helm/templates/deployment.yaml":       TPLS / "helm/templates/deployment.yaml.tpl",
        "helm/templates/service.yaml":          TPLS / "helm/templates/service.yaml.tpl",
        "helm/templates/ingress.yaml":          TPLS / "helm/templates/ingress.yaml.tpl",
        "helm/templates/configmap.yaml":        TPLS / "helm/templates/configmap.yaml.tpl",
        "helm/templates/servicemonitor.yaml":   TPLS / "helm/templates/servicemonitor.yaml.tpl",

        # ── ArgoCD ───────────────────────────────────────────
        "argocd/application.yaml":  TPLS / "argocd/application.yaml.tpl",

        # ── CI/CD ─────────────────────────────────────────────
        ".github/workflows/deploy.yaml": TPLS / "github/deploy.yaml.tpl",

        # ── Chaos experiments ─────────────────────────────────
        # Derived from chaos/ manifests in the repo root.
        # Rendered with SERVICE_NAME so each experiment targets
        # the correct service. Ready to kubectl apply immediately.
        "chaos/cpu-stress.yaml":      TPLS / "chaos/cpu-stress.yaml.tpl",
        "chaos/pod-kill.yaml":        TPLS / "chaos/pod-kill.yaml.tpl",
        "chaos/az-failure.yaml":      TPLS / "chaos/az-failure.yaml.tpl",
        "chaos/network-latency.yaml": TPLS / "chaos/network-latency.yaml.tpl",
    }

    # --------------------------------------------------
    # Render and write
    # --------------------------------------------------

    for output, source in files.items():

        target = root / output

        if target.exists():
            click.echo(f"  ✓ Exists: {output}")
            continue

        source_path = Path(source)

        if not source_path.exists():
            raise FileNotFoundError(f"Missing source file: {source_path}")

        content = render(source_path, values)

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        click.echo(f"  Generated {output}")

    if already_existed:
        click.echo(f"\n✓ Backfilled missing files for {service_name}")
    else:
        click.echo(f"\n✓ Bootstrapped {service_name}")
