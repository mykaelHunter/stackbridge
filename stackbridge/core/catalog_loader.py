from pathlib import Path
import yaml

from stackbridge.core.paths import REPO_ROOT


def load_catalog():
    # Resolved via the shared repo-root finder, not a __file__
    # relative climb — same bug class as core/terraform.py,
    # core/config.py, core/docker.py, core/helm.py,
    # core/validator.py, and commands/scaffold.py. This one
    # was missed in that earlier sweep because the static import
    # check only verified that imports resolved, not that every
    # path-construction pattern in every file was safe — it
    # didn't grep for __file__ usage specifically. Confirmed via
    # full grep this time: this was the only remaining instance.
    catalog_file = REPO_ROOT / "stackbridge" / "catalog" / "services.yaml"

    if not catalog_file.exists():
        raise FileNotFoundError(
            f"Catalog file not found: {catalog_file}"
        )

    with open(catalog_file, "r") as f:
        return yaml.safe_load(f)
