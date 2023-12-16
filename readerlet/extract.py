import json
import subprocess


readability = subprocess.run(
    ["js/extract_stdout.js", url], capture_output=True, text=True, check=True
)
article = json.loads(readability.stdout)
