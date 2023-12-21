import os
import click
import json
import subprocess
import stkclient
from readerlet.article import Article
from urllib.parse import urlparse


def check_node_installed() -> bool:
    # node version constraints?
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
            click.echo("Installing required npm packages...")
            try:
                subprocess.run(
                    ["npm", "install"],
                    cwd=javascript_dir,
                    capture_output=True,
                    check=True,
                )
                click.echo("Npm install completed successfully.")
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
            title = article_data.get("title", "No Title")
            byline = article_data.get("byline", f"{urlparse(url).netloc}")
            content = article_data.get("content", "")
            text_content = article_data.get("textContent", "")
            return Article(url, title, byline, content, text_content)

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
@click.argument("url", required=True)
@click.option(
    "--output-epub",
    "-e",
    type=click.Path(),
    help="Output EPUB file to the specified path.",
)
@click.option(
    "--send-to-kindle",
    "-k",
    is_flag=True,
    help="Send EPUB to Kindle if outputting to EPUB.",
)
@click.option(
    "--strip-hyperlinks",
    "-s",
    is_flag=True,
    default=False,
    help="Remove hyperlinks from the content.",
)
@click.option(
    "--strip-images",
    "-i",
    is_flag=True,
    default=False,
    help="Remove images from the content.",
)
@click.option(
    "--output-pdf",
    "-p",
    type=click.Path(),
    help="Output PDF file to the specified path.",
)
@click.option(
    "--output-markdown",
    "-m",
    type=click.Path(),
    help="Output Markdown file to the specified path.",
)
@click.option(
    "--stdout",
    "-o",
    type=click.Choice(["html", "text"]),
    help="Specify the output format (html or text without html). If used, content will be printed to stdout.",
)
def extract(
    url,
    output_epub,
    send_to_kindle,
    strip_hyperlinks,
    strip_images,
    output_pdf,
    output_markdown,
    stdout,
):
    """
    Extract and format a web content.
    """
    install_npm_packages()
    article = extract_content(url)
    article.extract_images()

    article.strip_hyperlinks() if strip_hyperlinks else None
    article.strip_images() if strip_images else None

    if output_epub:
        pass

        if send_to_kindle:
            pass

    if output_pdf:
        raise click.ClickException("Not implemented.")
    if output_markdown:
        raise click.ClickException("Not implemented.")
    if stdout == "html":
        click.echo(article.content)
    elif stdout == "text":
        click.echo(article.text_content)


@cli.command()
def kindle_auth():
    """
    Configure authentication with Kindle service on Amazon.
    """
    config_file = "kindle_config.json"
    cfg = os.path.join(click.get_app_dir("readerlet"), config_file)

    if os.path.exists(cfg):
        override_current = click.confirm(
            f"A credentials file '{cfg}' already exists. Do you want to override it?",
            default=False,
        )
        if not override_current:
            click.echo("Authentication canceled.")
            return

    auth = stkclient.OAuth2()
    signin_url = auth.get_signin_url()
    click.echo(
        f"\nPlease go to the following URL to sign in and authorize the application with Amazon's Kindle service:\n\n{signin_url}"
    )

    while True:
        try:
            redirect_url = input(
                "\nPaste the redirect URL from the authorization page:\n"
            )
            client = auth.create_client(redirect_url)
            click.echo(f"Authentication successful. Client details:\n{client}")

            with open(cfg, "w") as f:
                client.dump(f)

            click.echo(f"Authentication details saved to {cfg}.")
        except (EOFError, KeyboardInterrupt):
            break
        except Exception as e:
            click.echo(f"Error during authentication: {e}")


# # f = open("article.html", "w")
# # f.write(article.content)
# # f.close()
