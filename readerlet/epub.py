import re
import shutil
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4
from zipfile import ZIP_DEFLATED, ZipFile

from jinja2 import Environment, FileSystemLoader

from readerlet.article import Article


def create_epub(
    article: Article, output_path: str, remove_images: bool, for_kindle: bool
) -> Path:
    env = Environment(
        loader=FileSystemLoader(Path(__file__).parent / "templates"), autoescape=True
    )

    with TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir).resolve()

        for dir_name in ["OEBPS", "META-INF", "OEBPS/images", "OEBPS/css"]:
            (temp_path / dir_name).mkdir(parents=True, exist_ok=True)

        if not remove_images:
            article.extract_images(temp_path / "OEBPS/images", for_kindle)

        with (temp_path / "mimetype").open("w") as file:
            file.write("application/epub+zip")

        shutil.copy(
            Path(__file__).parent / "templates" / "container.xml",
            temp_path / "META-INF" / "container.xml",
        )

        shutil.copy(
            Path(__file__).parent / "templates" / "stylesheet.css",
            temp_path / "OEBPS/css" / "stylesheet.css",
        )

        tmplt = env.get_template("content.xhtml")
        content_xhtml = tmplt.render(article=article)
        with (temp_path / "OEBPS" / "content.xhtml").open("w") as file:
            file.write(content_xhtml)

        tmplt = env.get_template("content.opf")
        content_opf = tmplt.render(
            article=article,
            date=datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
            uuid=uuid4(),
        )
        with (temp_path / "OEBPS" / "content.opf").open("w") as file:
            file.write(content_opf)

        epub_name = f"{clean_title(article.title)}.epub"

        with ZipFile(Path(output_path) / epub_name, "w", ZIP_DEFLATED) as archive:
            for file_path in temp_path.rglob("*"):
                archive.write(file_path, arcname=file_path.relative_to(temp_path))

    return Path(output_path) / epub_name


def clean_title(title: str) -> str:
    cleaned_title = re.sub(r"[^a-zA-Z\s\-\u2014]", "", title)
    cleaned_title = re.sub(r"[-\s\u2014]+", "-", cleaned_title)
    cleaned_title = cleaned_title.strip("-")
    return cleaned_title
