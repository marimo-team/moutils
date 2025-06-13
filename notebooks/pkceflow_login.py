import marimo

__generated_with = "0.11.26"
app = marimo.App(width="medium")


@app.cell
def _():
    from moutils.oauth import PKCEFlow

    df = PKCEFlow(
        provider="cloudflare",
        client_id="ec85d9cd-ff12-4d96-a376-432dbcf0bbfc",
        redirect_uri="https://auth.sandbox.marimo.app/oauth/sso-callback",
        debug=True,
    )

    df
    return PKCEFlow, df


@app.cell
def _(df):
    print(f"df.access_token: {df.access_token}")
    return


if __name__ == "__main__":
    app.run()
