import marimo

__generated_with = "0.11.26"
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
    )
    return CookieManager, DOMQuery, Slot, StorageItem, URLHash, URLPath, mo


@app.cell
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


@app.cell
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


@app.cell
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


@app.cell
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


@app.cell
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


@app.cell
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


if __name__ == "__main__":
    app.run()
