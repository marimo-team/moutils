import marimo

__generated_with = "0.19.9"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # moutils

    A collection of browser utility widgets for [marimo](https://marimo.io) notebooks, built on [anywidget](https://anywidget.dev).

    This notebook demonstrates each widget with a live example.
    """)
    return


@app.cell
def _(mo):
    mo.outline()
    return


@app.cell(hide_code=True)
def _():
    import marimo as mo
    from moutils import (
        URLHash,
        URLPath,
        URLInfo,
        StorageItem,
        CookieManager,
        DOMQuery,
        Slot,
        CopyToClipboard,
        shell,
        ColorScheme,
        ViewportSize,
        OnlineStatus,
        PageVisibility,
        Geolocation,
        Notification,
        KeyboardShortcut,
        PrintPageButton,
        print_page,
        ScreenshotButton,
        screenshot,
    )

    return (
        ColorScheme,
        CookieManager,
        CopyToClipboard,
        DOMQuery,
        Geolocation,
        KeyboardShortcut,
        Notification,
        OnlineStatus,
        PageVisibility,
        PrintPageButton,
        ScreenshotButton,
        Slot,
        StorageItem,
        URLHash,
        URLInfo,
        URLPath,
        ViewportSize,
        mo,
        print_page,
        screenshot,
        shell,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ---

    ## URL Widgets

    ### `URLPath`

    Read and set the current URL path.
    """)
    return


@app.cell
def _(URLPath):
    url_path = URLPath()
    return (url_path,)


@app.cell(hide_code=True)
def _(mo, url_path):
    mo.md(f"""
    Current path: `{url_path.path}`
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### `URLHash`

    Read and set the URL hash fragment.
    """)
    return


@app.cell
def _(URLHash):
    url_hash = URLHash()
    return (url_hash,)


@app.cell(hide_code=True)
def _(mo, url_hash):
    mo.md(f"""
    Current hash: `{url_hash.hash or "(empty)"}`
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### `URLInfo`

    Read all URL components at once.
    """)
    return


@app.cell
def _(URLInfo):
    url_info = URLInfo()
    return (url_info,)


@app.cell(hide_code=True)
def _(mo, url_info):
    mo.md(f"""
    | Component | Value |
    |-----------|-------|
    | Protocol | `{url_info.protocol}` |
    | Hostname | `{url_info.hostname}` |
    | Port | `{url_info.port}` |
    | Pathname | `{url_info.pathname}` |
    | Search | `{url_info.search or "(empty)"}` |
    | Hash | `{url_info.hash or "(empty)"}` |
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ---

    ## Browser Environment

    ### `ColorScheme`

    Detect the user's preferred color scheme. Updates live when the OS setting changes.
    """)
    return


@app.cell
def _(ColorScheme):
    color_scheme = ColorScheme()
    return (color_scheme,)


@app.cell
def _(color_scheme, mo):
    _icon = "🌙" if color_scheme.prefers_dark else "☀️"
    mo.md(f"{_icon} Color scheme: **{color_scheme.scheme}**")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### `ViewportSize`

    Detect the browser window dimensions. Resize the window to see it update.
    """)
    return


@app.cell
def _(ViewportSize):
    viewport = ViewportSize()
    return (viewport,)


@app.cell(hide_code=True)
def _(mo, viewport):
    mo.md(f"""
    Viewport: **{viewport.width}** x **{viewport.height}** px
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### `OnlineStatus`

    Detect whether the browser has network connectivity.
    """)
    return


@app.cell
def _(OnlineStatus):
    online = OnlineStatus()
    return (online,)


@app.cell
def _(mo, online):
    _status = "Online ✅" if online.online else "Offline ❌"
    mo.md(f"Network: **{_status}**")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### `PageVisibility`

    Detect if this browser tab is active. Switch to another tab and back to see it change.
    """)
    return


@app.cell
def _(PageVisibility):
    visibility = PageVisibility()
    return (visibility,)


@app.cell(hide_code=True)
def _(mo, visibility):
    mo.md(f"""
    Tab is **{visibility.state}**
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ---

    ## Storage & Cookies

    ### `StorageItem`

    Read and write data to localStorage or sessionStorage.
    """)
    return


@app.cell
def _(StorageItem):
    local_state = StorageItem(key="moutils_demo_counter")
    return (local_state,)


@app.cell
def _(local_state):
    # Increment a counter each time this notebook runs
    _count = (local_state.data or 0) + 1
    local_state.data = _count
    return


@app.cell(hide_code=True)
def _(local_state, mo):
    mo.md(f"""
    This notebook has been opened **{local_state.data}** time(s) in this browser.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### `CookieManager`

    Read all browser cookies.
    """)
    return


