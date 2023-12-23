import datetime
import os
import tempfile
import uuid

from jinja2 import Environment, FileSystemLoader

from readerlet.article import Article

container_xml = """
<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>"""


def create_epub(article: Article) -> None:
    env = Environment(loader=FileSystemLoader("templates"), autoescape=True)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = os.path.abspath(temp_dir)

        for dirname in ["OEBPS", "META-INF", "OEBPS/images", "OEBPS/css"]:
            os.makedirs(os.path.join(temp_path, dirname), exist_ok=True)

        with open(os.path.join(temp_path, "mimetype"), "w") as file:
            file.write("application/epub+zip")

        with open(os.path.join(temp_path, "META-INF", "container.xml"), "w") as file:
            file.write(container_xml)

        tmplt = env.get_template("content.xhtml")
        output = tmplt.render(article=article)
        with open(os.path.join(temp_path, "OEBPS", "content.xhtml"), "w") as file:
            file.write(output)

        tmplt = env.get_template("content.opf")
        output = tmplt.render(
            article=article,
            date=datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
            uuid=uuid.uuid4(),
        )
        with open(os.path.join(temp_path, "OEBPS", "content.opf"), "w") as file:
            file.write(output)


if __name__ == "__main__":
    create_epub()

"""
Epub to disk - pass path from cli()?
All images in Article need a mimetype.

1. Temp dir.
2. Create a dir structure.
3. Write files that don't change.
4. Jinja populate templates.
5. Images (where and when to invoke the dowload function?)
6. Make a zip and save to disk.    
"""
