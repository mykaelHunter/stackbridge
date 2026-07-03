import subprocess
from pathlib import Path

from stackbridge.core.config import get_registry
from stackbridge.core.paths import REPO_ROOT


def build(service_name):

    registry = get_registry()

    server = registry.get("server", "docker.io")
    organization = registry.get("organization", "mykaelhunter")
    tag = registry.get("tag", "latest")

    image = f"{server}/{organization}/{service_name}:{tag}"

    # Resolved path — same fix as elsewhere. `docker build` was
    # previously given a path relative to wherever the CLI was
    # invoked from, which silently pointed at the wrong directory
    # (or nothing at all) unless run from the repo root.
    build_context = REPO_ROOT / "services" / service_name

    subprocess.run(
        [
            "docker",
            "build",
            "-t",
            image,
            str(build_context),
        ],
        check=True,
    )

    return image
