import os
import json
import subprocess
from contextlib import chdir
from bs4 import BeautifulSoup
import requests
from urllib.parse import urlparse, urljoin


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


def extract_content(url: str) -> dict:
    try:
        readability = subprocess.run(
            ["node", "js/extract_stdout.js", url],
            capture_output=True,
            text=True,
            check=True,
        )
        article = json.loads(readability.stdout)
        return article
    except subprocess.CalledProcessError:
        print("Error extracting article.")


def strip_hyperlinks(html: str) -> str:
    """Strip the <a> tag attributes but keep the tags and content"""
    soup = BeautifulSoup(html, "html.parser")
    for a in soup.find_all("a"):
        for attr in list(a.attrs.keys()):
            del a[attr]
    return str(soup)


def strip_images(html: str) -> str:
    """Strip all the <img> tags"""
    soup = BeautifulSoup(html, "html.parser")
    for img in soup.find_all("img"):
        img.decompose()
    return str(soup)


def download_image(url, directory):
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        filename = os.path.join(directory, os.path.basename(urlparse(url).path))
        with open(filename, "wb") as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)
        return filename
    return None


def extract_images(page_html, page_url):
    images_dir = "images"
    if not os.path.exists(images_dir):
        os.makedirs(images_dir)

    soup = BeautifulSoup(page_html, "html.parser")

    for img_tag in soup.find_all("img"):
        src = img_tag.get("src")

        if src:
            absolute_url = urljoin(page_url, src)
            image_path = download_image(absolute_url, images_dir)

            if image_path:
                img_tag["src"] = image_path
                print(f"Downloaded and replaced: {absolute_url} -> {image_path}")
            else:
                print(f"Failed to download: {absolute_url}")

    return str(soup)


if __name__ == "__main__":
    url = ()
    install_npm_packages()
    article = extract_content(url)

    # article = strip_hyperlinks(article["content"])
    # article = strip_images(article)

    article = extract_images(article["content"], url)

    f = open("article.html", "w")
    f.write(article)
    f.close()
