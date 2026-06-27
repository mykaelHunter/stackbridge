from pathlib import Path
import yaml

CATALOG_FILE = Path("catalog/services.yaml")

def load_catalog():

    if not CATALOG_FILE.exists():
        raise FileNotFoundError(
            f"{CATALOG_FILE} not found"
        )

    with open(CATALOG_FILE) as f:
        return yaml.safe_load(f)
