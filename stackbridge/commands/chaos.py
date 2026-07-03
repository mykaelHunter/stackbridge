import click

from stackbridge.core.chaos import (
    EXPERIMENTS,
    ChaosError,
    list_experiments,
    run_experiment,
    cleanup_experiment,
)


@click.group(name="chaos")
def chaos():
    """Run chaos engineering experiments against a scaffolded service."""
    pass


@chaos.command(name="list")
@click.argument("service_name")
def list_cmd(service_name):
    """List chaos experiments available for a service."""
    experiments = list_experiments(service_name)

    if not experiments:
        click.echo(
            f"No chaos manifests found for '{service_name}'. "
            f"Run `stackbridge service scaffold {service_name}` first."
        )
        return

    click.echo(f"Available experiments for {service_name}:")
    for exp in experiments:
        click.echo(f"  - {exp}")


@chaos.command(name="run")
@click.argument("service_name")
@click.argument("experiment", type=click.Choice(EXPERIMENTS))
@click.option(
    "--follow/--no-follow",
    default=True,
    help="Tail the experiment pod's logs until it completes (default: on).",
)
def run_cmd(service_name, experiment, follow):
    """Apply a chaos experiment manifest and optionally follow its logs."""
    try:
        run_experiment(service_name, experiment, follow=follow)
    except ChaosError as e:
        click.echo(f"Failed: {e}", err=True)
        raise SystemExit(1)


@chaos.command(name="clean")
@click.argument("service_name")
@click.argument("experiment", type=click.Choice(EXPERIMENTS))
def clean_cmd(service_name, experiment):
    """Delete a chaos experiment's Pod from the cluster."""
    try:
        cleanup_experiment(service_name, experiment)
    except ChaosError as e:
        click.echo(f"Failed: {e}", err=True)
        raise SystemExit(1)
