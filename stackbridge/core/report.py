import click


def report(service, image):

    click.echo()
    click.echo("Deployment Summary")
    click.echo("------------------")
    click.echo(f"Service : {service}")
    click.echo(f"Image   : {image}")
    click.echo("Status  : SUCCESS")
