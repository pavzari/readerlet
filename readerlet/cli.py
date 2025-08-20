import json
import os
import re
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
            title = (
                article_data["title"]
                if article_data["title"] is not None
                else urlparse(url).netloc
            )
            byline = (
                article_data["byline"]
                if article_data["byline"] is not None
                else urlparse(url).netloc
            )
            lang = (
                article_data["lang"]
                if article_data["lang"] and article_data["lang"].strip()
                else "en"
            )
            content = article_data.get("content")
            text_content = re.sub(r"\s+", " ", article_data.get("textContent", ""))
            # TODO: date
            if not content:
                raise click.ClickException("Content not extracted.")
            return Article(url, title, byline, lang, content, text_content)
    except subprocess.CalledProcessError:
        raise click.ClickException("Failed to extract article.")


@click.group()
@click.version_option()
def cli() -> None:
    """
    readerlet.
    """
    pass


@cli.command()
@click.argument(
    "source",
    required=True,
    type=str,
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
def send(source: str, remove_hyperlinks: bool, remove_images: bool) -> None:
    """Send content to Kindle.

    SOURCE: URL or a path to a local file.

    If a file path, sends it to Kindle.
    If a URL, extracts and sends web content to Kindle."""

    SUPPORTED_KINDLE_TYPES = [
        ".doc",
        ".docx",
        ".html",
        ".htm",
        ".rtf",
        ".txt",
        ".jpeg",
        ".jpg",
        ".gif",
        ".png",
        ".bmp",
        ".pdf",
        ".epub",
    ]

    def send_logic(file_path: Path, author: str, title: str, file_format: str):
        config_file = "kindle_config.json"
        cfg = Path(click.get_app_dir("readerlet"), config_file)

        try:
            click.echo("Sending to Kindle...")
            kindle_send(file_path, author, title, format=file_format, config=cfg)
            click.secho("Sent.", fg="green")
        except (FileNotFoundError, json.JSONDecodeError, APIError) as e:
            if isinstance(e, (FileNotFoundError, json.JSONDecodeError)):
                click.secho(
                    "Kindle configuration not found or corrupt. Please log in.",
                    fg="yellow",
                )
            else:  # APIError
                click.secho("Authentication expired. Please log in again.", fg="yellow")

            _perform_kindle_login_logic()
            click.echo("Retrying send...")
            kindle_send(file_path, author, title, format=file_format, config=cfg)
            click.secho("Sent.", fg="green")

    if Path(source).is_file():
        if remove_hyperlinks or remove_images:
            raise click.UsageError("Flags -i and -h cannot be used with a file path.")

        file_extension = Path(source).suffix
        if not file_extension:
            raise click.ClickException("File must have an extension.")

        if file_extension not in SUPPORTED_KINDLE_TYPES:
            raise click.ClickException(f"Unsupported file extension: {file_extension}")

        # Stk api will reject the file if either the author or title is missing.
        # Use the file name for both when sending a local file.
        file_name = Path(source).stem

        send_logic(
            Path(source),
            author=file_name,
            title=file_name,
            file_format=file_extension[1:],
        )

    else:
        install_npm_packages()
        article = extract_content(source)

        if remove_hyperlinks:
            article.remove_hyperlinks()

        if remove_images:
            article.remove_images()

        epub_path = None
        try:
            click.echo("Creating EPUB...")
            epub_path = create_epub(
                article,
                str(Path(__file__).parent.resolve()),
                remove_images,
                for_kindle=True,
            )
            send_logic(epub_path, article.byline, article.title, file_format="EPUB")
        finally:
            if epub_path:
                epub_path.unlink(missing_ok=True)


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
    """Extract and format web content, save as EPUB or print to stdout."""

    install_npm_packages()
    article = extract_content(url)

    if remove_hyperlinks:
        article.remove_hyperlinks()

    if remove_images:
        article.remove_images()

    if output_epub:
        click.echo("Creating EPUB...")
        epub_path = create_epub(article, output_epub, remove_images, for_kindle=False)
        click.secho(f"EPUB created: {epub_path}", fg="green")

    if stdout == "html":
        c = BeautifulSoup(article.content, "html.parser")
        click.echo(str(c))

    elif stdout == "text":
        click.echo(article.text_content)


def _perform_kindle_login_logic() -> None:
    """Core logic for Kindle OAuth2 authentication."""
    config_file = "kindle_config.json"
    config_dir = Path(click.get_app_dir("readerlet"))
    config_dir.mkdir(parents=True, exist_ok=True)
    cfg = config_dir / config_file

    auth = stkclient.OAuth2()
    signin_url = auth.get_signin_url()
    click.echo(
        f"\nSign in to authorize the application with Amazon's Send-to-Kindle service:\n\n{signin_url}"
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
            click.echo(f"Credentials saved to: {cfg}.")
            break
        except (EOFError, KeyboardInterrupt):
            raise click.ClickException("Authentication cancelled.")
        except Exception as e:
            raise click.ClickException(f"Error during authentication: {e}")


@cli.command()
def kindle_login() -> None:
    """Configure OAuth2 authentication with Amazon's Send-to-Kindle service."""
    _perform_kindle_login_logic()


def kindle_send(
    filepath: Path, author: str, title: str, format: str, config: Path
) -> None:
    """Send EPUB to Kindle via the send to kindle client."""

    # Tracks whether an error occurred before or during file sending using `before_sending`.
    # stkclient raises the same APIError for expired tokens and file sending errors.
    before_sending = True

    try:
        with open(config) as f:
            client = stkclient.Client.load(f)
        devices = client.get_owned_devices()
        destinations = [d.device_serial_number for d in devices]
        before_sending = False
        client.send_file(
            filepath, destinations, author=author, title=title, format=format
        )
    except APIError:
        if before_sending:
            raise
        else:
            raise click.ClickException(
                "Failed to send file. Check the file format and content."
            )
