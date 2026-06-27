from pathlib import Path


def render(template_path, values):
    content = Path(template_path).read_text()

    for k, v in values.items():
        content = content.replace(
            "{{" + k + "}}",
            str(v)
        )

    return content
