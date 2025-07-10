"""OAuth utilities for marimo notebooks, including device flow authentication."""

from pathlib import Path
import json
import time
from typing import Any, Callable, Dict, List, Optional, TypedDict, Union, cast
import urllib.parse
import urllib.request
import urllib.error
from collections import OrderedDict

import anywidget
import traitlets

import base64
import hashlib
import secrets
import requests
from urllib.parse import parse_qs, urlparse


class OAuthResponseDict(TypedDict, total=False):
    """Type for OAuth response dictionaries."""

    # Success fields
    device_code: str
    user_code: str
    verification_uri: str
    expires_in: int
    interval: int
    access_token: str
    token_type: str
    refresh_token: str
    refresh_token_expires_in: int
    scope: str

    # Error fields
    error: str
    error_description: str


DEFAULTS_FOR_PROVIDER = {
    "cloudflare": {
        "provider_name": "Cloudflare",
        "client_id": "ec85d9cd-ff12-4d96-a376-432dbcf0bbfc",
        "token_url": "https://dash.cloudflare.com/oauth2/token",
        "authorization_url": "https://dash.cloudflare.com/oauth2/auth",
        "logout_url": "https://dash.cloudflare.com/oauth2/revoke",
        "scopes": "notebook-examples:read",
        "proxy": "https://api-proxy.notebooks.cloudflare.com",
    },
    "github": {
        "provider_name": "GitHub",
        "verification_uri": "https://github.com/login/device",
        "device_code_url": "https://github.com/login/device/code",
        "logout_url": "https://github.com/login/oauth/revoke",
        "scopes": "repo user",
    },
    "google": {
        "provider_name": "Google",
        "verification_uri": "https://google.com/device",
        "device_code_url": "https://oauth2.googleapis.com/device/code",
        "token_url": "https://oauth2.googleapis.com/token",
        "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "logout_url": "https://oauth2.googleapis.com/revoke",
        "scopes": "https://www.googleapis.com/auth/userinfo.profile",
    },
    "microsoft": {
        "provider_name": "Microsoft",
        "verification_uri": "https://microsoft.com/devicelogin",
        "device_code_url": "https://login.microsoftonline.com/common/oauth2/v2.0/devicecode",
        "token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
        "authorization_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
        "logout_url": "https://login.microsoftonline.com/common/oauth2/v2.0/logout",
        "scopes": "user.read",
    },
}


