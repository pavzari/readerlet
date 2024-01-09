import base64
from pathlib import Path
from typing import Tuple, Union
from urllib.parse import unquote, urljoin, urlparse
from uuid import uuid4

import click
import requests
from bs4 import BeautifulSoup
from PIL import Image


class Article:
    def __init__(
        self,
        url: str,
        title: str,
        byline: str,
        lang: str,
        content: str,
        text_content: str,
    ):
        self.url = url
        self.title = title
        self.byline = byline
        self.lang = lang
        self.content = content
        self.text_content = text_content
        self.images = []

    def remove_hyperlinks(self) -> None:
        """Strip <a> tag attributes - keep the tags and content."""
        soup = BeautifulSoup(self.content, "html.parser")
        for a in soup.find_all("a"):
            for attrb in list(a.attrs.keys()):
                del a[attrb]
        self.content = str(soup)

    def remove_images(self) -> None:
        """Strip all image-related elements from content."""
        tags_to_remove = ["img", "figure", "picture"]
        soup = BeautifulSoup(self.content, "html.parser")
        for tag in soup.find_all(tags_to_remove):
            tag.decompose()
        self.content = str(soup)

    @staticmethod
    def download_image(url: str, temp_dir: Path) -> Union[Tuple[Path, str], None]:
        """Download image. Return downloaded image path and extension."""
        try:
            if "data:image" in url and "base64" in url:
                mimetype = url.split(":")[1].split(";")[0]
                extension = mimetype.split("/")[1]
                url = url.split("base64,")[1]
                data = base64.b64decode(url)
                image_path = temp_dir / (str(uuid4()) + "." + extension)

                with open(image_path, "wb") as img:
                    img.write(data)

                return image_path, extension

            response = requests.get(url, stream=True, timeout=10)
            response.raise_for_status()

            if "." in urlparse(url).path:
                extension = urlparse(url).path.split(".")[-1]
                image_name = urlparse(url).path.split("/")[-1]

            elif response.headers.get("Content-Type", "").startswith("image/"):
                extension = response.headers["Content-Type"].split("/")[1]
                image_name = str(uuid4()) + "." + extension

            else:
                return None

            image_path = temp_dir / image_name

            with open(image_path, "wb") as img:
                for chunk in response.iter_content(1024):
                    img.write(chunk)

            return image_path, extension

        except (OSError, requests.exceptions.RequestException, base64.binascii.Error):
            return None

    @staticmethod
    def convert_image(temp_dir: Path, image_path: Path) -> Union[Path, None]:
        """Convert unsupported image type to PNG for EPUB/Kindle compatibility."""
        # TODO: avif
        try:
            webp_image = Image.open(image_path)
            png_path = temp_dir / (image_path.stem + ".png")
            webp_image.save(png_path, format="PNG")
            return png_path
        except (OSError, ValueError):
            return None
        finally:
            image_path.unlink(missing_ok=True)

    def extract_images(self, temp_dir: Path, for_kindle: bool) -> None:
        """Download images and replace src with local path."""
        # TODO: src vs data-src.

        EPUB_IMAGE_TYPES = {
            "png": "image/png",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "gif": "image/gif",
            "svg": "image/svg+xml",
            "webp": "image/webp",
        }

        soup = BeautifulSoup(self.content, "html.parser")

        for img_tag in soup.find_all("img"):
            src = img_tag.get("src")

            if src:
                absolute_url = unquote(urljoin(self.url, src)).strip()
                absolute_url = absolute_url.split("?")[0]
                image = self.download_image(absolute_url, temp_dir)

                if image:
                    image_path, extension = image
                    mimetype = EPUB_IMAGE_TYPES.get(extension)

                    if not mimetype or (for_kindle and mimetype == "image/webp"):
                        image_path = self.convert_image(temp_dir, image_path)
                        mimetype = "image/png"

                        if not image_path:
                            img_tag.decompose()
                            click.echo(f"Failed to convert image: {src}")
                            continue

                    image_name = Path(image_path).name
                    img_tag["src"] = f"images/{image_name}"
                    self.images.append((image_name, mimetype))
                    click.echo(f"Downloaded: images/{image_name}")

                else:
                    click.echo(f"Failed to download image: {src}")
                    img_tag.decompose()

        self.content = str(soup)
