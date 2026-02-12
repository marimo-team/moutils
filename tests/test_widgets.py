"""Tests for widget initialization and JS validity."""

import subprocess
from pathlib import Path

import anywidget
import pytest

from moutils import (
    ColorScheme,
    ViewportSize,
    OnlineStatus,
    PageVisibility,
    Geolocation,
    CameraCapture,
    Notification,
    KeyboardShortcut,
    URLHash,
    URLPath,
    URLInfo,
    DOMQuery,
    CookieManager,
    StorageItem,
    CopyToClipboard,
    PrintPageButton,
    ScreenshotButton,
)

STATIC_DIR = Path(__file__).parent.parent / "src" / "moutils" / "static"


def _make(cls):
    """Instantiate a widget class bypassing the headless/__new__ wrapper."""
    w = anywidget.AnyWidget.__new__(cls)
    w.__init__()
    return w


# --- Initialization tests ---


class TestColorScheme:
    def test_init_defaults(self):
        w = _make(ColorScheme)
        assert w.scheme == "light"
        assert w.prefers_dark is False

    def test_esm_path_exists(self):
        assert (STATIC_DIR / "colorscheme.js").exists()


class TestViewportSize:
    def test_init_defaults(self):
        w = _make(ViewportSize)
        assert w.width == 0
        assert w.height == 0

    def test_esm_path_exists(self):
        assert (STATIC_DIR / "viewport.js").exists()


class TestOnlineStatus:
    def test_init_defaults(self):
        w = _make(OnlineStatus)
        assert w.online is True

    def test_esm_path_exists(self):
        assert (STATIC_DIR / "online.js").exists()


class TestPageVisibility:
    def test_init_defaults(self):
        w = _make(PageVisibility)
        assert w.visible is True
        assert w.state == "visible"

    def test_esm_path_exists(self):
        assert (STATIC_DIR / "visibility.js").exists()


class TestGeolocation:
    def test_init_defaults(self):
        w = _make(Geolocation)
        assert w.latitude == 0.0
        assert w.longitude == 0.0
        assert w.accuracy == 0.0
        assert w.error == ""
        assert w.enabled is False

    def test_esm_path_exists(self):
        assert (STATIC_DIR / "geolocation.js").exists()


class TestCameraCapture:
    def test_init_defaults(self):
        w = _make(CameraCapture)
        assert w.image_data == ""
        assert w.width == 640
        assert w.height == 480
        assert w.enabled is False

    def test_esm_path_exists(self):
        assert (STATIC_DIR / "camera.js").exists()

    def test_css_path_exists(self):
        assert (STATIC_DIR / "camera.css").exists()


class TestNotification:
    def test_init_defaults(self):
        w = _make(Notification)
        assert w.title == ""
        assert w.body == ""
        assert w.icon == ""
        assert w.permission == "default"
        assert w.send is False

    def test_esm_path_exists(self):
        assert (STATIC_DIR / "notification.js").exists()


class TestKeyboardShortcut:
    def test_init_defaults(self):
        w = _make(KeyboardShortcut)
        assert w.shortcut == ""
        assert w.pressed is False
        assert w.event == {}

    def test_esm_path_exists(self):
        assert (STATIC_DIR / "keyboard.js").exists()


class TestExistingWidgets:
    """Smoke tests for pre-existing widgets."""

    def test_url_hash_init(self):
        w = _make(URLHash)
        assert w.hash == ""

    def test_url_path_init(self):
        w = _make(URLPath)
        assert w.path == ""

    def test_url_info_init(self):
        w = _make(URLInfo)
        assert w.protocol == ""
        assert w.hostname == ""

    def test_dom_query_init(self):
        w = _make(DOMQuery)
        assert w.selector == ""
        assert w.result == []

    def test_cookie_manager_init(self):
        w = _make(CookieManager)
        assert w.cookies == {}

    def test_storage_item_init(self):
        w = _make(StorageItem)
        assert w.storage_type == "local"
        assert w.key == ""

    def test_copy_to_clipboard_init(self):
        w = _make(CopyToClipboard)
        assert w.text == ""
        assert w.success is False


class TestPrintPageButton:
    def test_init_defaults(self):
        w = _make(PrintPageButton)
        assert w is not None

    def test_esm_path_exists(self):
        assert (STATIC_DIR / "print_page_button.js").exists()


class TestScreenshotButton:
    def test_init_defaults(self):
        w = _make(ScreenshotButton)
        assert w.locator == ""
        assert w.filename == ""

    def test_esm_path_exists(self):
        assert (STATIC_DIR / "screenshot_button.js").exists()


# --- JS syntax validation ---

JS_FILES = sorted(STATIC_DIR.glob("*.js"))


@pytest.mark.parametrize("js_file", JS_FILES, ids=lambda p: p.name)
def test_js_syntax_valid(js_file):
    """Verify each JS file parses without syntax errors using Node."""
    result = subprocess.run(
        ["node", "--check", str(js_file)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"{js_file.name} has syntax errors:\n{result.stderr}"
    )
