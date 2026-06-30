
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
