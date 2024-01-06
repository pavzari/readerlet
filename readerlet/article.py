from pathlib import Path
from typing import Union
from urllib.parse import unquote, urljoin, urlparse
from PIL import Image

import click
import requests
from bs4 import BeautifulSoup


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
    def download_image(url: str, temp_dir: Path) -> Union[Path, None]:
        # TODO: base64 encoded images.
        try:
            response = requests.get(url, stream=True, timeout=10)
            response.raise_for_status()
            filename = temp_dir / Path(urlparse(url).path).name
            with open(filename, "wb") as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)
            return filename
        except requests.exceptions.RequestException as e:
            click.echo(f"Failed to download image: {e}")
            return None

    @staticmethod
    def check_mediatype(name: str) -> str:
        """Check image extension and return mimetype."""
        ext = name.split(".")[-1].lower()

        ext_mimetype = {
            "png": "image/png",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "gif": "image/gif",
            "svg": "image/svg+xml",
            "webp": "image/webp",
        }

        if ext in ext_mimetype:
            return ext_mimetype[ext]
        else:
            raise ValueError(f"Unsupported EPUB 3 image format: {ext}. Removing...")

    @staticmethod
    def handle_webp_images(temp_dir: Path, image_path: Path) -> Path:
        """Convert WebP image to PNG for EPUB compatibility"""
        webp_image = Image.open(image_path)
        png_path = temp_dir / (image_path.stem + ".png")
        webp_image.save(png_path, format="PNG")
        return png_path

    def extract_images(self, temp_dir: Path, for_kindle: bool) -> None:
        """Download images and replace src with local path."""
        soup = BeautifulSoup(self.content, "html.parser")

        for img_tag in soup.find_all("img"):
            src = img_tag.get("src")
            if src:
                absolute_url = unquote(urljoin(self.url, src)).strip()
                try:
                    # TODO: src vs data-src..
                    mimetype = self.check_mediatype(Path(absolute_url).name)

                    if for_kindle and mimetype == "image/webp":
                        webp_path = self.download_image(absolute_url, temp_dir)
                        if webp_path:
                            png_path = self.handle_webp_images(temp_dir, webp_path)
                            webp_path.unlink(missing_ok=True)
                            img_tag["src"] = f"images/{Path(png_path).name}"
                            self.images.append((Path(png_path).name, "image/png"))
                            click.echo(
                                f"Downloaded and converted: images/{Path(png_path).name}"
                            )
                            continue
                        else:
                            img_tag.decompose()
                            continue
                except ValueError as e:
                    click.echo(e)
                    img_tag.decompose()
                    continue

                image_path = self.download_image(absolute_url, temp_dir)
                if image_path:
                    img_tag["src"] = f"images/{Path(image_path).name}"
                    image_name = Path(image_path).name
                    self.images.append((image_name, mimetype))
                    click.echo(f"Downloaded: images/{Path(image_path).name}")
                else:
                    img_tag.decompose()

        self.content = str(soup)
