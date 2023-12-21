import os
import pytest
import click
from unittest.mock import patch
from readerlet.cli import check_node_installed, install_npm_packages


def test_check_node_installed_success(fp):
    fp.register_subprocess(["node", "--version"], stdout="v20.5.0")
    assert check_node_installed() == True


def test_check_node_installed_failure(fp):
    fp.register_subprocess(["node", "--version"], returncode=1)
    assert check_node_installed() == False


def test_install_npm_packages_node_not_installed(fp):
    fp.register_subprocess(["node", "--version"], returncode=1)
    with pytest.raises(click.ClickException, match="Node.js runtime not found."):
        install_npm_packages()


def test_install_npm_packages_npm_failure(fp):
    fp.register_subprocess(["node", "--version"], returncode=0)
    fp.register_subprocess(["npm", "install"], returncode=1)

    with patch.object(os.path, "exists", return_value=False):
        with pytest.raises(
            click.ClickException, match="Failed to install npm packages."
        ):
            install_npm_packages()


def test_install_npm_packages_npm_ok(capsys, fp):
    fp.register_subprocess(["node", "--version"], stdout="v20.5.0")
    fp.register_subprocess(["npm", "install"], returncode=0)

    with patch.object(os.path, "exists", return_value=False):
        with patch("click.echo") as mock_echo:
            install_npm_packages()
            mock_echo.assert_called_with("Npm install completed successfully.")
