from pathlib import Path
import yaml


def load_catalog():
    catalog_file = (
        Path(__file__).parent.parent
        / "catalog"
        / "services.yaml"
    )

    if not catalog_file.exists():
        raise FileNotFoundError(
            f"Catalog file not found: {catalog_file}"
        )

    with open(catalog_file, "r") as f:
        return yaml.safe_load(f)
