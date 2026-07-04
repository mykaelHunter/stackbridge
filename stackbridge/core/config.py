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

def get_registry():
    """Return the `registry` section of stackbridge.yaml (empty dict if absent)."""
    cfg = load_config()
    return cfg.get("registry", {})


def get_namespace(environment):
    """Resolve the Kubernetes namespace for a given environment name,
    per the `environments` section of stackbridge.yaml. Falls back to
    the environment name itself if it isn't listed there (e.g. dev
    and staging namespaces match their environment name by
    convention, but prod maps to 'production' — this must be looked
    up rather than assumed, or deploy and rollout will silently
    target the wrong namespace)."""
    cfg = load_config()
    env_cfg = cfg.get("environments", {}).get(environment, {})
    return env_cfg.get("namespace", environment)
