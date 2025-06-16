import marimo

__generated_with = "0.13.8"
app = marimo.App(width="medium")


@app.cell
def _():
    return


@app.cell
def _():
    from moutils.oauth import DeviceFlow

    df = DeviceFlow(
        provider="github",
        client_id="Iv23lizZAx1IpMzYou7C",
        debug=True,
    )

    df
    return (df,)


@app.cell
def _(df):
    df.access_token
    return


if __name__ == "__main__":
    app.run()