class DeviceFlow(anywidget.AnyWidget):
    """Widget for OAuth 2.0 device flow authentication.

    This widget implements the OAuth 2.0 device flow, allowing users to authenticate
    with services like GitHub, Microsoft, Google, etc. using a device code.
    """

    _esm = Path(__file__).parent / "static" / "device_flow.js"
    _css = Path(__file__).parent / "static" / "device_flow.css"

    # Configuration properties
    provider = traitlets.Unicode().tag(sync=True)
    provider_name = traitlets.Unicode().tag(sync=True)
    client_id = traitlets.Unicode().tag(sync=True)
    icon = traitlets.Unicode().tag(sync=True)
    verification_uri = traitlets.Unicode().tag(sync=True)
    scopes = traitlets.Unicode().tag(sync=True)

    # Device flow state
    device_code = traitlets.Unicode("").tag(sync=True)
    user_code = traitlets.Unicode("").tag(sync=True)
    poll_interval = traitlets.Int(5).tag(sync=True)
    expires_in = traitlets.Int(900).tag(sync=True)

    # Authentication result
    access_token = traitlets.Unicode("").tag(sync=True)
    token_type = traitlets.Unicode("").tag(sync=True)
    refresh_token = traitlets.Unicode("").tag(sync=True)
    refresh_token_expires_in = traitlets.Int(0).tag(sync=True)
    authorized_scopes = traitlets.List(traitlets.Unicode(), []).tag(sync=True)

    # UI state
    status = traitlets.Unicode("not_started").tag(
        sync=True
    )  # not_started, initiating, pending, success, error
    error_message = traitlets.Unicode("").tag(sync=True)

    # Commands from frontend
    start_auth = traitlets.Bool(False).tag(sync=True)
    check_token = traitlets.Int(0).tag(sync=True)

    # URLs for OAuth endpoints
    device_code_url = traitlets.Unicode("").tag(sync=True)
    token_url = traitlets.Unicode("").tag(sync=True)
    logout_url = traitlets.Unicode("").tag(sync=True)

    # Events
    on_success = None
    on_error = None

    # For tracking expiry
    _expires_at = 0

    # Additional parameters
    repository_id: Optional[str] = None

    def __init__(
        self,
        *,
        provider: str,
        client_id: str,
        provider_name: Optional[str] = None,
        icon: Optional[str] = None,
        verification_uri: Optional[str] = None,
        device_code_url: Optional[str] = None,
        token_url: Optional[str] = None,
        logout_url: Optional[str] = None,
        scopes: Optional[str] = None,
        repository_id: Optional[str] = None,
        on_success: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
        debug: Optional[bool] = False,
    ):
        """Initialize the DeviceFlow widget.

        Args:
            provider: OAuth provider identifier (e.g., "github", "microsoft")
            client_id: OAuth client ID
            provider_name: Display name for the provider (defaults to capitalized provider)
            icon: Font Awesome icon class (e.g., "fab fa-github")
            verification_uri: URL where the user enters the device code
            device_code_url: URL to request device code (defaults to provider default)
            token_url: URL to request token (defaults to provider default)
            logout_url: URL to revoke tokens (defaults to provider default)
            scopes: Space-separated list of OAuth scopes to request (defaults to provider default)
            repository_id: GitHub-specific parameter to limit token to a specific repository
            on_success: Callback function when authentication succeeds
            on_error: Callback function when authentication fails
        """
        # Set default provider_name if not provided
        if provider_name is None:
            provider_name = provider.capitalize()

        default_options = DEFAULTS_FOR_PROVIDER.get(
            provider,
            {
                "provider_name": provider.capitalize(),
                "icon": "fas fa-key",
                "verification_uri": "",
                "device_code_url": "",
                "token_url": "",
                "logout_url": "",
                "scopes": "",
            },
        )

        # Set default icon based on provider if not specified
        if not icon:
            icon = default_options.get("icon", "fas fa-key")

        # Set default verification URI based on provider if not specified
        if not verification_uri:
            verification_uri = default_options.get("verification_uri", "")
        if not verification_uri:
            raise ValueError(f"Verification URI is required for provider: {provider}")

        # Set OAuth endpoint URLs
        if not device_code_url:
            device_code_url = default_options.get("device_code_url", "")
        if not device_code_url:
            raise ValueError(f"Device code URL is required for provider: {provider}")

        if not token_url:
            token_url = default_options.get("token_url", "")
        if not token_url:
            raise ValueError(f"Token URL is required for provider: {provider}")

        if not logout_url:
            logout_url = default_options.get("logout_url", "")
        if not logout_url:
            logout_url = "#logout"

        # Set default scopes based on provider if not specified
        if not scopes:
            scopes = default_options.get("scopes", "")

        # Store callbacks
        self.on_success = on_success
        self.on_error = on_error

        self.debug = debug
        self._log("Initializing DeviceFlow widget")

        # Register event handlers
        self.observe(self._handle_token_change, names=["access_token"])
        self.observe(self._handle_error_change, names=["error_message"])
        self.observe(self._handle_start_auth, names=["start_auth"])
        self.observe(self._handle_check_token, names=["check_token"])
        self._log(f"Registered event handlers for {provider}")

        # Store additional parameters
        self.repository_id = repository_id

        # Initialize widget with properties
        super().__init__(
            provider=provider,
            provider_name=provider_name,
            client_id=client_id,
            icon=icon,
            verification_uri=verification_uri,
            device_code_url=device_code_url,
            token_url=token_url,
            logout_url=logout_url,
            scopes=scopes,
        )

    def _log(self, message: str) -> None:
        """Log a message."""
        if self.debug:
            print(f"[moutils:oauth] {message}")

    def _handle_token_change(self, change: Dict[str, Any]) -> None:
        """Handle changes to the access_token property."""
        if self.debug:
            self._log(f"_handle_token_change called: change={change}, current status={self.status}")
        if change["new"]:
            self._log("Access token received, calling success callback")
            # Always update status to success to trigger UI update
            self.status = "success"
            token_data: Dict[str, Union[str, List[str], int]] = {
                "access_token": self.access_token,
                "token_type": self.token_type,
                "refresh_token": self.refresh_token,
                "scopes": self.authorized_scopes,
                "provider": self.provider,
            }
            if self.refresh_token_expires_in:
                token_data["refresh_token_expires_in"] = self.refresh_token_expires_in
            # Call success callback if provided
            if self.on_success:
                self.on_success(token_data)
            # Ensure we don't trigger another auth flow
            self.start_auth = False
            # Store token data for persistence (this will be handled by JavaScript)
            self._store_token_for_persistence()

    def _handle_error_change(self, change: Dict[str, Any]) -> None:
        """Handle changes to the error_message property."""
        if change["new"] and self.on_error:
            self._log(f"Error occurred: {change['new']}")
            self.on_error(change["new"])

    def _handle_start_auth(self, change: Dict[str, Any]) -> None:
        """Handle start_auth being set to True by the frontend."""
        if change["new"]:
            self._log("Start auth triggered from frontend")
            # Only start if we're not already in a success state
            if self.status != "success":
                # Reset to prevent repeated triggering
                self.start_auth = False
                # Start the authentication flow
                self.start_device_flow()
            else:
                # If we're already in success state, just reset the flag
                self.start_auth = False

    def _handle_check_token(self, change: Dict[str, Any]) -> None:
        """Handle check_token being incremented by the frontend."""
        if change["new"] > change["old"]:
            self._log(f"Check token triggered from frontend: {change['new']}")

            # Check if authentication flow has expired
            if time.time() > self._expires_at:
                self._log("Authentication flow expired")
                self.error_message = "Authentication timed out. Please try again."
                self.status = "error"
                return

            # Check token status
            self.check_token_status()

    def reset(self) -> None:
        """Reset the authentication state."""
        if self.debug:
            self._log(f"reset called. Current access_token={self.access_token}, status={self.status}")
        # Store configuration properties that should persist
        hostname = self.hostname
        port = self.port
        href = self.href
        proxy = self.proxy
        # Reset authentication state
        self.device_code = ""
        self.user_code = ""
        self.access_token = ""
        self.token_type = ""
        self.refresh_token = ""
        self.refresh_token_expires_in = 0
        self.authorized_scopes = []
        self.status = "not_started"
        self.error_message = ""
        self._expires_at = 0
        # Restore configuration properties
        self.hostname = hostname
        self.port = port
        self.href = href
        self.proxy = proxy

    def start_device_flow(self) -> None:
        """Start the device flow authentication process."""
        # Reset state
        self.reset()

        # Update status to show we're starting
        self.status = "initiating"
        self._log("Starting device flow authentication")

        try:
            # Request device code
            self._log("Requesting device code")
            device_code_response = self._request_device_code()

            # Check for errors
            if "error" in device_code_response:
                error_msg = device_code_response.get(
                    "error_description", device_code_response["error"]
                )
                self._log(f"Error in device code response: {error_msg}")
                self.error_message = f"Error requesting device code: {error_msg}"
                self.status = "error"
                return

            # Extract and update device info
            self.device_code = device_code_response.get("device_code", "")
            self.user_code = device_code_response.get("user_code", "")
            self.poll_interval = int(device_code_response.get("interval", 5))
            self.expires_in = int(device_code_response.get("expires_in", 900))
            self._expires_at = time.time() + self.expires_in
            self._log(
                f"Device code obtained. User code: {self.user_code}, expires in: {self.expires_in}s"
            )

            # Update verification URI if provided in response
            if "verification_uri" in device_code_response:
                self.verification_uri = device_code_response["verification_uri"]
                self._log(f"Verification URI updated to: {self.verification_uri}")

            # Update status to pending - waiting for user
            self.status = "pending"
            self._log("Status updated to pending, waiting for user authentication")

        except Exception as e:
            self._log(f"Exception during device flow start: {str(e)}")
            self.error_message = f"Error starting device flow: {str(e)}"
            self.status = "error"

    def check_token_status(self) -> None:
        """Check if the token has been authorized."""
        self._log("Checking token status")
        try:
            token_response = self._request_token()

            # Check for token
            if "access_token" in token_response:
                # Success - we have a token
                self._log("Access token received successfully")
                self.access_token = token_response.get("access_token", "")
                self.token_type = token_response.get("token_type", "bearer")
                self.refresh_token = token_response.get("refresh_token", "")

                # Store additional response data
                self.refresh_token_expires_in = token_response.get(
                    "refresh_token_expires_in", 0
                )

                # Parse scopes
                if "scope" in token_response:
                    self.authorized_scopes = token_response["scope"].split(" ")
                    self._log(f"Authorized scopes: {self.authorized_scopes}")

                # Check GitHub-specific token formats
                if (
                    self.provider == "github"
                    and self.access_token
                    and not self.access_token.startswith("ghu_")
                ):
                    self._log(
                        "Warning: GitHub access token doesn't start with expected prefix ghu_"
                    )
                if (
                    self.provider == "github"
                    and self.refresh_token
                    and not self.refresh_token.startswith("ghr_")
                ):
                    self._log(
                        "Warning: GitHub refresh token doesn't start with expected prefix ghr_"
                    )

                # Update status
                self.status = "success"
                self._log("Authentication successful")
                return

            # Check for errors
            if "error" in token_response:
                error = token_response["error"]

                # If authorization_pending, just continue
                if error == "authorization_pending":
                    self._log("Authorization still pending")
                    return

                # If slow_down, increase interval
                if error == "slow_down" and "interval" in token_response:
                    new_interval = int(token_response["interval"])
                    self._log(
                        f"Received slow_down response, increasing interval to {new_interval}s"
                    )
                    self.poll_interval = new_interval
                    return

                # Handle specific error types
                if error == "expired_token":
                    self._log("Device code has expired")
                    self.error_message = (
                        "Your authorization code has expired. Please try again."
                    )
                    self.status = "error"
                    return

                if error == "access_denied":
                    self._log("User denied access")
                    self.error_message = "Access was denied by the user."
                    self.status = "error"
                    return

                if error == "unsupported_grant_type":
                    self._log("Unsupported grant type")
                    self.error_message = (
                        "Unsupported grant type. This is likely a configuration issue."
                    )
                    self.status = "error"
                    return

                if error == "incorrect_client_credentials":
                    self._log("Incorrect client credentials")
                    self.error_message = (
                        "Invalid client ID. Please check your configuration."
                    )
                    self.status = "error"
                    return

                if error == "incorrect_device_code":
                    self._log("Incorrect device code")
                    self.error_message = "Invalid device code."
                    self.status = "error"
                    return

                if error == "device_flow_disabled":
                    self._log("Device flow disabled")
                    self.error_message = (
                        "Device flow is not enabled for this application."
                    )
                    self.status = "error"
                    return

                # Other errors - show error message
                error_description = token_response.get("error_description", error)
                self._log(f"Token error: {error_description}")
                self.error_message = f"Error: {error_description}"
                self.status = "error"

        except Exception as e:
            self._log(f"Exception during token check: {str(e)}")
            self.error_message = f"Error checking token status: {str(e)}"
            self.status = "error"

    def _request_device_code(self) -> OAuthResponseDict:
        """Request a device code from the OAuth provider."""
        try:
            url = f"{self.device_code_url}?client_id={self.client_id}"
            self._log(f"Requesting device code from {url}")

            # Set up request
            req = urllib.request.Request(
                url,
                method="POST",
                headers={
                    "Accept": "application/json",
                },
            )

            # Make request
            with urllib.request.urlopen(req) as response:
                response_data = response.read().decode("utf-8")
                self._log("Device code response received")

                # Parse response (could be JSON or URL-encoded)
                content_type = response.getheader("Content-Type", "")
                if "application/json" in content_type:
                    self._log("Parsing JSON response")
                    return json.loads(response_data)
                else:
                    # Parse URL-encoded response
                    self._log("Parsing URL-encoded response")
                    parsed_data: OAuthResponseDict = {}
                    for pair in response_data.split("&"):
                        if "=" in pair:
                            key, value = pair.split("=", 1)
                            parsed_data[urllib.parse.unquote(key)] = (
                                urllib.parse.unquote(value)
                            )
                    return parsed_data

        except Exception as e:
            self._log(f"Exception in device code request: {str(e)}")
            return {"error": "exception", "error_description": str(e)}

    def _request_token(self) -> OAuthResponseDict:
        """Request a token using the device code."""
        try:
            # Prepare request data
            data = {
                "client_id": self.client_id,
                "device_code": self.device_code,
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            }

            # Add repository_id if provided (GitHub-specific)
            if hasattr(self, "repository_id") and self.repository_id:
                data["repository_id"] = self.repository_id

            self._log(f"Requesting token from {self.token_url}")
            # Encode data for request
            encoded_data = urllib.parse.urlencode(data).encode("utf-8")

            # Set up request
            req = urllib.request.Request(
                self.token_url,
                data=encoded_data,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "application/json",
                },
            )

            # Smart fallback mechanism: try direct connection first, then proxy if needed
            response = None
            error_to_retry = None
            
            # First attempt: Try direct connection (no proxy)
            try:
                if self.debug:
                    self._log("Attempting direct connection to OAuth provider")
                
                # Make request without proxy
                with urllib.request.urlopen(req) as response:
                    response_data = response.read().decode("utf-8")
                    self._log("Token response received")

                    # Parse response (could be JSON or URL-encoded)
                    content_type = response.getheader("Content-Type", "")
                    if "application/json" in content_type:
                        self._log("Parsing JSON token response")
                        return json.loads(response_data)
                    else:
                        # Parse URL-encoded response
                        self._log("Parsing URL-encoded token response")
                        parsed_data: OAuthResponseDict = {}
                        for pair in response_data.split("&"):
                            if "=" in pair:
                                key, value = pair.split("=", 1)
                                parsed_data[urllib.parse.unquote(key)] = (
                                    urllib.parse.unquote(value)
                                )
                        return parsed_data
                
            except (urllib.error.URLError, ConnectionError, OSError) as e:
                # These errors suggest network/proxy issues that might be resolved with a proxy
                error_to_retry = e
                if self.debug:
                    self._log(f"Direct connection failed with {type(e).__name__}: {str(e)}")
                
            # If we have a proxy configured, try with proxy
            if hasattr(self, 'proxy') and self.proxy and self.proxy.strip():
                if self.debug:
                    self._log(f"Retrying with proxy: {self.proxy}")
                try:
                    # Format proxy URL properly
                    if self.proxy.startswith(('http://', 'https://')):
                        proxy_url = self.proxy
                    else:
                        # Assume HTTPS if no protocol specified
                        proxy_url = f"https://{self.proxy}"
                    if self.debug:
                        self._log(f"Formatted proxy URL: {proxy_url}")
                    if use_requests:
                        # Use requests with proxy
                        proxies = {'http': proxy_url, 'https': proxy_url}
                        response = requests.request(
                            method,
                            url,
                            data=data,
                            headers=headers,
                            proxies=proxies,
                            timeout=30
                        )
                        # Parse response
                        content_type = response.headers.get("Content-Type", "")
                        if "application/json" in content_type:
                            return response.json()
                        else:
                            # Parse URL-encoded response
                            response_text = response.text
                            parsed_data = {}
                            for pair in response_text.split("&"):
                                if "=" in pair:
                                    key, value = pair.split("=", 1)
                                    parsed_data[urllib.parse.unquote(key)] = urllib.parse.unquote(value)
                            return parsed_data
                    else:
                        # Use urllib with proxy
                        proxy_handler = urllib.request.ProxyHandler({'http': proxy_url, 'https': proxy_url})
                        opener = urllib.request.build_opener(proxy_handler)
                        urllib.request.install_opener(opener)
                        if method == "POST" and data:
                            encoded_data = urllib.parse.urlencode(data).encode("utf-8")
                            req = urllib.request.Request(url, data=encoded_data, headers=headers)
                        else:
                            req = urllib.request.Request(url, headers=headers)
                        with urllib.request.urlopen(req) as response:
                            response_data = response.read().decode("utf-8")
                            # Parse response
                            content_type = response.getheader("Content-Type", "")
                            if "application/json" in content_type:
                                return json.loads(response_data)
                            else:
                                # Parse URL-encoded response
                                parsed_data = {}
                                for pair in response_data.split("&"):
                                    if "=" in pair:
                                        key, value = pair.split("=", 1)
                                        parsed_data[urllib.parse.unquote(key)] = urllib.parse.unquote(value)
                                return parsed_data
                except Exception as proxy_error:
                    if self.debug:
                        self._log(f"Proxy connection also failed: {str(proxy_error)}")
                    # If both direct and proxy fail, raise the original error
                    raise error_to_retry
            else:
                # No proxy configured, raise the original error
                raise error_to_retry

        except urllib.error.HTTPError as e:
            self._log(f"HTTP error in token request: {e.code} {e.reason}")
            # Some providers return error details in the response body
            try:
                error_data = json.loads(e.read().decode("utf-8"))
                self._log(f"Error response details: {error_data}")
                return error_data
            except Exception:
                return {
                    "error": "http_error",
                    "error_description": f"HTTP error {e.code}: {e.reason}",
                }
        except Exception as e:
            self._log(f"Exception in token request: {str(e)}")
            return {"error": "request_error", "error_description": str(e)}

    def logout(self) -> None:
        """Handle OAuth logout."""
        self._log("Logging out")
        try:
            # Revoke the access token
            if self.access_token:
                self._log("Revoking access token")
                revoke_url = self.logout_url
                data = {
                    "client_id": self.client_id,
                    "token": self.access_token,
                    "token_type_hint": "access_token",
                }
                
                # Use the smart fallback helper method
                response_data = self._make_request_with_fallback(
                    url=revoke_url,
                    method="POST",
                    data=data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    use_requests=True
                )
                
                # Check if the response indicates success
                if "error" not in response_data:
                    self._log("Token revoked successfully")
                else:
                    self._log(f"Token revocation returned error: {response_data}")

        except requests.exceptions.HTTPError as e:
            self._log(f"HTTP error in token revocation: {e.response.status_code} {e.response.reason}")
        except Exception as e:
            self._log(f"Error during logout: {str(e)}")
        finally:
            # Reset all authentication state
            self.reset()
            # Clear token expiration to trigger JavaScript cleanup
            self.token_expires_in = 0
            # Update status to not_started
            self.status = "not_started"
            self._log("Logout complete")

    def __new__(cls, *args: Any, **kwargs: Any) -> Any:
        instance = super().__new__(cls)
        try:
            import marimo

            instance.__init__(*args, **kwargs)
            as_widget = marimo.ui.anywidget(instance)
            if getattr(instance, "debug", False):
                instance._log("Created marimo widget")
            return as_widget
        except (ImportError, ModuleNotFoundError):
            return instance


