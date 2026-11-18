"""Read coordinated release metadata; --sync updates version mirrors."""

import json
import tomllib
from pathlib import Path

version = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))["project"][
    "version"
]
print(json.dumps({"version": version}))
