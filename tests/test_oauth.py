"""Tests for OAuth device flow implementation."""

import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import re
import time
from typing import Dict, Any, Optional, List, Tuple

from moutils.oauth import DeviceFlow


class MockOAuthHandler(BaseHTTPRequestHandler):
    """Mock HTTP handler for OAuth device flow testing."""

    # Class variables to control behavior
    device_codes: Dict[str, Dict[str, Any]] = {}
    authorized_codes: List[str] = []
    return_json: bool = True
    should_fail: bool = False
    fail_with: Dict[str, str] = {}
    slow_down: bool = False

    def do_POST(self):
        """Handle POST requests for device code and token endpoints."""
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length).decode("utf-8")
        parsed_data = urllib.parse.parse_qs(post_data)

        # Convert lists to single values for easier handling
        params = {k: v[0] for k, v in parsed_data.items()}

        # Set response headers based on configuration
        content_type = (
            "application/json"
            if self.return_json
            else "application/x-www-form-urlencoded"
        )
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.end_headers()

        # If configured to fail, return error response
        if self.should_fail:
            self._send_response(self.fail_with)
            return

        # Handle device code endpoint
        if re.search(r"/device/code$", self.path):
            response = self._handle_device_code(params)
            self._send_response(response)

        # Handle token endpoint
        elif re.search(r"/token$|/access_token$", self.path):
            response = self._handle_token_request(params)
            self._send_response(response)

        else:
            # Unknown endpoint
            error_resp = {
                "error": "invalid_request",
                "error_description": "Unknown endpoint",
            }
            self._send_response(error_resp)

    def _handle_device_code(self, params: Dict[str, str]) -> Dict[str, Any]:
        """Process device code request and return response."""
        client_id = params.get("client_id", "")

        # Generate a device code and user code
        device_code = f"device_{client_id}_{int(time.time())}"
        user_code = f"USER{int(time.time()) % 10000}"

        # Store the device code info
        self.device_codes[device_code] = {
            "client_id": client_id,
            "user_code": user_code,
            "created_at": time.time(),
        }

        # Create response
        response = {
            "device_code": device_code,
            "user_code": user_code,
            "verification_uri": "https://example.com/device",
            "expires_in": 900,  # 15 minutes
            "interval": 5,
        }

        return response

    def _handle_token_request(self, params: Dict[str, str]) -> Dict[str, Any]:
        """Process token request and return response."""
        device_code = params.get("device_code", "")
        grant_type = params.get("grant_type", "")

        # Verify grant type
        if grant_type != "urn:ietf:params:oauth:grant-type:device_code":
            return {
                "error": "unsupported_grant_type",
                "error_description": "Invalid grant type",
            }

        # Check if device code exists
        if device_code not in self.device_codes:
            return {
                "error": "invalid_grant",
                "error_description": "Invalid device code",
            }

        # If slow_down flag is set, tell client to slow down
        if self.slow_down:
            return {"error": "slow_down", "interval": 10}

        # Check if code is authorized
        if device_code in self.authorized_codes:
            # Return access token
            return {
                "access_token": f"test_access_token_{device_code}",
                "token_type": "bearer",
                "refresh_token": f"test_refresh_token_{device_code}",
                "refresh_token_expires_in": 7776000,  # 90 days
                "scope": "repo user",
            }
        else:
            # Not yet authorized
            return {
                "error": "authorization_pending",
                "error_description": "The user has not yet authorized the app",
            }

    def _send_response(self, data: Dict[str, Any]) -> None:
        """Send response in the configured format (JSON or URL-encoded)."""
        if self.return_json:
            response_bytes = json.dumps(data).encode("utf-8")
        else:
            # Convert to URL-encoded
            response_parts = []
            for key, value in data.items():
                if value is not None:
                    encoded_key = urllib.parse.quote(str(key))
                    encoded_value = urllib.parse.quote(str(value))
                    response_parts.append(f"{encoded_key}={encoded_value}")
            response_bytes = "&".join(response_parts).encode("utf-8")

        self.wfile.write(response_bytes)


