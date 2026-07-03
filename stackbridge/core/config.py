import os
import yaml


def load_config():

    with open("stackbridge.yaml") as f:
        cfg = yaml.safe_load(f)

    slack_webhook = os.getenv("SLACK_WEBHOOK")

    if slack_webhook:
        cfg.setdefault("notifications", {})
        cfg["notifications"].setdefault("slack", {})
        cfg["notifications"]["slack"]["webhook"] = slack_webhook

    return cfg
