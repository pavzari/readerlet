from click.testing import CliRunner
from readerlet.cli import cli


def test_version():
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "version" in result.output


def test_readerlet():
    runner = CliRunner()
    result = runner.invoke(cli, ["Test"])
    assert result.exit_code == 0
    assert result.output == "Argument: Test!\n"
