import json
import os
import subprocess
from pathlib import Path
from urllib.parse import urlparse

import click
import stkclient
from bs4 import BeautifulSoup
from stkclient.api import APIError

from readerlet.article import Article
from readerlet.epub import create_epub


def check_node_installed() -> bool:
    try:
        subprocess.run(
            ["node", "--version"],
            check=True,
            capture_output=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def install_npm_packages() -> None:
    if check_node_installed():
        current_dir = os.path.dirname(os.path.abspath(__file__))
        javascript_dir = os.path.join(current_dir, "js")
        node_modules_dir = os.path.join(javascript_dir, "node_modules")

        if not os.path.exists(node_modules_dir):
            click.echo("Installing npm packages...")
            try:
                subprocess.run(
                    ["npm", "install"],
                    cwd=javascript_dir,
                    capture_output=True,
                    check=True,
                )
                click.echo("Npm install completed.")
            except subprocess.CalledProcessError:
                raise click.ClickException("Failed to install npm packages.")
    else:
        raise click.ClickException("Node.js runtime not found.")


def extract_content(url: str) -> Article:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    js_script_path = os.path.join(current_dir, "js", "extract_stdout.js")

    try:
        readability = subprocess.run(
            ["node", js_script_path, url],
            capture_output=True,
            text=True,
            check=True,
        )
        article_data = json.loads(readability.stdout)

        if article_data:
            title = article_data.get("title", f"{urlparse(url).netloc}")
            byline = article_data.get("byline", f"{urlparse(url).netloc}")
            lang = article_data.get("lang", "")
            content = article_data.get("content", "")
            text_content = article_data.get("textContent", "")
            if not content:
                raise click.ClickException("Content not extracted.")
            return Article(url, title, byline, lang, content, text_content)
    except subprocess.CalledProcessError:
        raise click.ClickException("Error extracting article.")


@click.group()
@click.version_option()
def cli():
    """
    readerlet.
    """
    pass


@cli.command()
@click.argument("url", required=True, type=str)
@click.option(
    "--remove-hyperlinks",
    "-h",
    is_flag=True,
    default=False,
    help="Remove hyperlinks from content.",
)
@click.option(
    "--remove-images",
    "-i",
    is_flag=True,
    default=False,
    help="Remove image-related elements from content.",
)
def send(url: str, remove_hyperlinks: bool, remove_images: bool) -> None:
    """Extract web content as EPUB and send to Kindle."""

    install_npm_packages()
    article = extract_content(url)

    if remove_hyperlinks:
        article.remove_hyperlinks()

    if remove_images:
        article.remove_images()

    try:
        click.echo("Creating EPUB...")
        epub_path = create_epub(
            article, str(Path(__file__).parent.resolve()), remove_images
        )
        click.echo("Sending to Kindle...")
        kindle_send(epub_path, article.byline, article.title)
        click.secho("EPUB sent.", fg="green")
    finally:
        if epub_path.exists():
            epub_path.unlink()


@cli.command()
@click.argument("url", required=True, type=str)
@click.option(
    "--output-epub",
    "-e",
    type=click.Path(exists=True, dir_okay=True, resolve_path=True),
    help="Save EPUB to disk. Output directory for the EPUB file.",
)
@click.option(
    "--remove-hyperlinks",
    "-h",
    is_flag=True,
    default=False,
    help="Remove hyperlinks from content.",
)
@click.option(
    "--remove-images",
    "-i",
    is_flag=True,
    default=False,
    help="Remove image-related elements from content.",
)
@click.option(
    "--stdout",
    "-o",
    type=click.Choice(["html", "text"]),
    help="Print content to stdout. Specify the output format (html or text without html).",
)
def extract(
    url: str,
    output_epub: str,
    remove_hyperlinks: bool,
    remove_images: bool,
    stdout: bool,
) -> None:
    """Extract and format a web content, save as EPUB or print to stdout."""

    install_npm_packages()
    article = extract_content(url)

    if remove_hyperlinks:
        article.remove_hyperlinks()

    if remove_images:
        article.remove_images()

    if output_epub:
        click.echo("Creating EPUB...")
        epub_path = create_epub(article, output_epub, remove_images)
        click.secho(f"EPUB file created: {epub_path}", fg="green")

    if stdout == "html":
        c = BeautifulSoup(article.content, "html.parser")
        click.echo(str(c))

    # TODO:
    # newlines and whitespace.
    # add title.
    elif stdout == "text":
        click.echo(article.text_content)


@cli.command()
def kindle_login() -> None:
    """Configure OAuth2 authentication with Amazon's Send-to-Kindle service."""

    config_file = "kindle_config.json"
    config_dir = Path(click.get_app_dir("readerlet"))
    config_dir.mkdir(parents=True, exist_ok=True)
    cfg = config_dir / config_file

    auth = stkclient.OAuth2()
    signin_url = auth.get_signin_url()
    click.echo(
        f"\nSign in and authorize the application with Amazon's Send-to-Kindle service:\n\n{signin_url}"
    )

    while True:
        try:
            redirect_url = input(
                "\nPaste the redirect URL from the authorization page:\n"
            )
            client = auth.create_client(redirect_url)
            with open(cfg, "w") as f:
                client.dump(f)
            click.secho("Authentication successful.", fg="green")
            click.echo(f"Authentication details saved to: {cfg}.")
            break
        except (EOFError, KeyboardInterrupt):
            break
        except Exception as e:
            click.echo(f"Error during authentication: {e}")
            break


def kindle_send(filepath: Path, author: str, title: str, format: str = "EPUB") -> None:
    """Send EPUB to Kindle."""

    config_file = "kindle_config.json"
    cfg = Path(click.get_app_dir("readerlet"), config_file)

    if not cfg.exists():
        raise click.ClickException(
            "Kindle configuration file not found. Use 'readerlet kindle-login'."
        )
    try:
        with open(cfg) as f:
            client = stkclient.Client.load(f)
        devices = client.get_owned_devices()
        destinations = [d.device_serial_number for d in devices]
        client.send_file(
            filepath, destinations, author=author, title=title, format=format
        )
    except APIError:
        # token expiration?
        raise click.ClickException("Authenticate error. Use 'readerlet kindle-login'.")
    except json.JSONDecodeError:
        raise click.ClickException(f"Error: File '{cfg}' is not a valid JSON file.")
    except Exception as e:
        raise click.ClickException(f"Error: {e}")
