from pathlib import Path
import yaml

CATALOG = (
    Path(__file__)
    .resolve()
    .parent
    / "services.yaml"
)


def load_catalog():
    with open(CATALOG) as f:
        return yaml.safe_load(f)
