import marimo

__generated_with = "0.13.10"
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
    return (df,)


@app.cell
def _(df, mo):
    # Display the access token when authentication is successful
    if df.access_token:
        mo.md("## Access Token")
        mo.md(f"```\n{df.access_token}\n```")
    return


if __name__ == "__main__":
    app.run()
