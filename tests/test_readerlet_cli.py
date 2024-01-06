from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from readerlet.article import Article
from readerlet.cli import cli


def test_version():
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "version" in result.output


@pytest.fixture
def article():
    return Article(
        "https://example.com",
        "Test title",
        "Test byline",
        "en",
        "<p><a href='link'>Link</a> test</p><img src='http://example.com/test-image.jpg'><figure></figure>",
        "Test text only content",
    )


def test_extract_to_epub(tmp_path, article):
    runner = CliRunner()

    with patch("readerlet.cli.extract_content") as mock_extract:
        mock_extract.return_value = article
        result = runner.invoke(
            cli, ["extract", "https://example.com", "-e", str(tmp_path)]
        )
        assert "EPUB created:" in result.output
        epub_path = tmp_path / "Test-title.epub"
        assert epub_path.exists()


def test_extract_to_epub_remove_images_hyperlinks(tmp_path, article):
    runner = CliRunner()

    with patch("readerlet.cli.extract_content") as mock_extract:
        mock_extract.return_value = article
        result = runner.invoke(
            cli, ["extract", "https://example.com", "-i", "-h", "-e", str(tmp_path)]
        )
        assert "img" not in article.content
        assert "figure" not in article.content
        assert "href" not in article.content
        assert "EPUB created:" in result.output
        epub_path = tmp_path / "Test-title.epub"
        assert epub_path.exists()


def test_extract_remove_links_print_html_to_stdout(article):
    runner = CliRunner()
    with patch("readerlet.cli.extract_content") as mock_extract:
        mock_extract.return_value = article
        result = runner.invoke(
            cli, ["extract", "https://example.com", "-h", "-o", "html"]
        )
        assert (
            result.output
            == '<p><a>Link</a> test</p><img src="http://example.com/test-image.jpg"/><figure></figure>\n'
        )


def test_extract_print_content_text_to_stdout(article):
    runner = CliRunner()
    with patch("readerlet.cli.extract_content") as mock_extract:
        mock_extract.return_value = article
        result = runner.invoke(cli, ["extract", "https://example.com", "-o", "text"])
        assert result.output == "Test text only content\n"


@patch("readerlet.cli.extract_content")
def test_send_kindle_config_file_not_found(mock_extract, article):
    runner = CliRunner()
    mock_extract.return_value = article
    with patch.object(Path, "exists") as mock_exists:
        mock_exists.return_value = False
        result = runner.invoke(cli, ["send", "https://example.com"])
        assert (
            "Error: Kindle configuration file not found. Use 'readerlet kindle-login'."
            in result.output
        )
