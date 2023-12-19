import os
import click
import json
import subprocess
from contextlib import chdir
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
            with chdir(javascript_dir):
                try:
                    subprocess.run(
                        ["npm", "install"],
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    click.echo("npm install completed successfully.")
                except subprocess.CalledProcessError:
                    raise click.ClickException("Error running npm install.")
    else:
        raise click.ClickException("Node.js is not installed.")


def extract_content(url: str) -> Article:
    try:
        readability = subprocess.run(
            ["node", "js/extract_stdout.js", url],
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


@click.command()
@click.version_option()
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
def cli(
    url,
    output_epub,
    send_to_kindle,
    strip_hyperlinks,
    strip_images,
    output_pdf,
    output_markdown,
    stdout,
):
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


# # f = open("article.html", "w")
# # f.write(article.content)
# # f.close()