class PKCEFlow(anywidget.AnyWidget):
    """Widget for OAuth 2.0 PKCE flow authentication.

    This widget implements the OAuth 2.0 Authorization Code Flow with PKCE,
    allowing users to authenticate with services like GitHub, Microsoft, Google, etc.
    PKCE (Proof Key for Code Exchange) is a security extension to the Authorization Code flow
    that prevents authorization code interception attacks.
    """

    _esm = Path(__file__).parent / "static" / "pkce_flow.js"
    _css = Path(__file__).parent / "static" / "pkce_flow.css"

    # Configuration properties
    provider = traitlets.Unicode().tag(sync=True)
    provider_name = traitlets.Unicode().tag(sync=True)
    client_id = traitlets.Unicode().tag(sync=True)
    authorization_url = traitlets.Unicode().tag(sync=True)
    token_url = traitlets.Unicode().tag(sync=True)
    redirect_uri = traitlets.Unicode().tag(sync=True)
    scopes = traitlets.Unicode().tag(sync=True)
    logout_url = traitlets.Unicode().tag(sync=True)
    hostname = traitlets.Unicode("").tag(sync=True)
    port = traitlets.Unicode("").tag(sync=True)
    proxy = traitlets.Unicode("").tag(sync=True)
    href = traitlets.Unicode("").tag(sync=True)
    use_new_tab = traitlets.Bool(True).tag(sync=True)

    # PKCE state
    code_verifier = traitlets.Unicode("").tag(sync=True)
    code_challenge = traitlets.Unicode("").tag(sync=True)
    state = traitlets.Unicode("").tag(sync=True)
    authorization_code = traitlets.Unicode("").tag(sync=True)

    # Authentication result
    access_token = traitlets.Unicode("").tag(sync=True)
    token_type = traitlets.Unicode("").tag(sync=True)
    refresh_token = traitlets.Unicode("").tag(sync=True)
    refresh_token_expires_in = traitlets.Int(0).tag(sync=True)
    authorized_scopes = traitlets.List(traitlets.Unicode(), []).tag(sync=True)

    # UI state
    status = traitlets.Unicode("not_started").tag(
        sync=True
    )  # not_started, initiating, pending, success, error
    error_message = traitlets.Unicode("").tag(sync=True)

    # Commands from frontend
    start_auth = traitlets.Bool(False).tag(sync=True)
    handle_callback = traitlets.Unicode("").tag(sync=True)
    logout_requested = traitlets.Bool(False).tag(sync=True)
    
    # Token persistence
    token_expires_in = traitlets.Int(0).tag(sync=True)

    # Events
    on_success = None
    on_error = None

    def __init__(
        self,
        *,
        provider: str,
        client_id: Optional[str] = None,
        provider_name: Optional[str] = None,
        authorization_url: Optional[str] = None,
        token_url: Optional[str] = None,
        redirect_uri: Optional[str] = None,
        scopes: Optional[str] = None,
        logout_url: Optional[str] = None,
        proxy: Optional[str] = None,
        use_new_tab: Optional[bool] = None,
        additional_state: Optional[Callable[[], Dict[str, Any]]] = None,
        on_success: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
        debug: Optional[bool] = False,
    ):
        """Initialize the PKCEFlow widget.

        Args:
            provider: OAuth provider identifier (e.g., "github", "microsoft")
            client_id: OAuth client ID (optional, will use provider default if not provided)
            provider_name: Display name for the provider (defaults to capitalized provider)
            authorization_url: URL to start the authorization flow
            token_url: URL to exchange code for token
            redirect_uri: URL where the provider will redirect after authorization
            scopes: Space-separated list of OAuth scopes to request
            logout_url: URL to revoke tokens (defaults to provider default)
            proxy: Proxy URL to use for HTTP requests (e.g., "https://proxy.example.com")
            use_new_tab: Whether to open the authorization URL in a new tab (True) or same tab (False)
            on_success: Callback function when authentication succeeds
            on_error: Callback function when authentication fails
            debug: Whether to show debug information
        """
        # Set default provider_name if not provided
        if provider_name is None:
            provider_name = provider.capitalize()

        default_options = DEFAULTS_FOR_PROVIDER.get(
            provider,
            {
                "provider_name": provider.capitalize(),
                "authorization_url": "",
                "token_url": "",
                "logout_url": "",
                "scopes": "",
            },
        )

        # Set default client_id from provider defaults if not provided
        if not client_id:
            client_id = default_options.get("client_id", "")
        if not client_id:
            raise ValueError(f"Client ID is required for provider: {provider}")

        # Set OAuth endpoint URLs
        if not authorization_url:
            authorization_url = default_options.get("authorization_url", "")
        if not authorization_url:
            raise ValueError(f"Authorization URL is required for provider: {provider}")

        if not token_url:
            token_url = default_options.get("token_url", "")
        if not token_url:
            raise ValueError(f"Token URL is required for provider: {provider}")

        # Set default scopes based on provider if not specified
        if not scopes:
            scopes = default_options.get("scopes", "")

        # Set default logout URL based on provider if not specified
        if not logout_url:
            logout_url = default_options.get("logout_url", "")
        if not logout_url:
            raise ValueError(f"Logout URL is required for provider: {provider}")

        # Set default redirect URI if not provided
        if not redirect_uri:
            redirect_uri = "http://localhost:2718/oauth/callback"

        # Set default proxy from provider defaults if not provided
        if not proxy:
            proxy = default_options.get("proxy", "")

        # Store callbacks
        self.on_success = on_success
        self.on_error = on_error
        self.debug = debug
        self.additional_state = additional_state

        # Register event handlers
        self.observe(self._handle_token_change, names=["access_token"])
        self.observe(self._handle_error_change, names=["error_message"])
        self.observe(self._handle_start_auth, names=["start_auth"])
        self.observe(self._handle_callback, names=["handle_callback"])
        self.observe(self._handle_logout, names=["logout_requested"])

        # Initialize widget with properties
        super().__init__(
            provider=provider,
            provider_name=provider_name,
            client_id=client_id,
            authorization_url=authorization_url,  # Use the base URL without parameters
            token_url=token_url,
            redirect_uri=redirect_uri,
            scopes=scopes,
            logout_url=logout_url,
            proxy=proxy or "",
            use_new_tab=use_new_tab if use_new_tab is not None else True,
        )
        
        # Configure environment-specific URLs for Cloudflare
        self._configure_cloudflare_urls()

    def _log(self, message: str) -> None:
        """Log a message."""
        if self.debug:
            print(f"[moutils:oauth] {message}")

    def _configure_cloudflare_urls(self) -> None:
        """Configure Cloudflare URLs based on environment detection."""
        if self.provider != "cloudflare":
            return
            
        self._log("Configuring Cloudflare URLs based on environment")
        
        # Try to detect WASM environment
        try:
            import js
            origin = js.eval("self.location?.origin")
            self._log(f"WASM environment detected - origin: {origin}")
            
            if "localhost:8088" in origin:
                self._log("Environment: Local WASM with Cloudflare Pages")
                self.logout_url = f"{origin}/oauth2/revoke"
                self.redirect_uri = f"{origin}/oauth/callback"
                self.token_url = f"{origin}/oauth2/token"
                self.use_new_tab = True
            elif "localhost" in origin:
                self._log("Environment: Local WASM (standard)")
                # Use direct Cloudflare URLs for standard localhost
                self.logout_url = "https://dash.cloudflare.com/oauth2/revoke"
                self.redirect_uri = "https://auth.sandbox.marimo.app/oauth/sso-callback"
                self.token_url = "https://dash.cloudflare.com/oauth2/token"
                self.use_new_tab = False
            else:
                self._log("Environment: Production WASM")
                self.logout_url = f"{origin}/oauth2/revoke"
                self.redirect_uri = f"{origin}/oauth/callback"
                self.token_url = f"{origin}/oauth2/token"
                self.use_new_tab = True
        except (AttributeError, NameError):
            self._log("Environment: Local Python")
            # Use direct Cloudflare URLs for local Python
            self.logout_url = "https://dash.cloudflare.com/oauth2/revoke"
            self.redirect_uri = "https://auth.sandbox.marimo.app/oauth/sso-callback"
            self.token_url = "https://dash.cloudflare.com/oauth2/token"
            self.use_new_tab = False

    def _generate_code_verifier(self) -> str:
        """Generate a code verifier for PKCE."""
        # Using the same length as the JavaScript implementation
        code_verifier = secrets.token_urlsafe(96)
        return code_verifier

    def _generate_code_challenge(self, code_verifier: str) -> str:
        """Generate a code challenge from a code verifier."""
        sha256_hash = hashlib.sha256(code_verifier.encode("utf-8")).digest()
        code_challenge = (
            base64.urlsafe_b64encode(sha256_hash).decode("utf-8").rstrip("=")
        )
        return code_challenge

    def _generate_state(self) -> str:
        """Generate a state parameter appended to any additional state provided."""
        hostname = self.hostname
        sandbox_id = ""

        if self.debug:
            self._log(f"Generating state with hostname: {hostname}")

        # Handle localhost case
        if hostname == "localhost":
            port = self.port
            sandbox_id = f"{hostname}:{port}" if port else hostname
            if self.debug:
                self._log(f"Detected localhost, setting sandbox_id to: {sandbox_id}")

        # Handle sandbox.marimo.app format
        elif ".sandbox.marimo.app" in hostname:
            # Extract the random string before .sandbox.marimo.app
            parts = hostname.split(".sandbox.marimo.app")
            if parts and parts[0]:
                sandbox_id = parts[0]
                if self.debug:
                    self._log(
                        f"Detected sandbox.marimo.app, extracted sandbox_id: {sandbox_id}"
                    )

        # Otherwise fallback to hostname as sandbox_id
        else:
            sandbox_id = hostname
            if self.debug:
                self._log(
                    f"Fallback hostname for sandbox_id: {sandbox_id}"
                )

        state = OrderedDict([
            ("sandbox_id", sandbox_id),
            ("href", self.href),
            ("nonce", f"{secrets.token_urlsafe(16)}.{secrets.token_urlsafe(8)}"),
        ])
        if self.additional_state is not None:
            state.update(self.additional_state())

        if self.debug:
            self._log(f"Final state object: {state}")

        # Encode state to base64
        encoded_state = (
            base64.urlsafe_b64encode(json.dumps(state).encode()).decode().rstrip("=")
        )
        if self.debug:
            self._log(f"Encoded state: {encoded_state}")

        return encoded_state

    def start_pkce_flow(self) -> None:
        """Start the PKCE flow authentication process."""
        # Reset state
        self.reset()

        # Update status to show we're starting
        self.status = "initiating"
        self._log("Starting PKCE flow authentication")

        try:
            # Check if hostname is set
            if not self.hostname:
                self._log("Hostname not set, waiting for JavaScript initialization")
                self.error_message = "Hostname not set, please try again"
                self.status = "error"
                return

            # Generate new PKCE values
            self.code_verifier = self._generate_code_verifier()
            self.code_challenge = self._generate_code_challenge(self.code_verifier)
            self.state = self._generate_state()

            if self.debug:
                self._log(f"Generated state: {self.state}")

            # Parameters in exact order as the working example
            params = [
                ("response_type", "code"),
                ("client_id", self.client_id),
                ("redirect_uri", self.redirect_uri),
                ("scope", self.scopes),
                ("state", self.state),
                ("code_challenge", self.code_challenge),
                ("code_challenge_method", "S256"),
            ]

            # Build URL with parameters in exact order
            base_url = self.authorization_url.split("?")[
                0
            ]  # Get base URL without parameters
            query_string = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
            auth_url = f"{base_url}?{query_string}"
            if self.debug:
                # Pre-process the auth_url to escape single quotes for the HTML
                escaped_auth_url = auth_url.replace("'", "\\'")
                debug_info = f"""
                Base URL: {base_url}
                Query String: {query_string}
                Full Authorization URL: {auth_url}

                Generated HTML button code:
                <pre>
                <button
                    onclick="window.open('{escaped_auth_url}', '_blank')"
                    style="background-color: #f38020; color: black; border: none; padding: 10px 20px; font-size: 16px; cursor: pointer; border-radius: 4px;"
                >
                    Login <i class="fa-brands fa-cloudflare"></i>
                </button>
                </pre>
                """
                self._log(debug_info)

            # Update the authorization URL in the model
            self.authorization_url = auth_url

            # Update status to pending
            self.status = "pending"
            self._log("Status updated to pending, waiting for user authentication")

        except Exception as e:
            self._log(f"Exception during PKCE flow start: {str(e)}")
            self.error_message = f"Error starting PKCE flow: {str(e)}"
            self.status = "error"

    def _handle_token_change(self, change: Dict[str, Any]) -> None:
        """Handle changes to the access_token property."""
        if self.debug:
            self._log(f"_handle_token_change called: change={change}, current status={self.status}")
        if change["new"]:
            self._log("Access token received, calling success callback")
            # Always update status to success to trigger UI update
            self.status = "success"
            token_data: Dict[str, Union[str, List[str], int]] = {
                "access_token": self.access_token,
                "token_type": self.token_type,
                "refresh_token": self.refresh_token,
                "scopes": self.authorized_scopes,
                "provider": self.provider,
            }
            if self.refresh_token_expires_in:
                token_data["refresh_token_expires_in"] = self.refresh_token_expires_in
            # Call success callback if provided
            if self.on_success:
                self.on_success(token_data)
            # Ensure we don't trigger another auth flow
            self.start_auth = False
            # Store token data for persistence (this will be handled by JavaScript)
            self._store_token_for_persistence()

    def _store_token_for_persistence(self) -> None:
        """Store token data in the widget for JavaScript persistence."""
        if self.debug:
            self._log("Storing token data for persistence")
        
        # Set the token expiration time to trigger JavaScript storage
        # Most OAuth tokens expire in 1 hour (3600 seconds) if not specified
        expires_in = 3600  # Default to 1 hour
        
        # Try to get expiration from token response if available
        # This would need to be set when the token is received
        if hasattr(self, '_token_expires_in') and self._token_expires_in:
            expires_in = self._token_expires_in
        
        self.token_expires_in = expires_in

    def _handle_error_change(self, change: Dict[str, Any]) -> None:
        """Handle changes to the error_message property."""
        if change["new"] and self.on_error:
            self._log(f"Error occurred: {change['new']}")
            self.on_error(change["new"])

    def _handle_start_auth(self, change: Dict[str, Any]) -> None:
        """Handle start_auth being set to True by the frontend."""
        if change["new"]:
            # Only start if we're not already in a success state
            if self.status != "success":
                self.start_auth = False
                self._log("Start auth triggered from frontend")
                self.start_pkce_flow()
            else:
                self.start_auth = False

    def _handle_callback(self, change: Dict[str, Any]) -> None:
        """Handle callback URL from the frontend."""
        if change["new"]:
            self._log("Callback URL received from frontend")
            callback_url = change["new"]

            # Parse callback URL
            parsed_url = urlparse(callback_url)
            query_params = parse_qs(parsed_url.query)

            # Check for errors
            if "error" in query_params:
                error = query_params["error"][0]
                error_description = query_params.get("error_description", [error])[0]
                self._log(f"Error in callback: {error} - {error_description}")
                self.error_message = f"Error: {error_description}"
                self.status = "error"
                self.start_auth = False
                return

            # Verify state
            if "state" not in query_params:
                self._log("No state parameter in callback")
                self.error_message = "No state parameter received"
                self.status = "error"
                self.start_auth = False
                return

            received_state = query_params["state"][0]
            if self.debug:
                self._log(f"Received state: {received_state}")

            # Get authorization code
            if "code" not in query_params:
                self._log("No authorization code in callback")
                self.error_message = "No authorization code received"
                self.status = "error"
                self.start_auth = False
                return

            self.authorization_code = cast(str, query_params["code"][0])
            self._log("Authorization code received, exchanging for token")

            # Exchange code for token
            token_response = self._exchange_code_for_token()

            # Check for token
            if "access_token" in token_response:
                # Success - we have a token
                self._log("Access token received successfully")
                self.access_token = token_response.get("access_token", "")
                self.token_type = token_response.get("token_type", "bearer")
                self.refresh_token = token_response.get("refresh_token", "")

                # Store additional response data
                self.refresh_token_expires_in = token_response.get(
                    "refresh_token_expires_in", 0
                )
                
                # Store token expiration time for persistence
                self._token_expires_in = token_response.get("expires_in", 3600)

                # Parse scopes
                if "scope" in token_response:
                    self.authorized_scopes = token_response["scope"].split(" ")
                    self._log(f"Authorized scopes: {self.authorized_scopes}")

                # Update status and ensure start_auth is False
                self.status = "success"
                self.start_auth = False
                self._log("Authentication successful")
                
                # Store token data for persistence
                self._store_token_for_persistence()
                return

            # Handle errors
            if "error" in token_response:
                error = token_response["error"]
                error_description = token_response.get("error_description", error)
                self._log(f"Token error: {error_description}")
                self.error_message = f"Error: {error_description}"
                self.status = "error"
                self.start_auth = False

    def _handle_logout(self, change: Dict[str, Any]) -> None:
        """Handle logout being set to True by the frontend."""
        if change["new"]:
            self._log("Logout triggered from frontend")
            self.logout_requested = False
            self.logout()

    def reset(self) -> None:
        """Reset the authentication state."""
        if self.debug:
            self._log(f"reset called. Current access_token={self.access_token}, status={self.status}")
        # Store configuration properties that should persist
        hostname = self.hostname
        port = self.port
        href = self.href
        proxy = self.proxy
        # Reset authentication state
        self.code_verifier = ""
        self.code_challenge = ""
        self.state = ""
        self.authorization_code = ""
        self.access_token = ""
        self.token_type = ""
        self.refresh_token = ""
        self.refresh_token_expires_in = 0
        self.token_expires_in = 0
        self.authorized_scopes = []
        self.status = "not_started"
        self.error_message = ""
        # Restore configuration properties
        self.hostname = hostname
        self.port = port
        self.href = href
        self.proxy = proxy

    def _make_request_with_fallback(self, url: str, method: str = "POST", data: Optional[Dict[str, Any]] = None, 
                                   headers: Optional[Dict[str, str]] = None, 
                                   use_requests: bool = True) -> Dict[str, Any]:
        """Make an HTTP request with smart fallback: try direct connection first, then proxy if needed.
        
        Args:
            url: The URL to request
            method: HTTP method (GET, POST, etc.)
            data: Request data (for POST requests)
            headers: Request headers
            use_requests: Whether to use requests library (True) or urllib (False)
            
        Returns:
            Parsed response data
            
        Raises:
            Exception: If both direct and proxy connections fail
        """
        if headers is None:
            headers = {}
        if data is None:
            data = {}
            
        if self.debug:
            self._log(f"Making {method} request to {url} with fallback")
        
        # If we have a proxy configured, try with proxy first
        tried_proxy = False
        error_to_retry = None
        if hasattr(self, 'proxy') and self.proxy and self.proxy.strip():
            if self.debug:
                self._log(f"Trying proxy first: {self.proxy}")
            try:
                # Format proxy URL properly
                if self.proxy.startswith(('http://', 'https://')):
                    proxy_url = self.proxy
                else:
                    # Assume HTTPS if no protocol specified
                    proxy_url = f"https://{self.proxy}"
                if self.debug:
                    self._log(f"Formatted proxy URL: {proxy_url}")
                if use_requests:
                    # Use requests with proxy
                    proxies = {'http': proxy_url, 'https': proxy_url}
                    response = requests.request(
                        method,
                        url,
                        data=data,
                        headers=headers,
                        proxies=proxies,
                        timeout=30
                    )
                    # Parse response
                    content_type = response.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        return response.json()
                    else:
                        # Parse URL-encoded response
                        response_text = response.text
                        parsed_data = {}
                        for pair in response_text.split("&"):
                            if "=" in pair:
                                key, value = pair.split("=", 1)
                                parsed_data[urllib.parse.unquote(key)] = urllib.parse.unquote(value)
                        return parsed_data
                else:
                    # Use urllib with proxy
                    proxy_handler = urllib.request.ProxyHandler({'http': proxy_url, 'https': proxy_url})
                    opener = urllib.request.build_opener(proxy_handler)
                    urllib.request.install_opener(opener)
                    if method == "POST" and data:
                        encoded_data = urllib.parse.urlencode(data).encode("utf-8")
                        req = urllib.request.Request(url, data=encoded_data, headers=headers)
                    else:
                        req = urllib.request.Request(url, headers=headers)
                    with urllib.request.urlopen(req) as response:
                        response_data = response.read().decode("utf-8")
                        # Parse response
                        content_type = response.getheader("Content-Type", "")
                        if "application/json" in content_type:
                            return json.loads(response_data)
                        else:
                            # Parse URL-encoded response
                            parsed_data = {}
                            for pair in response_data.split("&"):
                                if "=" in pair:
                                    key, value = pair.split("=", 1)
                                    parsed_data[urllib.parse.unquote(key)] = urllib.parse.unquote(value)
                            return parsed_data
            except Exception as proxy_error:
                tried_proxy = True
                error_to_retry = proxy_error
                if self.debug:
                    self._log(f"Proxy connection failed: {str(proxy_error)}. Falling back to direct connection.")

        # Try direct connection (no proxy) if proxy is not set or failed
        try:
            if self.debug:
                self._log("Attempting direct connection (no proxy)")
            if use_requests:
                response = requests.request(
                    method,
                    url,
                    data=data,
                    headers=headers,
                    proxies=None,  # No proxy for direct connection
                    timeout=30
                )
                content_type = response.headers.get("Content-Type", "")
                if "application/json" in content_type:
                    return response.json()
                else:
                    response_text = response.text
                    parsed_data = {}
                    for pair in response_text.split("&"):
                        if "=" in pair:
                            key, value = pair.split("=", 1)
                            parsed_data[urllib.parse.unquote(key)] = urllib.parse.unquote(value)
                    return parsed_data
            else:
                if method == "POST" and data:
                    encoded_data = urllib.parse.urlencode(data).encode("utf-8")
                    req = urllib.request.Request(url, data=encoded_data, headers=headers)
                else:
                    req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req) as response:
                    response_data = response.read().decode("utf-8")
                    content_type = response.getheader("Content-Type", "")
                    if "application/json" in content_type:
                        return json.loads(response_data)
                    else:
                        parsed_data = {}
                        for pair in response_data.split("&"):
                            if "=" in pair:
                                key, value = pair.split("=", 1)
                                parsed_data[urllib.parse.unquote(key)] = urllib.parse.unquote(value)
                        return parsed_data
        except Exception as direct_error:
            if tried_proxy:
                if self.debug:
                    self._log(f"Both proxy and direct connection failed. Raising proxy error: {str(error_to_retry)}")
                raise error_to_retry
            else:
                if self.debug:
                    self._log(f"Direct connection failed: {str(direct_error)}")
                raise direct_error

    def _exchange_code_for_token(self) -> Dict[str, Any]:
        """Exchange the authorization code for tokens."""
        try:
            # Prepare request data
            data: dict[str, str] = {
                "grant_type": "authorization_code",
                "code": self.authorization_code,
                "redirect_uri": self.redirect_uri,
                "client_id": self.client_id,
                "code_verifier": self.code_verifier,
            }

            if self.debug:
                self._log(f"Token request data: {data}")

            self._log(f"Exchanging code for token at {self.token_url}")
            
            # Set up headers
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
                "Accept-Encoding": "gzip, deflate",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9",
                "Origin": self.redirect_uri.split("/oauth/callback")[0],
                "Referer": self.authorization_url,
                "Connection": "keep-alive",
            }
            
            # Use the smart fallback helper method
            return self._make_request_with_fallback(
                url=self.token_url,
                method="POST",
                data=data,
                headers=headers,
                use_requests=True
            )

        except requests.exceptions.HTTPError as e:
            self._log(f"HTTP error in token request: {e.response.status_code} {e.response.reason}")
            try:
                error_text = e.response.text
                self._log(f"Error response body: {error_text}")

                # Check if this is a Cloudflare challenge
                if "Just a moment..." in error_text and "Cloudflare" in error_text:
                    self._log("Detected Cloudflare challenge")
                    return {
                        "error": "cloudflare_challenge",
                        "error_description": "Cloudflare security challenge detected. Please try again in a few minutes.",
                    }

                try:
                    error_json = e.response.json()
                    self._log(f"Error response details: {error_json}")
                    return error_json
                except ValueError:
                    self._log("Error response is not JSON")
                    return {
                        "error": "http_error",
                        "error_description": f"HTTP error {e.response.status_code}: {e.response.reason}",
                        "error_details": error_text,
                    }
            except Exception as e2:
                self._log(f"Error reading error response: {str(e2)}")
                return {
                    "error": "http_error",
                    "error_description": f"HTTP error {e.response.status_code}: {e.response.reason}",
                }
        except Exception as e:
            self._log(f"Exception in token request: {str(e)}")
            return {"error": "request_error", "error_description": str(e)}

    def logout(self) -> None:
        """Handle OAuth logout."""
        self._log("Logging out")
        try:
            # Revoke the access token
            if self.access_token:
                self._log("Revoking access token")
                revoke_url = self.logout_url
                data = {
                    "client_id": self.client_id,
                    "token": self.access_token,
                    "token_type_hint": "access_token",
                }
                
                # Use the smart fallback helper method
                response_data = self._make_request_with_fallback(
                    url=revoke_url,
                    method="POST",
                    data=data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    use_requests=True
                )
                
                # Check if the response indicates success
                if "error" not in response_data:
                    self._log("Token revoked successfully")
                else:
                    self._log(f"Token revocation returned error: {response_data}")

        except requests.exceptions.HTTPError as e:
            self._log(f"HTTP error in token revocation: {e.response.status_code} {e.response.reason}")
        except Exception as e:
            self._log(f"Error during logout: {str(e)}")
        finally:
            # Reset all authentication state
            self.reset()
            # Clear token expiration to trigger JavaScript cleanup
            self.token_expires_in = 0
            # Update status to not_started
            self.status = "not_started"
            self._log("Logout complete")

    def __new__(cls, *args: Any, **kwargs: Any) -> Any:
        instance = super().__new__(cls)
        try:
            import marimo

            instance.__init__(*args, **kwargs)
            as_widget = marimo.ui.anywidget(instance)
            if getattr(instance, "debug", False):
                instance._log("Created marimo widget")
            return as_widget
        except (ImportError, ModuleNotFoundError):
            return instance
