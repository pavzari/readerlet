from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner
from stkclient.api import APIError

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
@patch("readerlet.cli._perform_kindle_login_logic")
def test_send_kindle_config_file_not_found(mock_kindle_login, mock_extract, article):
    runner = CliRunner()
    mock_extract.return_value = article
    with patch.object(Path, "exists", return_value=False):
        runner.invoke(cli, ["send", "https://example.com"])
        mock_kindle_login.assert_called_once()


@patch("readerlet.cli.extract_content")
@patch("readerlet.cli._perform_kindle_login_logic")
def test_send_kindle_expired_token_triggers_login(
    mock_kindle_login, mock_extract, article
):
    runner = CliRunner()
    mock_extract.return_value = article

    with patch.object(Path, "exists", return_value=True):
        with patch("stkclient.Client.load") as mock_client_load:
            mock_client = MagicMock()
            mock_client_load.return_value = mock_client
            mock_client.get_owned_devices.side_effect = APIError("Missing token", None)
            runner.invoke(cli, ["send", "https://example.com"])
            mock_kindle_login.assert_called_once()


def test_send_kindle_invalid_url_raise_error(article):
    runner = CliRunner()
    result = runner.invoke(cli, ["send", "invalid-url"])
    assert "Error: Failed to extract article.\n" in result.output
