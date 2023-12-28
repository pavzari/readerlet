[![PyPI](https://img.shields.io/pypi/v/readerlet.svg)](https://pypi.org/project/readerlet/)
[![Tests](https://github.com/pavzari/readerlet/workflows/Test/badge.svg)](https://github.com/pavzari/readerlet/actions?query=workflow%3ATest)

A CLI utility for extracting readable content from web pages. Converts web articles to clean HTML or plain text using the [mozilla/readability](https://github.com/mozilla/readability) library. Extracted content can be packaged into EPUB or printed to stdout.

The application includes Send-to-Kindle integration via the [stkclient](https://github.com/maxdjohnson/stkclient), allowing sending created EPUB articles directly to your Kindle device for offline reading.

## Installation

Install using `pip` or `pipx`:

    pip install readerlet
    pipx install readerlet

Note that this utility requires Node.js.

For convenience, the [nodejs-bin](https://github.com/samwillis/nodejs-pypi) package containing node binary & npm can be installed optionally as an extra dependency:

    pip install 'readerlet[node]'

## Usage

For help, run:

    readerlet --help

The `readerlet send` packages content as EPUB file and sends it to your Kindle. You must first authorize the application with `readerlet kindle-login`. This feature stores credentials locally.

    readerlet kindle-login
    readerlet send <url>

The `extract` command extracts content from URL and outputs an EPUB file to specified directory if used with `-e` flag:

    readerlet extract <url> -e <output-dir>

To print the extracted content to stdout as html or just text:

    readerlet extract <url> -o html
    readerlet extract <url> -o text

Both `extract` and `send` commands accept `-i` and `-h` flags that remove image-related elements and hyperlinks from content.

Remove hyperlinks:

    readerlet extract <url> -h
    readerlet send <url> -h

Remove images and hyperlinks:

    readerlet extract <url> -i -h -o html
    readerlet send <url> -i -h

## Development

First checkout the code. Then create a new virtual environment:

    cd readerlet
    python -m venv venv
    source venv/bin/activate

Install the dependencies and dev/test dependencies:

    pip install -e '.[test]'

To run the tests:

    pytest
