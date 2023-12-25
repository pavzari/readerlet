from pathlib import Path
from typing import Union
from urllib.parse import urljoin, urlparse

import click
import requests
from bs4 import BeautifulSoup


class Article:
    def __init__(self, url, title, byline, content, text_content):
        self.url = url
        self.title = title
        self.byline = byline
        self.content = content
        self.text_content = text_content
        self.images = []

    def strip_hyperlinks(self) -> None:
        """Strip <a> tag attributes but keep the tags and content."""
        soup = BeautifulSoup(self.content, "html.parser")
        for a in soup.find_all("a"):
            for attrb in list(a.attrs.keys()):
                del a[attrb]
        self.content = str(soup)

    def strip_images(self) -> None:
        """Strip all image-related elements from the content."""
        tags_to_remove = ["img", "figure", "picture"]
        soup = BeautifulSoup(self.content, "html.parser")
        for tag in soup.find_all(tags_to_remove):
            tag.decompose()
        self.content = str(soup)

    @staticmethod
    def download_image(url: str, temp_dir: Path) -> Union[Path, None]:
        response = requests.get(url, stream=True, timeout=10)
        if response.status_code == 200:
            filename = temp_dir / Path(urlparse(url).path).name
            with open(filename, "wb") as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)
            return filename
        return None

    @staticmethod
    def check_mediatype(name: str) -> str:
        """Check image extension and return mimetype."""
        ext = name.split(".")[-1].lower()

        extension_to_mimetype = {
            "png": "image/png",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "gif": "image/gif",
            "svg": "image/svg+xml",
        }
        # Unsupported on Kindle:
        # "webp": "image/webp"

        if ext in extension_to_mimetype:
            return extension_to_mimetype[ext]
        else:
            raise ValueError(f"Image format {ext} is not supported.")

    def extract_images(self, temp_dir: Path) -> None:
        """Download images and replace src with a local path."""
        soup = BeautifulSoup(self.content, "html.parser")

        for img_tag in soup.find_all("img"):
            src = img_tag.get("src")
            if src:
                absolute_url = urljoin(self.url, src)
                image_path = self.download_image(absolute_url, temp_dir)
                if image_path:
                    try:
                        mimetype = self.check_mediatype(Path(image_path).name)
                    except ValueError as e:
                        click.echo(f"{e}. Skipping {absolute_url}")
                        continue
                    # TODO:
                    # html rendering issues if image name contains %!
                    img_tag["src"] = str(image_path)
                    image_name = Path(image_path).name
                    self.images.append(tuple(image_name, mimetype))
                    click.echo(
                        f"Downloaded and replaced: {absolute_url} -> {image_path}"
                    )
                else:
                    img_tag.decompose()
                    click.echo(f"Failed to download image: {absolute_url}")
        self.content = str(soup)
