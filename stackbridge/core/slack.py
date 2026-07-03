import requests

from stackbridge.core.report import DeploymentReport


class SlackNotifier:

    def __init__(self, webhook):
        self.webhook = webhook

    def send(self, report: DeploymentReport):

        payload = {
            "text": self.build_message(report)
        }

        requests.post(
            self.webhook,
            json=payload,
            timeout=10,
        )

    def build_message(self, report):

        icon = "✅" if report.success else "❌"

        lines = [
            f"{icon} *StackBridge Deployment*",
            "",
            f"*Service:* `{report.service}`",
            f"*Environment:* `{report.environment}`",
            f"*Image:* `{report.image}`",
            f"*Duration:* `{report.duration:.2f}s`",
            "",
            "*Pipeline*",
        ]

        for event in report.events:

            emoji = "✅" if event.status == "SUCCESS" else "❌"

            lines.append(
                f"{emoji} {event.type.value}"
            )

        return "\n".join(lines)
