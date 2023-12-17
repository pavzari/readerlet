import os
import json
import subprocess
from contextlib import chdir


def check_node_installed() -> bool:
    # version constraints?
    try:
        subprocess.run(
            ["node", "--version"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def install_npm_packages() -> None:
    # check for node_modules
    # if does not exist only then run npm install
    if check_node_installed():
        current_dir = os.path.dirname(os.path.abspath(__file__))
        javascript_dir = os.path.join(current_dir, "js")
        node_modules_dir = os.path.join(javascript_dir, "node_modules")

        if not os.path.exists(node_modules_dir):
            with chdir(javascript_dir):
                # os.chdir(javascript_dir) Do I need a context manager to go back to og dir?
                try:
                    result = subprocess.run(
                        ["npm", "install"],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        check=True,
                    )
                    print("npm install completed successfully.")
                except subprocess.CalledProcessError as e:
                    print(f"Error running npm install: {e}")
                    if result.stderr:
                        print(f"Error output: {result.stderr}")
                    # Handle the error?
    else:
        print("Node.js is not installed.")


def extract_content(url: str) -> dict:
    readability = subprocess.run(
        ["node", "js/extract_stdout.js", url],
        capture_output=True,
        text=True,
        check=True,
    )
    article = json.loads(readability.stdout)
    return article


if __name__ == "__main__":
    url = ""
    install_npm_packages()
    print(extract_content(url))
