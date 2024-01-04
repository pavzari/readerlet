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
    with pytest.raises(click.ClickException, match="Error extracting article."):
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
        Article, "download_image", return_value=tmp_path / "test-image.jpg"
    ):
        article.extract_images(tmp_path)
        assert len(article.images) == 1
        assert article.images[0][0] == "test-image.jpg"
        assert article.images[0][1] == "image/jpeg"
        assert "images/test-image.jpg" in article.content


def test_download_image_fails_img_tag_decomposed(article, tmp_path):
    with patch.object(article, "download_image") as mock_download:
        mock_download.return_value = None
        article.extract_images(tmp_path)
        assert len(article.images) == 0
        soup = BeautifulSoup(article.content, "html.parser")
        img_tags = soup.find_all("img")
        assert len(img_tags) == 0
