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

## Widgets

| Widget | Description |
|--------|-------------|
| [`URLHash`](#urlhash) | Get and set the URL hash |
| [`URLPath`](#urlpath) | Get and set the URL path |
| [`URLInfo`](#urlinfo) | Read all URL components |
| [`DOMQuery`](#domquery) | Query DOM elements with CSS selectors |
| [`CookieManager`](#cookiemanager) | Get, set, and monitor browser cookies |
| [`StorageItem`](#storageitem) | Read/write localStorage or sessionStorage |
| [`Slot`](#slot) | Render HTML with DOM event handlers |
| [`CopyToClipboard`](#copytoclipboard) | Copy text to clipboard with a button |
| [`ShellWidget`](#shellwidget) | Run terminal commands with live output |
| [`ColorScheme`](#colorscheme) | Detect dark/light mode preference |
| [`ViewportSize`](#viewportsize) | Detect window dimensions |
| [`OnlineStatus`](#onlinestatus) | Detect network connectivity |
| [`PageVisibility`](#pagevisibility) | Detect if the browser tab is active |
| [`Geolocation`](#geolocation) | Get the user's geographic coordinates |
| [`CameraCapture`](#cameracapture) | Capture a still image from the webcam |
| [`Notification`](#notification) | Send browser notifications |
| [`KeyboardShortcut`](#keyboardshortcut) | Listen for global keyboard shortcuts |
| [`thread_map`<br>`process_map`<br>`interpreter_map`](#thread_map-process_map-interpreter_map) | Thread/Process/Interpreter mapping |
| [`PrintPageButton`](#printpagebutton) | Button to open the browser print dialog |
| [`print_page()`](#print_page) | Programmatically trigger the browser print dialog |
| [`ScreenshotButton`](#screenshotbutton) | Button to capture a DOM element as PNG |
| [`screenshot()`](#screenshot) | Programmatically screenshot a DOM element |

---

### URLHash

Get and set the hash portion of the URL.

```python
from moutils import URLHash
h = URLHash()
h.hash  # e.g. "#section-1"
```

### URLPath

Get and set the current URL path.

```python
from moutils import URLPath
p = URLPath()
p.path  # e.g. "/notebooks/demo"
```

### URLInfo

Read all URL components (protocol, hostname, port, pathname, search, hash, etc.).

```python
from moutils import URLInfo
info = URLInfo()
info.hostname  # e.g. "localhost"
```

### DOMQuery

Query DOM elements using CSS selectors.

```python
from moutils import DOMQuery
q = DOMQuery(selector=".my-class")
q.result  # list of matched element data
```

### CookieManager

Get, set, and monitor browser cookies.

```python
from moutils import CookieManager
cm = CookieManager()
cm.cookies  # dict of current cookies
```

### StorageItem

Read and write data in the browser's localStorage or sessionStorage.

```python
from moutils import StorageItem
s = StorageItem(key="my-key", storage_type="local")
s.data  # stored value
```

### Slot

Render HTML content and handle DOM events (mouse, keyboard, form, drag, touch, pointer, scroll, clipboard, animation).

```python
from moutils import Slot
s = Slot(children="<button>Click me</button>", on_dblclick=lambda e: print(e))
```

### CopyToClipboard

Copy text to the clipboard with a button and success feedback.

```python
from moutils import CopyToClipboard
c = CopyToClipboard(text="hello world")
```

### ShellWidget

Run terminal commands in notebooks with real-time output streaming.

```python
from moutils import shell

shell("ls -la")
shell("npm install", working_directory="./frontend")
```

### ColorScheme

Detect the user's preferred color scheme (light or dark). Automatically updates when the preference changes.

```python
from moutils import ColorScheme
cs = ColorScheme()
cs.scheme       # "light" or "dark"
cs.prefers_dark # True or False
```

### ViewportSize

Detect the browser window dimensions. Updates on resize (debounced).

```python
from moutils import ViewportSize
vs = ViewportSize()
vs.width   # e.g. 1920
vs.height  # e.g. 1080
```

### OnlineStatus

Detect whether the browser has network connectivity.

```python
from moutils import OnlineStatus
os_ = OnlineStatus()
os_.online  # True or False
```

### PageVisibility

Detect whether the browser tab is currently active or hidden.

```python
from moutils import PageVisibility
pv = PageVisibility()
pv.visible  # True or False
pv.state    # "visible" or "hidden"
```

### Geolocation

Get the user's geographic coordinates. Opt-in — set `enabled=True` to request permission.

```python
from moutils import Geolocation
geo = Geolocation(enabled=True)
geo.latitude   # e.g. 37.7749
geo.longitude  # e.g. -122.4194
geo.accuracy   # meters
geo.error      # error message, if any
```

### CameraCapture

Capture a still image from the webcam. Opt-in — set `enabled=True` to request camera access.

```python
from moutils import CameraCapture
cam = CameraCapture(enabled=True, width=640, height=480)
cam.image_data  # base64 data URL of the captured image
```

### Notification

Send browser notifications. Automatically requests permission when needed.

```python
from moutils import Notification
n = Notification(title="Done!", body="Your computation finished.")
n.send = True   # fires the notification
n.permission    # "default", "granted", or "denied"
```

### KeyboardShortcut

Listen for global keyboard shortcuts with modifier key support.

```python
from moutils import KeyboardShortcut
ks = KeyboardShortcut(shortcut="ctrl+k")
ks.pressed  # True when the shortcut is pressed
ks.event    # dict with key event details
```

### thread_map, process_map, interpreter_map

Equivalent to `list(map(fn, *iterables))` driven by `ThreadPoolExecutor`,
`ProcessPoolExecutor`, or `InterpreterPoolExecutor` (python >= 3.14) from
`concurrent.futures`, respectively, with a Marimo progress bar or spinner.

A spinner is used if the length cannot be automatically determined.

Inspired by https://tqdm.github.io/docs/contrib.concurrent/.

```python
from moutils.concurrent import thread_map, process_map, interpreter_map

def add_one(x):
    return x + 1

results: list[int] = thread_map(add_one, range(1000))
# Can specify title, max_workers, etc.
results = process_map(add_one, range(1000), title="Process map", max_workers=2)
results = interpreter_map(add_one, range(1000)) # Only available for Python >=3.14
```

### PrintPageButton

Button that opens the browser print dialog when clicked.

```python
from moutils import PrintPageButton
btn = PrintPageButton()
```

### print_page()

Programmatically trigger the browser print dialog.

```python
import moutils
moutils.print_page()
```

### ScreenshotButton

Button that captures a DOM element as a PNG and downloads it.

```python
from moutils import ScreenshotButton
btn = ScreenshotButton(locator="#my-chart", filename="chart.png")
```

### screenshot()

Programmatically screenshot a DOM element and download as PNG.

```python
import moutils
moutils.screenshot(locator="#my-chart", filename="chart.png")
```

## Development

We use [uv](https://github.com/astral-sh/uv) for development.

Specific notebook
```sh
uv run marimo edit notebooks/example.py
```

Workspace
```sh
uv run --active marimo edit --port 2718
```

### Installing pre-commit

```sh
uv tool install pre-commit
pre-commit
```

### Testing

To run all tests:

```sh
pytest -v tests/
```
