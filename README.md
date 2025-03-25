# moutils

Utility functions used in [marimo](https://github.com/marimo-team/marimo).

> [!NOTE]
> This is a community led effort and not actively prioritized by the core marimo team.

## Installation

```sh
pip install moutils
```

or with [uv](https://github.com/astral-sh/uv):

```sh
uv add moutils
```

## Included

### URLHash

Widget for interacting with URL hash. Allows you to get and set the hash portion of the URL.

### URLPath

Widget for interacting with URL path. Allows you to get and set the current URL path.

### DOMQuery

Widget for querying DOM elements. Use CSS selectors to find and interact with elements on the page.

### CookieManager

Widget for managing browser cookies. Get, set, and monitor browser cookies.

### StorageItem

Widget for interacting with browser storage (local/session). Access and manipulate data in browser's localStorage or sessionStorage.

### Slot

Widget for creating a slot that can contain HTML and handle DOM events. Supports a wide range of events:

- Mouse events (click, hover, etc.)
- Keyboard events
- Form events
- Drag and drop
- Touch events
- Pointer events
- Scroll events
- Clipboard events
- Animation and transition events

## Development

We recommend using [uv](https://github.com/astral-sh/uv) for development.
It will automatically manage virtual environments and dependencies for you.

```sh
uv run marimo notebooks/example.py
```
