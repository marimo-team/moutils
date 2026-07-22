# moutils

Utility [anywidget](https://anywidget.dev) components (URL/DOM/clipboard/camera/etc.) for marimo notebooks. Published to PyPI as `moutils`.

## Development

```bash
uv sync                 # create env + install (src/ layout)
uv run pytest           # run tests
uvx ruff format . && uvx ruff check .   # format + lint
uv build                # build sdist/wheel
```

- Python package lives under `src/moutils/`; widget JS/CSS in `src/moutils/static/`.
- Linting/formatting also run via pre-commit (org-wide pre-commit.ci); `pre-commit run -a` mirrors CI.
