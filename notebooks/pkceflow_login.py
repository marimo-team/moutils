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


__generated_with = "0.11.26"
app = marimo.App(width="full", auto_download=["ipynb", "html"])


@app.cell(hide_code=True)
def _():
    # Helper Functions - click to view code
    import json
    import marimo as mo
    from urllib.request import Request, urlopen
    import warnings
    warnings.filterwarnings("ignore", category=UserWarning, module="pkg_resources")

    # Configure OAuth endpoints based on environment
    try:
        import js

        origin = js.eval("self.location?.origin")
        # print(f"WASM environment detected - origin: {origin}")
        if "localhost:8088" in origin:
            # print("Environment: Local WASM with Cloudflare Pages")
            oauth_config = {
                "logout_url": f"{origin}/oauth/revoke",
                "redirect_uri": f"{origin}/oauth/callback",
                "token_url": f"{origin}/oauth/token",
                "use_new_tab": True,
            }
        elif "localhost" in origin:
            # print("Environment: Local WASM (standard)")
            origin = "https://auth.sandbox.marimo.app"
            oauth_config = {
                "logout_url": "https://dash.cloudflare.com/oauth2/oauth/revoke",
                "redirect_uri": f"{origin}/oauth/sso-callback",
                "token_url": "https://dash.cloudflare.com/oauth2/token",
                "use_new_tab": False,
            }
        else:
            # print("Environment: Production WASM")
            oauth_config = {
                "logout_url": f"{origin}/oauth/revoke",
                "redirect_uri": f"{origin}/oauth/callback",
                "token_url": f"{origin}/oauth/token",
                "use_new_tab": True,
            }
    except AttributeError:
        # print("Environment: Local Python")
        origin = "https://auth.sandbox.marimo.app"
        oauth_config = {
            "logout_url": "https://dash.cloudflare.com/oauth2/revoke",
            "redirect_uri": f"{origin}/oauth/sso-callback",
            "token_url": "https://dash.cloudflare.com/oauth2/token",
            "proxy": "https://corsproxy.marimo.app",
            "use_new_tab": False,
        }

    # Debug OAuth config
    # for key, value in oauth_config.items():
    #     print(f"{key}: {value}")
    return Request, js, json, mo, oauth_config, origin, urlopen


@app.cell(hide_code=True)
def _(oauth_config):
    # Login to Cloudflare - click to view code
    import requests  # noqa: F401 - required for moutils.oauth
    from moutils.oauth import PKCEFlow

    df = PKCEFlow(
        provider="cloudflare",
        client_id="ec85d9cd-ff12-4d96-a376-432dbcf0bbfc",
        logout_url=oauth_config.get("logout_url"),
        redirect_uri=oauth_config.get("redirect_uri"),
        token_url=oauth_config.get("token_url"),
        proxy=oauth_config.get("proxy"),
        use_new_tab=oauth_config.get("use_new_tab"),
        debug=False,
    )
    df
    return PKCEFlow, df, requests


@app.cell
def _(df):
    print(f"df.access_token: {df.access_token}")
    return


if __name__ == "__main__":
    app.run()
