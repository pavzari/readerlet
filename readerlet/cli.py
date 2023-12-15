import click


@click.command()
@click.version_option()
@click.argument("arg")
def cli(arg):
    click.echo(f"Argument: {arg}!")
