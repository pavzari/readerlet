import os
import json
import subprocess
from contextlib import chdir
from bs4 import BeautifulSoup
import requests
from urllib.parse import urlparse, urljoin


class Article:
    def __init__(self, url, title, byline, content):
        self.url = url
        self.title = title
        self.byline = byline
        self.content = content
        self.images = []

    def strip_hyperlinks(self):
        """Strip the <a> tag attributes but keep the tags and content"""
        soup = BeautifulSoup(self.content, "html.parser")
        for a in soup.find_all("a"):
            for attr in list(a.attrs.keys()):
                del a[attr]
        self.content = str(soup)

    def strip_images(self):
        """Strip all the <img> tags"""
        soup = BeautifulSoup(self.content, "html.parser")
        for img in soup.find_all("img"):
            img.decompose()
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
                    self.images.append(image_path)
                    print(f"Downloaded and replaced: {absolute_url} -> {image_path}")
                else:
                    print(f"Failed to download: {absolute_url}")
        self.content = str(soup)


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
            with chdir(javascript_dir):
                try:
                    subprocess.run(
                        ["npm", "install"],
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    print("npm install completed successfully.")
                except subprocess.CalledProcessError:
                    print("Error running npm install.")
    else:
        print("Node.js is not installed.")


def extract_content(url: str) -> Article:
    try:
        readability = subprocess.run(
            ["node", "js/extract_stdout.js", url],
            capture_output=True,
            text=True,
            check=True,
        )
        article_data = json.loads(readability.stdout)

        title = article_data.get("title", "No Title")
        byline = article_data.get("byline", f"Unknown Author ({urlparse(url).netloc})")
        content = article_data.get("content", "")
        return Article(url, title, byline, content)

    except subprocess.CalledProcessError:
        print("Error extracting article.")


if __name__ == "__main__":
    url = ()
    install_npm_packages()
    article = extract_content(url)

    print(article.title)
    print(article.byline)
    # print(article["byline"])

    # article = strip_hyperlinks(article["content"])
    # article = strip_images(article)
    # article.extract_images()

    # f = open("article.html", "w")
    # f.write(article.content)
    # f.close()
