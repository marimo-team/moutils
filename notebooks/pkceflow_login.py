# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "anywidget==0.9.18",
#     "js==1.0",
#     "marimo",
#     "nbformat==5.10.4",
#     "requests==2.32.4",
# ]
# ///

import marimo

__generated_with = "0.14.7"

app = marimo.App(
    width="full",
    auto_download=["ipynb", "html"],
)


####################
# Helper Functions #
####################
@app.cell(hide_code=True)
async def _():
    # Helper Functions - click to view code
    import json
    import marimo as mo
    from urllib.request import Request, urlopen

    try:
        import js
        origin = js.eval("self.location?.origin")
        print(f"WASM environment detected - origin: {origin}")
        # Configure OAuth endpoints based on environment
        if "localhost:8088" in origin:
            # Local development with Cloudflare Pages
            print("Environment: Local WASM with Cloudflare Pages")
            oauth_config = {
                "logout_url": f"{origin}/oauth/revoke",
                "redirect_uri": f"{origin}/oauth/callback",
                "token_url": f"{origin}/oauth/token"
            }
        elif "localhost" in origin:
            # Local WASM without Cloudflare Pages
            print("Environment: Local WASM (standard)")
            origin = "https://auth.sandbox.marimo.app"
            oauth_config = {
                "logout_url": f"{origin}/oauth/revoke",
                "redirect_uri": f"{origin}/oauth/sso-callback",
                "token_url": f"{origin}/oauth/token"
            }
        else:
            # Production WASM environment
            print("Environment: Production WASM")
            oauth_config = {
                "logout_url": f"{origin}/oauth/revoke",
                "redirect_uri": f"{origin}/oauth/sso-callback",
                "token_url": f"{origin}/oauth/token"
            }
    except AttributeError:
        # Running in Python environment (not WASM)
        print("Environment: Local Python")
        origin = "https://auth.sandbox.marimo.app"
        oauth_config = {
            "logout_url": f"{origin}/oauth/revoke",
            "redirect_uri": f"{origin}/oauth/sso-callback",
            "token_url": f"{origin}/oauth/token",
            "proxy": "https://cors-anywhere.herokuapp.com/https://example.com"
        }

    # Debug OAuth config
    for key, value in oauth_config.items():
        print(f"{key}: {value}")

    return json, mo, Request, urlopen, origin, oauth_config


###############
# Login Cells #
###############
@app.cell(hide_code=True)
def _(oauth_config):
    # Login to Cloudflare - click to view code
    import requests  # noqa: F401 - required for moutils.oauth
    from moutils.oauth import PKCEFlow

    df = PKCEFlow(
        provider="cloudflare",
        client_id="ec85d9cd-ff12-4d96-a376-432dbcf0bbfc",
        logout_url=oauth_config["logout_url"],
        redirect_uri=oauth_config["redirect_uri"],
        token_url=oauth_config["token_url"],
        proxy=oauth_config["proxy"],
    )
    df
    return df


@app.cell
def _(df):
    print(f"df.access_token: {df.access_token}")
    return


if __name__ == "__main__":
    app.run()
