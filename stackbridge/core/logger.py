import click


class Logger:

    def stage(self, name):
        click.secho(f"\n▶ {name}", fg="cyan", bold=True)

    def info(self, msg):
        click.echo(msg)

    def success(self, msg):
        click.secho(f"✓ {msg}", fg="green")

    def warning(self, msg):
        click.secho(msg, fg="yellow")

    def error(self, msg):
        click.secho(msg, fg="red", bold=True)


logger = Logger()


def get_logger():
    return logger
