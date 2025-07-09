# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "anywidget",
#     "js==1.0",
#     "marimo",
#     "nbformat",
#     "requests==2.32.4",
# ]
# ///

import marimo

__generated_with = "0.14.10"
app = marimo.App(
    width="full",
    app_title="PKCE Login Notebook",
    auto_download=["ipynb", "html"],
)

###############
# Login Cells #
###############
get_accounts = None


@app.cell(hide_code=True)
def _():
    # Login Stub - click to view code
    import json
    import marimo as mo
    import requests
    import warnings
    import moutils
    from moutils.oauth import PKCEFlow
    from urllib.request import Request, urlopen

    debug = True
    warnings.filterwarnings("ignore", category=UserWarning, module="pkg_resources")
    warnings.filterwarnings("ignore", category=UserWarning, module="fanstatic")
    proxy = "https://api-proxy.notebooks.cloudflare.com"

    # Configure OAuth endpoints based on environment
    try:
        import js

        origin = js.eval("self.location?.origin")
        if debug: print(f"[DEBUG] WASM environment detected - origin: {origin}")

        if "localhost:8088" in origin:
            if debug: print("[DEBUG] Environment: Local WASM with Cloudflare Pages")
            oauth_config = {
                "logout_url": f"{origin}/oauth2/revoke",
                "redirect_uri": f"{origin}/oauth/callback",
                "token_url": f"{origin}/oauth2/token",
                "use_new_tab": True,
            }
        elif "localhost" in origin:
            if debug: print("[DEBUG] Environment: Local WASM (standard)")
            oauth_config = {
                "logout_url": "https://dash.cloudflare.com/oauth2/revoke",
                "redirect_uri": "https://auth.sandbox.marimo.app/oauth/sso-callback",
                "token_url": "https://dash.cloudflare.com/oauth2/token",
                "use_new_tab": False,
            }
        else:
            if debug: print("[DEBUG] Environment: Production WASM")
            oauth_config = {
                "logout_url": f"{origin}/oauth2/revoke",
                "redirect_uri": f"{origin}/oauth/callback",
                "token_url": f"{origin}/oauth2/token",
                "use_new_tab": True,
            }
    except AttributeError:
        if debug: print("[DEBUG] Environment: Local Python")
        oauth_config = {
            "logout_url": "https://dash.cloudflare.com/oauth2/revoke",
            "redirect_uri": "https://auth.sandbox.marimo.app/oauth/sso-callback",
            "token_url": "https://dash.cloudflare.com/oauth2/token",
            "use_new_tab": False,
        }

    oauth_config["proxy"] = proxy
    oauth_config["moutils_oauth_version"] = moutils.__version__

    # Debug OAuth config
    if debug:
        print("[DEBUG] OAuth configuration:")
        for key, value in oauth_config.items():
            print(f"  {key}: {value}")

    # Functions
    async def get_accounts(debug, token):
        # Check for valid token
        if not token or token.strip() == "":
            print("Please login using the button above")
            return []
        
        # Use the proxy for API calls in WASM environment to avoid CORS issues
        request_url = f"{proxy}/client/v4/accounts"
        headers = {"Authorization": f"Bearer {token}"}
        if debug:
            print("[DEBUG] get_accounts request URL:", request_url)
            print("[DEBUG] get_accounts headers:", headers)
            print("[DEBUG] get_accounts token (first 40 chars):", token[:40] + "..." if token else "None")
        from urllib.error import HTTPError

        try:
            request = Request(request_url, headers=headers)
            res = json.load(urlopen(request))
            return res.get("result", []) or []
        except HTTPError as e:
            print("Token invalid - Please login using the button above")
            if debug:
                print("[DEBUG] HTTPError:", e)
                print("[DEBUG] HTTPError response body:", e.read().decode())
            return []
        except Exception as e:
            print("Token invalid - Please login using the button above")
            if debug: print("[DEBUG] Exception:", e)
            return []

    if debug: print("[DEBUG] Helper functions cell completed")
    return Request, debug, get_accounts, js, json, key, mo, moutils, oauth_config, origin, PKCEFlow, proxy, requests, urlopen, value, warnings


@app.cell(hide_code=True)
def _(debug, oauth_config, PKCEFlow):
    # Login to Cloudflare - click to view code
    df = PKCEFlow(
        provider="cloudflare",
        client_id="ec85d9cd-ff12-4d96-a376-432dbcf0bbfc",
        logout_url=oauth_config.get("logout_url"),
        redirect_uri=oauth_config.get("redirect_uri"),
        token_url=oauth_config.get("token_url"),
        proxy=oauth_config.get("proxy"),
        use_new_tab=oauth_config.get("use_new_tab", True),
        debug=debug,
    )
    df
    return df


@app.cell(hide_code=True)
async def _(debug, df, get_accounts, mo):
    # Login Stub - click to view code
    if debug: print(f"[DEBUG] Access token (truncated to 20 chars): {df.access_token[:20] + '...' if df.access_token else 'None'}")
    accounts = await get_accounts(debug, df.access_token)
    radio = mo.ui.radio(options=[a["name"] for a in accounts], label="Select Account")
    return accounts, radio


@app.cell(hide_code=True)
def _(accounts, df, mo, radio):
    # Select Account Stub - click to view code
    account_name = radio.value if radio.value else None
    account_id = (
        next((a["id"] for a in accounts if a["name"] == account_name), None)
        if accounts
        else None
    )
    mo.hstack(
        [
            radio,
            mo.md(
                "Variables"
                "<pre>"
                f"account_id:      {account_id[:20] + '...' if account_id else 'None'}\n"
                f"account_name:    {account_name if account_name else 'None'}\n"
                f"df.access_token: {df.access_token[:20] + '...' if df.access_token else 'None'}\n"
                "</pre>"
            ),
        ]
    )
    return account_id, account_name


##################
# Notebook Cells #
##################
@app.cell
def _(account_id, account_name, df):
    print("Hello, World! 🌎")
    print(f"Cloudflare API Token:    {df.access_token[:20] + '...' if df.access_token else 'None'}")
    print(f"Cloudflare Account ID:   {account_id[:20] + '...' if account_id else 'None'}")
    print(f"Cloudflare Account Name: {account_name if account_name else 'None'}")
    return


if __name__ == "__main__":
    app.run()
