import os
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

    def strip_hyperlinks(self):
        """Strip <a> tag attributes but keep the tags and content."""
        soup = BeautifulSoup(self.content, "html.parser")
        for a in soup.find_all("a"):
            for attrb in list(a.attrs.keys()):
                del a[attrb]
        self.content = str(soup)

    def strip_images(self):
        """Strip all image-related elements from the content."""
        tags_to_remove = ["img", "figure", "picture"]
        soup = BeautifulSoup(self.content, "html.parser")
        for tag in soup.find_all(tags_to_remove):
            tag.decompose()
        self.content = str(soup)

    def download_image(self, url, images_dir):
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            # html rendering issues if image name contains %!
            filename = os.path.join(images_dir, os.path.basename(urlparse(url).path))
            with open(filename, "wb") as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)
            return filename
        return None

    def extract_images(self):
        # This can be passed from the outsite as a temp dir or zip..
        images_dir = "images"
        if not os.path.exists(images_dir):
            os.makedirs(images_dir)

        soup = BeautifulSoup(self.content, "html.parser")

        for img_tag in soup.find_all("img"):
            src = img_tag.get("src")
            if src:
                absolute_url = urljoin(self.url, src)
                image_path = self.download_image(absolute_url, images_dir)
                if image_path:
                    img_tag["src"] = image_path
                    # make sure this is just image name. Shorten it too!
                    self.images.append(image_path)
                    print(f"Downloaded and replaced: {absolute_url} -> {image_path}")
                else:
                    print(f"Failed to download: {absolute_url}")
        self.content = str(soup)