class MockOAuthServer:
    """Mock OAuth server for testing the device flow."""

    def __init__(self, host: str = "localhost", port: int = 0):
        """Initialize the server with the given host and port."""
        self.host = host
        self.port = port
        self.server = HTTPServer((host, port), MockOAuthHandler)
        self.server_thread = None
        self.actual_port = self.server.server_port

    def start(self):
        """Start the server in a separate thread."""
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()

    def stop(self):
        """Stop the server."""
        if self.server:
            self.server.shutdown()
            self.server.server_close()

    def reset(self):
        """Reset the server state."""
        MockOAuthHandler.device_codes = {}
        MockOAuthHandler.authorized_codes = []
        MockOAuthHandler.return_json = True
        MockOAuthHandler.should_fail = False
        MockOAuthHandler.fail_with = {}
        MockOAuthHandler.slow_down = False

    def authorize_device_code(self, device_code: str):
        """Simulate user authorizing a device code."""
        if device_code in MockOAuthHandler.device_codes:
            MockOAuthHandler.authorized_codes.append(device_code)
            return True
        return False

    def get_urls(self) -> Tuple[str, str]:
        """Get the device code and token URLs for this server."""
        base_url = f"http://{self.host}:{self.actual_port}"
        device_code_url = f"{base_url}/device/code"
        token_url = f"{base_url}/token"
        return device_code_url, token_url

    def configure(
        self,
        return_json: bool = True,
        should_fail: bool = False,
        fail_with: Optional[Dict[str, str]] = None,
        slow_down: bool = False,
    ):
        """Configure server behavior for testing different scenarios."""
        MockOAuthHandler.return_json = return_json
        MockOAuthHandler.should_fail = should_fail
        MockOAuthHandler.fail_with = fail_with or {}
        MockOAuthHandler.slow_down = slow_down


