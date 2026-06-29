from pathlib import Path
import yaml

CONFIG_FILE = Path("stackbridge.yaml")


def load_config():

    if not CONFIG_FILE.exists():
        raise FileNotFoundError(
            "stackbridge.yaml not found"
        )

    with CONFIG_FILE.open() as f:
        return yaml.safe_load(f)
