"""OAuth utilities for marimo notebooks, including device flow authentication."""

from pathlib import Path
import json
import time
from typing import Any, Callable, Dict, List, Optional, TypedDict, Union
import urllib.parse
import urllib.request
import urllib.error

import anywidget
import traitlets


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
    "github": {
        "provider_name": "GitHub",
        "icon": "fab fa-github",
        "verification_uri": "https://github.com/login/device",
        "device_code_url": "https://github.com/login/device/code",
        "token_url": "https://github.com/login/oauth/access_token",
        "scopes": "repo user",
    },
    "microsoft": {
        "provider_name": "Microsoft",
        "icon": "fab fa-microsoft",
        "verification_uri": "https://microsoft.com/devicelogin",
        "device_code_url": "https://login.microsoftonline.com/common/oauth2/v2.0/devicecode",
        "token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
        "scopes": "user.read",
    },
    "google": {
        "provider_name": "Google",
        "icon": "fab fa-google",
        "verification_uri": "https://google.com/device",
        "device_code_url": "https://oauth2.googleapis.com/device/code",
        "token_url": "https://oauth2.googleapis.com/token",
        "scopes": "https://www.googleapis.com/auth/userinfo.profile",
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
            scopes=scopes,
        )

    def _log(self, message: str) -> None:
        """Log a message."""
        if self.debug:
            print(f"[moutils:oauth] {message}")

    def _handle_token_change(self, change: Dict[str, Any]) -> None:
        """Handle changes to the access_token property."""
        if change["new"] and self.on_success:
            self._log("Access token received, calling success callback")
            token_data: Dict[str, Union[str, List[str], int]] = {
                "access_token": self.access_token,
                "token_type": self.token_type,
                "refresh_token": self.refresh_token,
                "scopes": self.authorized_scopes,
                "provider": self.provider,
            }

            # Add refresh_token_expires_in if available
            if (
                hasattr(self, "refresh_token_expires_in")
                and self.refresh_token_expires_in
            ):
                token_data["refresh_token_expires_in"] = self.refresh_token_expires_in

            self.on_success(token_data)

    def _handle_error_change(self, change: Dict[str, Any]) -> None:
        """Handle changes to the error_message property."""
        if change["new"] and self.on_error:
            self._log(f"Error occurred: {change['new']}")
            self.on_error(change["new"])

    def _handle_start_auth(self, change: Dict[str, Any]) -> None:
        """Handle start_auth being set to True by the frontend."""
        if change["new"]:
            self._log("Start auth triggered from frontend")
            # Reset to prevent repeated triggering
            self.start_auth = False

            # Start the authentication flow
            self.start_device_flow()

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
        self._log("Resetting authentication state")
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

            # Make request
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
