import subprocess
from unittest.mock import patch

import click
import pytest
from bs4 import BeautifulSoup

from readerlet.article import Article
from readerlet.cli import extract_content


@pytest.fixture
def article():
    return Article(
        "https://example.com",
        "Test title",
        "Test byline",
        "en",
        "<p><a href='link'>Link</a> test</p><img  src='http://example.com/test-image.jpg'><figure></figure>",
        "Test text only content",
    )


@pytest.fixture
def mock_subprocess_run():
    with patch("subprocess.run") as mock_sub_run:
        yield mock_sub_run


def test_extract_content_successful_extraction(mock_subprocess_run):
    mock_subprocess_run.return_value.stdout = '{"title": "Sample Title", "byline": "Author", "lang": "en", "content": "<p>Content</p>", "textContent": "Text Content"}'
    url = "http://example.com"
    result = extract_content(url)
    assert isinstance(result, Article)
    assert result.url == url
    assert result.title == "Sample Title"


def test_extract_content_unsuccessful_extraction(mock_subprocess_run):
    mock_subprocess_run.side_effect = subprocess.CalledProcessError(
        returncode=1, cmd="node"
    )
    url = "http://example.com"
    with pytest.raises(click.ClickException, match="Failed to extract article."):
        extract_content(url)


def test_extract_content_no_content(mock_subprocess_run):
    mock_subprocess_run.return_value.stdout = '{"title": "Sample Title", "byline": "Author", "lang": "en", "content": "", "textContent": "Text Content"}'
    url = "http://example.com"
    with pytest.raises(click.ClickException, match="Content not extracted."):
        extract_content(url)


def test_remove_hyperlinks_href(article):
    article.remove_hyperlinks()
    soup = BeautifulSoup(article.content, "html.parser")
    assert soup.find("a") is not None
    assert not soup.find("a").has_attr("href")


def test_remove_images(article):
    article.remove_images()
    soup = BeautifulSoup(article.content, "html.parser")
    assert soup.find("img") is None
    assert soup.find("figure") is None


def test_extract_images(article, tmp_path):
    with patch.object(
        Article, "download_image", return_value=(tmp_path / "test-image.jpg", "jpg")
    ):
        article.extract_images(tmp_path, for_kindle=False)
        assert len(article.images) == 1
        assert article.images[0][0] == "test-image.jpg"
        assert article.images[0][1] == "image/jpeg"
        assert "images/test-image.jpg" in article.content


def test_extract_images_with_base64(article, tmp_path):
    with patch.object(
        Article, "download_image", return_value=(tmp_path / "test-base64.png", "png")
    ):
        article.content = (
            '<img src="data:image/png;base64,base64data" alt="Test Image base64">'
        )
        article.extract_images(tmp_path, for_kindle=False)

        assert len(article.images) == 1
        assert article.images[0][0] == "test-base64.png"
        assert article.images[0][1] == "image/png"
        assert "images/test-base64.png" in article.content


def test_extract_images_check_content_type_header(article, tmp_path):
    with patch.object(
        Article,
        "download_image",
        return_value=(tmp_path / "test-content-type.jpg", "jpg"),
    ):
        article.content = '<img src="https://example.com/image-url" alt="Test Image">'
        article.extract_images(tmp_path, for_kindle=False)

        assert len(article.images) == 1
        assert article.images[0][0] == "test-content-type.jpg"
        assert article.images[0][1] == "image/jpeg"
        assert "images/test-content-type.jpg" in article.content


def test_download_image_fails_img_tag_decomposed(article, tmp_path):
    with patch.object(article, "download_image") as mock_download:
        mock_download.return_value = None
        article.extract_images(tmp_path, for_kindle=True)
        assert len(article.images) == 0
        soup = BeautifulSoup(article.content, "html.parser")
        img_tags = soup.find_all("img")
        assert len(img_tags) == 0


@pytest.fixture
def article_webp():
    return Article(
        "https://example.com",
        "Test title",
        "Test byline",
        "en",
        "<p><a href='link'>Link</a> test</p><img  src='http://example.com/test-image.webp'><figure></figure>",
        "Test text only content",
    )


def test_extract_images_webp_conversion(article_webp, tmp_path):
    webp_image_path = tmp_path / "test-image.webp"
    png_image_path = tmp_path / "test-image.png"

    with patch.object(
        Article, "download_image", return_value=(webp_image_path, "webp")
    ):
        with patch.object(Article, "convert_image", return_value=png_image_path):
            article_webp.extract_images(tmp_path, for_kindle=True)

    assert len(article_webp.images) == 1
    assert article_webp.images[0][0] == "test-image.png"
    assert article_webp.images[0][1] == "image/png"
    assert "images/test-image.png" in article_webp.content


def test_extract_images_no_webp_conversion(article_webp, tmp_path):
    webp_image_path = tmp_path / "test-image.webp"
    png_image_path = tmp_path / "test-image.png"

    with patch.object(
        Article, "download_image", return_value=(webp_image_path, "webp")
    ):
        with patch.object(Article, "convert_image", return_value=png_image_path):
            article_webp.extract_images(tmp_path, for_kindle=False)

    assert len(article_webp.images) == 1
    assert article_webp.images[0][0] == "test-image.webp"
    assert article_webp.images[0][1] == "image/webp"
    assert "images/test-image.webp" in article_webp.content
