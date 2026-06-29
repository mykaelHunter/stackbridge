from pathlib import Path
import yaml


def update(service, tag):

    values = (
        Path("services")
        / service
        / "helm"
        / "values.yaml"
    )

    with values.open() as f:
        data = yaml.safe_load(f)

    data["image"]["tag"] = tag

    with values.open("w") as f:
        yaml.safe_dump(data, f)