class TestDeviceFlow:
    """Test cases for the DeviceFlow class."""

    @classmethod
    def setup_class(cls):
        """Set up the OAuth server once for all tests."""
        cls.server = MockOAuthServer()
        cls.server.start()
        cls.device_code_url, cls.token_url = cls.server.get_urls()

    @classmethod
    def teardown_class(cls):
        """Tear down the OAuth server after all tests."""
        cls.server.stop()

    def setup_method(self):
        """Set up before each test."""
        self.server.reset()
        self.success_called = False
        self.error_called = False
        self.last_token_data: Optional[Dict[str, Any]] = None
        self.last_error: Optional[str] = None

    def on_success(self, token_data: Dict[str, Any]) -> None:
        """Success callback for DeviceFlow."""
        self.success_called = True
        self.last_token_data = token_data

    def on_error(self, error_message: str) -> None:
        """Error callback for DeviceFlow."""
        self.error_called = True
        self.last_error = error_message

    def test_initialization(self):
        """Test that the DeviceFlow widget initializes correctly."""
        flow = DeviceFlow(
            provider="test_provider",
            client_id="test_client_id",
            provider_name="Test Provider",
            icon="fas fa-test",
            verification_uri="https://example.com/device",
            device_code_url=self.device_code_url,
            token_url=self.token_url,
            scopes="test_scope",
            on_success=self.on_success,
            on_error=self.on_error,
            debug=True,
        )

        # Check initialization values
        assert flow.provider == "test_provider"
        assert flow.client_id == "test_client_id"
        assert flow.provider_name == "Test Provider"
        assert flow.icon == "fas fa-test"
        assert flow.verification_uri == "https://example.com/device"
        assert flow.device_code_url == self.device_code_url
        assert flow.token_url == self.token_url
        assert flow.scopes == "test_scope"
        assert flow.status == "not_started"

    def test_device_flow_success_json(self):
        """Test successful device flow with JSON responses."""
        # Configure server to return JSON
        self.server.configure(return_json=True)

        # Create flow
        flow = DeviceFlow(
            provider="test_provider",
            client_id="test_client_id",
            verification_uri="https://example.com/device",
            device_code_url=self.device_code_url,
            token_url=self.token_url,
            on_success=self.on_success,
            on_error=self.on_error,
            debug=True,
        )

        # Start device flow
        flow.start_device_flow()

        # Verify state after device code request
        assert flow.status == "pending"
        assert flow.device_code != ""
        assert flow.user_code != ""

        # Check token status - should be pending
        flow.check_token_status()
        assert flow.status == "pending"

        # Authorize the device code
        self.server.authorize_device_code(flow.device_code)

        # Check token status again - should succeed
        flow.check_token_status()

        # Verify success state
        assert flow.status == "success"
        assert flow.access_token != ""
        assert flow.refresh_token != ""
        assert self.success_called
        assert not self.error_called

        # Verify token data
        assert self.last_token_data is not None
        if self.last_token_data:  # Type narrowing for mypy
            assert self.last_token_data["provider"] == "test_provider"
            assert "access_token" in self.last_token_data
            assert "refresh_token" in self.last_token_data

    def test_device_flow_success_form_encoded(self):
        """Test successful device flow with form-encoded responses."""
        # Configure server to return form-encoded data
        self.server.configure(return_json=False)

        # Create flow
        flow = DeviceFlow(
            provider="test_provider",
            client_id="test_client_id",
            verification_uri="https://example.com/device",
            device_code_url=self.device_code_url,
            token_url=self.token_url,
            on_success=self.on_success,
            on_error=self.on_error,
            debug=True,
        )

        # Start device flow
        flow.start_device_flow()

        # Verify state after device code request
        assert flow.status == "pending"

        # Authorize the device code
        self.server.authorize_device_code(flow.device_code)

        # Check token status again - should succeed
        flow.check_token_status()

        # Verify success state
        assert flow.status == "success"
        assert self.success_called

    def test_device_flow_error(self):
        """Test device flow with server error."""
        # Configure server to fail
        self.server.configure(
            should_fail=True,
            fail_with={
                "error": "server_error",
                "error_description": "Test server error",
            },
        )

        # Create flow
        flow = DeviceFlow(
            provider="test_provider",
            client_id="test_client_id",
            verification_uri="https://example.com/device",
            device_code_url=self.device_code_url,
            token_url=self.token_url,
            on_success=self.on_success,
            on_error=self.on_error,
            debug=True,
        )

        # Start device flow - should fail
        flow.start_device_flow()

        # Verify error state
        assert flow.status == "error"
        assert self.error_called
        assert not self.success_called

    def test_slow_down_response(self):
        """Test the slow_down error response."""
        # Configure server for normal operation first
        self.server.configure(return_json=True)

        # Create flow
        flow = DeviceFlow(
            provider="test_provider",
            client_id="test_client_id",
            verification_uri="https://example.com/device",
            device_code_url=self.device_code_url,
            token_url=self.token_url,
            on_success=self.on_success,
            on_error=self.on_error,
            debug=True,
        )

        # Start device flow
        flow.start_device_flow()

        # Get original poll interval
        original_interval = flow.poll_interval

        # Configure server to return slow_down
        self.server.configure(return_json=True, slow_down=True)

        # Check token status - should update poll interval
        flow.check_token_status()

        # Verify poll interval is updated
        assert flow.poll_interval > original_interval

    def test_reset(self):
        """Test the reset method."""
        # Configure server
        self.server.configure(return_json=True)

        # Create flow
        flow = DeviceFlow(
            provider="test_provider",
            client_id="test_client_id",
            verification_uri="https://example.com/device",
            device_code_url=self.device_code_url,
            token_url=self.token_url,
            on_success=self.on_success,
            on_error=self.on_error,
            debug=True,
        )

        # Start device flow
        flow.start_device_flow()

        # Verify state after device code request
        assert flow.status == "pending"
        assert flow.device_code != ""

        # Reset the flow
        flow.reset()

        # Verify reset state
        assert flow.status == "not_started"
        assert flow.device_code == ""
        assert flow.user_code == ""
        assert flow.access_token == ""
        assert flow.error_message == ""
