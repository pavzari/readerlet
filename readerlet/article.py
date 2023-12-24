from pathlib import Path
from typing import Union
from urllib.parse import urljoin, urlparse

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
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            # html rendering issues if image name contains %!
            filename = temp_dir / Path(urlparse(url).path).name
            with open(filename, "wb") as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)
            return filename
        return None

    def extract_images(self, temp_dir: Path) -> None:
        soup = BeautifulSoup(self.content, "html.parser")

        for img_tag in soup.find_all("img"):
            src = img_tag.get("src")
            if src:
                absolute_url = urljoin(self.url, src)
                image_path = self.download_image(absolute_url, temp_dir)
                if image_path:
                    # download_image returns a Path object not string! str(image_path)
                    img_tag["src"] = image_path
                    # TODO:
                    # mimetype, id and path for content.opf.
                    # make sure this is just image name. Shorten it too!
                    self.images.append(image_path)
                    print(f"Downloaded and replaced: {absolute_url} -> {image_path}")
                else:
                    # TODO:
                    # what happens if fails to download?
                    # remove the src attribute?
                    print(f"Failed to download: {absolute_url}")
        self.content = str(soup)
