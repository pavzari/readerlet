## readerlet

[![PyPI](https://img.shields.io/pypi/v/readerlet.svg)](https://pypi.org/project/readerlet/)
[![Tests](https://github.com/pavzari/readerlet/workflows/Test/badge.svg)](https://github.com/pavzari/readerlet/actions?query=workflow%3ATest)

## Installation

Install this tool using `pip` or `pipx`:

    pip install readerlet
    pipx install readerlet

## Usage

For help, run:

    readerlet --help

You can also use:

    python -m readerlet --help

## Development

First checkout the code. Then create a new virtual environment:

    cd readerlet
    python -m venv venv
    source venv/bin/activate

Install the dependencies and test dependencies:

    pip install -e '.[test]'

To run the tests:

    pytest