@app.cell
def _(CookieManager):
    cookies = CookieManager()
    return (cookies,)


@app.cell
def _(cookies):
    cookies.cookies
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ---

    ## DOM & Clipboard

    ### `DOMQuery`

    Query DOM elements using CSS selectors.
    """)
    return


@app.cell
def _(DOMQuery):
    query = DOMQuery(selector="title")
    return (query,)


@app.cell
def _(query):
    query.result
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### `Slot`

    Render arbitrary HTML and listen for DOM events.
    """)
    return


@app.cell
def _(Slot):
    slot = Slot(
        children='<button style="padding: 8px 16px; cursor: pointer;">Hover or double-click me</button>',
        on_mouseover=lambda: print("mouse entered"),
        on_mouseout=lambda: print("mouse left"),
        on_dblclick=lambda e: print("double-clicked!", e),
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### `CopyToClipboard`

    Copy text to the clipboard with a single click.
    """)
    return


@app.cell
def _(CopyToClipboard):
    copy_widget = CopyToClipboard(
        text="Hello from moutils!",
        button_text="Copy greeting",
        success_text="Copied!",
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ---

    ## Device APIs

    ### `Geolocation`

    Get the user's geographic coordinates. Set `enabled=True` to request permission.
    """)
    return


@app.cell
def _(Geolocation):
    geo = Geolocation()
    return (geo,)


@app.cell
def _(geo, mo):
    geo_switch = mo.ui.switch(label="Enable geolocation", value=geo.enabled)
    geo_switch
    return (geo_switch,)


@app.cell
def _(geo, geo_switch, mo):
    geo.enabled = geo_switch.value
    _msg = (
        f"Location: **{geo.latitude:.4f}, {geo.longitude:.4f}** (accuracy: {geo.accuracy:.0f}m)"
        if geo.enabled and geo.latitude != 0
        else f"Error: {geo.error}"
        if geo.error
        else "Toggle the switch above to request location access."
    )
    mo.md(_msg)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### `Notification`

    Send a browser notification. The browser will ask for permission the first time.
    """)
    return


@app.cell
def _(Notification):
    notif = Notification(title="moutils", body="Your computation is done!")
    return (notif,)


@app.cell
def _(mo):
    send_notification = mo.ui.button(label="Send notification")
    send_notification
    return (send_notification,)


@app.cell
def _(mo, notif, send_notification):
    send_notification.value  # react to button press
    if send_notification.value:
        notif.send = True
    mo.md(f"Permission: `{notif.permission}`")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ---

    ## Keyboard

    ### `KeyboardShortcut`

    Listen for global keyboard shortcuts. Try pressing the shortcut below.
    """)
    return


@app.cell
def _(KeyboardShortcut):
    shortcut = KeyboardShortcut(shortcut="ctrl+k")
    return (shortcut,)


@app.cell
def _(mo, shortcut):
    _msg = (
        "**`ctrl+k` was pressed!**"
        if shortcut.pressed
        else "Press `ctrl+k` to trigger the shortcut."
    )
    mo.md(_msg)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ---

    ## Shell

    ### `ShellWidget`

    Run terminal commands with real-time output streaming.
    """)
    return


@app.cell
def _(shell):
    shell_widget = shell("echo 'Hello from moutils!'")
    shell_widget
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ---

    ## Print & Screenshot

    ### `PrintPageButton`

    A button that opens the browser print dialog when clicked.
    """)
    return


@app.cell
def _(PrintPageButton):
    print_btn = PrintPageButton()
    print_btn
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### `print_page()`

    Programmatically trigger the browser print dialog. Uncomment to activate.
    """)
    return


@app.cell
def _(mo):
    print_page_button = mo.ui.run_button(label="Print page")
    print_page_button
    return (print_page_button,)


@app.cell
def _(print_page, print_page_button):
    # Uncomment below to trigger print dialog on cell run:
    if print_page_button.value:
        print_page()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### `ScreenshotButton`

    A button that captures a DOM element as a PNG download.
    """)
    return


@app.cell
def _(ScreenshotButton):
    screenshot_btn = ScreenshotButton(locator="body", filename="page.png")
    screenshot_btn
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### `screenshot()`

    Programmatically screenshot a DOM element. Uncomment to activate.
    """)
    return


@app.cell
def _(mo):
    take_screenshot = mo.ui.run_button(label="Take screenshot")
    take_screenshot
    return (take_screenshot,)


@app.cell
def _(screenshot, take_screenshot):
    # Uncomment below to capture a screenshot on cell run:
    if take_screenshot.value:
        screenshot(locator="[data-cell-name='my_cell']", filename="page.png")
    return


@app.cell
def my_cell(mo):
    mo.ui.table([1, 2, 3])
    return


if __name__ == "__main__":
    app.run()
