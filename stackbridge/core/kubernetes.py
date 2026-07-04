
import shutil
import subprocess


class KubernetesError(Exception):
    pass


class KubectlNotInstalled(KubernetesError):
    pass


class ClusterUnavailable(KubernetesError):
    pass


def check_cluster():

    if shutil.which("kubectl") is None:
        raise KubectlNotInstalled(
            "kubectl is not installed."
        )

    try:

        subprocess.run(
            ["kubectl", "cluster-info"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    except subprocess.CalledProcessError as exc:
        raise ClusterUnavailable(
            "Kubernetes cluster is unreachable."
        ) from exc


def ensure_namespace(namespace):
    """
    Make sure `namespace` exists, creating it if needed.

    Uses `kubectl create namespace --dry-run=client -o yaml | kubectl
    apply -f -` rather than a plain `create`, so this is idempotent —
    safe to call every time instead of only on first setup, and it
    won't error if the namespace is already there.
    """

    try:
        dry_run = subprocess.run(
            ["kubectl", "create", "namespace", namespace,
             "--dry-run=client", "-o", "yaml"],
            check=True,
            capture_output=True,
            text=True,
        )

        subprocess.run(
            ["kubectl", "apply", "-f", "-"],
            input=dry_run.stdout,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        raise KubernetesError(
            f"Failed to ensure namespace '{namespace}' exists: "
            f"{exc.stderr.strip() if exc.stderr else exc}"
        ) from exc


# The chaos-sa ServiceAccount is what every pod-kill and az-failure
# experiment Pod runs as (see chaos/pod-kill.yaml.tpl and
# chaos/az-failure.yaml.tpl — `serviceAccountName: chaos-sa`).
# Permissions needed, one-time, cluster-wide:
#   - pod-kill:   get/list/delete Pods in the chaos namespace
#   - az-failure: get/list/patch Nodes (cordon + taint are both
#                 patches against node spec) — cluster-scoped —
#                 plus get/list on Argo Rollouts in the chaos
#                 namespace, to check rollout recovery.
_CHAOS_RBAC_TEMPLATE = """\
apiVersion: v1
kind: ServiceAccount
metadata:
  name: chaos-sa
  namespace: {namespace}
  labels:
    managed-by: stackbridge-idp
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: stackbridge-chaos-node-access
  labels:
    managed-by: stackbridge-idp
rules:
  - apiGroups: [""]
    resources: ["nodes"]
    verbs: ["get", "list", "patch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: stackbridge-chaos-node-access
  labels:
    managed-by: stackbridge-idp
subjects:
  - kind: ServiceAccount
    name: chaos-sa
    namespace: {namespace}
roleRef:
  kind: ClusterRole
  name: stackbridge-chaos-node-access
  apiGroup: rbac.authorization.k8s.io
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: stackbridge-chaos-namespace-access
  namespace: {namespace}
  labels:
    managed-by: stackbridge-idp
rules:
  - apiGroups: [""]
    resources: ["pods"]
    verbs: ["get", "list", "delete"]
  - apiGroups: ["argoproj.io"]
    resources: ["rollouts"]
    verbs: ["get", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: stackbridge-chaos-namespace-access
  namespace: {namespace}
  labels:
    managed-by: stackbridge-idp
subjects:
  - kind: ServiceAccount
    name: chaos-sa
    namespace: {namespace}
roleRef:
  kind: Role
  name: stackbridge-chaos-namespace-access
  apiGroup: rbac.authorization.k8s.io
"""


def ensure_argo_rollouts_installed():
    """
    Make sure the Argo Rollouts CRDs and controller are installed,
    installing them if needed.

    az-failure experiments check rollout recovery with
    `kubectl get rollouts`, which fails with "the server doesn't
    have a resource type 'rollouts'" if the controller was never
    installed. This checks for the CRD first and only installs
    when it's actually missing, since the controller manifest is
    a large multi-object install — no need to re-apply it on every
    experiment run.
    """

    check = subprocess.run(
        ["kubectl", "get", "crd", "rollouts.argoproj.io"],
        capture_output=True,
        text=True,
    )

    if check.returncode == 0:
        return

    try:
        dry_run = subprocess.run(
            ["kubectl", "create", "namespace", "argo-rollouts",
             "--dry-run=client", "-o", "yaml"],
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["kubectl", "apply", "-f", "-"],
            input=dry_run.stdout,
            check=True,
            capture_output=True,
            text=True,
        )

        subprocess.run(
            [
                "kubectl", "apply",
                "-n", "argo-rollouts",
                "--server-side", "--force-conflicts",
                "-f", "https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        subprocess.run(
            [
                "kubectl", "wait", "--for", "condition=established",
                "--timeout=60s",
                "crd/rollouts.argoproj.io",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        raise KubernetesError(
            "Failed to install Argo Rollouts controller: "
            f"{exc.stderr.strip() if exc.stderr else exc}"
        ) from exc


def ensure_argocd_installed():
    """
    Make sure ArgoCD is installed in the 'argocd' namespace,
    installing it if needed.

    Both `stackbridge service deploy`'s gitops sync (core/gitops.py,
    which shells out to the `argocd` CLI) and every scaffolded
    service's argocd/application.yaml assume a running ArgoCD
    controller already exists. Checking for the argocd-server
    Deployment first (rather than just the namespace, which can
    exist empty) and only installing when it's actually missing,
    since the install manifest is large and this only needs to run
    once per cluster — during `stackbridge environment create`.
    """

    check = subprocess.run(
        ["kubectl", "get", "deployment", "argocd-server", "-n", "argocd"],
        capture_output=True,
        text=True,
    )

    if check.returncode == 0:
        return

    try:
        dry_run = subprocess.run(
            ["kubectl", "create", "namespace", "argocd",
             "--dry-run=client", "-o", "yaml"],
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["kubectl", "apply", "-f", "-"],
            input=dry_run.stdout,
            check=True,
            capture_output=True,
            text=True,
        )

        subprocess.run(
            [
                "kubectl", "apply", "-n", "argocd",
                "--server-side", "--force-conflicts",
                "-f", "https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        subprocess.run(
            [
                "kubectl", "rollout", "status",
                "deployment/argocd-server",
                "-n", "argocd",
                "--timeout=180s",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        raise KubernetesError(
            "Failed to install ArgoCD: "
            f"{exc.stderr.strip() if exc.stderr else exc}"
        ) from exc


def ensure_chaos_rbac(namespace):
    """
    Make sure the chaos-sa ServiceAccount and its RBAC exist in
    `namespace`, creating them if needed.

    Applied via `kubectl apply -f -`, which is itself idempotent —
    safe to call before every experiment run, not just on first
    setup.
    """

    try:
        subprocess.run(
            ["kubectl", "apply", "-f", "-"],
            input=_CHAOS_RBAC_TEMPLATE.format(namespace=namespace),
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        raise KubernetesError(
            f"Failed to ensure chaos-sa RBAC exists in '{namespace}': "
            f"{exc.stderr.strip() if exc.stderr else exc}"
        ) from exc
