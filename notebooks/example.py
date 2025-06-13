import marimo

__generated_with = "0.13.15"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    from moutils import (
        URLHash,
        URLPath,
        StorageItem,
        CookieManager,
        DOMQuery,
        Slot,
        URLInfo,
        CopyToClipboard,
        shell,
    )

    return (
        CookieManager,
        CopyToClipboard,
        DOMQuery,
        Slot,
        StorageItem,
        URLHash,
        URLInfo,
        URLPath,
        mo,
        shell,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## `URLPath`""")
    return


@app.cell
def _(URLPath):
    url_path = URLPath()
    return (url_path,)


@app.cell
def _(url_path):
    url_path.path
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## `URLHash`""")
    return


@app.cell
def _(URLHash):
    url_hash = URLHash()
    return (url_hash,)


@app.cell
def _(url_hash):
    url_hash.hash
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## `URLInfo`""")
    return


@app.cell
def _(URLInfo):
    url_info = URLInfo()
    url_info
    return (url_info,)


@app.cell
def _(url_info):
    [
        url_info.hostname,
        url_info.port,
    ]
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## StorageItem""")
    return


@app.cell
def _(StorageItem):
    local_state = StorageItem(key="my_state")
    return (local_state,)


@app.cell
def _(local_state):
    local_state.data = 100
    return


@app.cell
def _(local_state):
    local_state.data
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Cookies""")
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
    mo.md(r"""## DOM Query""")
    return


@app.cell
def _(DOMQuery):
    query = DOMQuery(selector="#root")
    return (query,)


@app.cell
def _(query):
    query.result
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Slot""")
    return


@app.cell
def _(Slot):
    slot = Slot(
        children="<div>hello</div>",
        on_mouseover=lambda: print("mouse over"),
        on_mouseout=lambda: print("mouse out"),
    )
    return (slot,)


@app.cell
def _(slot):
    slot.value
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Copy to Clipboard""")
    return


@app.cell
def _(CopyToClipboard):
    copy_widget = CopyToClipboard(
        text="Hello, world!",
        button_text="Click to copy",
        success_text="Copied to clipboard!",
    )
    return (copy_widget,)


@app.cell
def _(copy_widget):
    copy_widget.success
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Shell""")
    return


@app.cell
def _(shell):
    shell_widget = shell("echo 'Hello from ShellWidget!'")
    shell_widget
    return


if __name__ == "__main__":
    app.run()
