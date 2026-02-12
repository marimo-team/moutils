"""moutils - A collection of browser utilities for marimo notebooks.

This module provides various widgets for interacting with browser features like URL, storage,
cookies, and DOM elements in marimo notebooks.
"""

import asyncio
import importlib.metadata
import os
import signal
import sys
from pathlib import Path
from typing import Any, Callable, Dict, Optional

import anywidget
import traitlets

try:
    __version__ = importlib.metadata.version("moutils")
except importlib.metadata.PackageNotFoundError:
    __version__ = "unknown"

# Define the public API
__all__ = [
    "URLHash",
    "URLPath",
    "URLInfo",
    "DOMQuery",
    "CookieManager",
    "StorageItem",
    "Slot",
    "CopyToClipboard",
    "ShellWidget",
    "shell",
    "ColorScheme",
    "ViewportSize",
    "OnlineStatus",
    "PageVisibility",
    "Geolocation",
    "CameraCapture",
    "Notification",
    "KeyboardShortcut",
    "PrintPageButton",
    "print_page",
    "ScreenshotButton",
    "screenshot",
]


def headless(instance: Any, *args: Any, **kwargs: Any) -> Any:
    """Wrap a widget instance to work in both headless and UI modes.

    Args:
        instance: The widget instance to wrap
        *args: Arguments to pass to the widget's __init__
        **kwargs: Keyword arguments to pass to the widget's __init__

    Returns:
        The wrapped widget instance
    """
    try:
        import marimo

        instance.__init__(*args, **kwargs)
        as_widget = marimo.ui.anywidget(instance)
        marimo.output.append(as_widget)
        return as_widget
    except ImportError:
        return instance


def _wrap_marimo(instance: Any, *args: Any, **kwargs: Any) -> Any:
    try:
        import marimo

        instance.__init__(*args, **kwargs)
        return marimo.ui.anywidget(instance)
    except (ImportError, ModuleNotFoundError):
        return instance


class URLHash(anywidget.AnyWidget):
    """Widget for interacting with URL hash."""

    _esm = Path(__file__).parent / "static" / "hash.js"
    hash = traitlets.Unicode("").tag(sync=True)

    @traitlets.validate("hash")
    def _validate_hash(self, proposal: Dict[str, str]) -> str:
        """Validate hash value - must start with #."""
        value = proposal["value"]
        if value and not value.startswith("#"):
            value = f"#{value}"
        return value

    def __new__(cls, *args: Any, **kwargs: Any) -> Any:
        instance = super().__new__(cls)
        return headless(instance, *args, **kwargs)


class URLPath(anywidget.AnyWidget):
    """Widget for interacting with URL path."""

    _esm = Path(__file__).parent / "static" / "path.js"
    path = traitlets.Unicode("").tag(sync=True)

    @traitlets.validate("path")
    def _validate_path(self, proposal: Dict[str, str]) -> str:
        """Validate path value - must start with /."""
        value = proposal["value"]
        if value and not value.startswith("/"):
            value = f"/{value}"
        return value

    def __new__(cls, *args: Any, **kwargs: Any) -> Any:
        instance = super().__new__(cls)
        return headless(instance, *args, **kwargs)


class URLInfo(anywidget.AnyWidget):
    """Widget for interacting with all URL components."""

    _esm = Path(__file__).parent / "static" / "urlinfo.js"
    protocol = traitlets.Unicode("").tag(sync=True)
    hostname = traitlets.Unicode("").tag(sync=True)
    port = traitlets.Unicode("").tag(sync=True)
    pathname = traitlets.Unicode("").tag(sync=True)
    search = traitlets.Unicode("").tag(sync=True)
    hash = traitlets.Unicode("").tag(sync=True)
    username = traitlets.Unicode("").tag(sync=True)
    password = traitlets.Unicode("").tag(sync=True)
    href = traitlets.Unicode("").tag(sync=True)

    @traitlets.validate("protocol")
    def _validate_protocol(self, proposal: Dict[str, str]) -> str:
        """Validate protocol value - should end with :"""
        value = proposal["value"]
        if value and not value.endswith(":"):
            value = f"{value}:"
        return value

    @traitlets.validate("pathname")
    def _validate_pathname(self, proposal: Dict[str, str]) -> str:
        """Validate pathname value - must start with /."""
        value = proposal["value"]
        if value and not value.startswith("/"):
            value = f"/{value}"
        return value

    @traitlets.validate("search")
    def _validate_search(self, proposal: Dict[str, str]) -> str:
        """Validate search value - should start with ? if not empty."""
        value = proposal["value"]
        if value and not value.startswith("?"):
            value = f"?{value}"
        return value

    @traitlets.validate("hash")
    def _validate_hash(self, proposal: Dict[str, str]) -> str:
        """Validate hash value - should start with # if not empty."""
        value = proposal["value"]
        if value and not value.startswith("#"):
            value = f"#{value}"
        return value

    def __new__(cls, *args: Any, **kwargs: Any) -> Any:
        instance = super().__new__(cls)
        return headless(instance, *args, **kwargs)


class DOMQuery(anywidget.AnyWidget):
    """Widget for querying DOM elements."""

    _esm = Path(__file__).parent / "static" / "query.js"
    selector = traitlets.Unicode("").tag(sync=True)
    result = traitlets.List([]).tag(sync=True)

    def __new__(cls, *args: Any, **kwargs: Any) -> Any:
        instance = super().__new__(cls)
        return headless(instance, *args, **kwargs)


class CookieManager(anywidget.AnyWidget):
    """Widget for managing browser cookies."""

    _esm = Path(__file__).parent / "static" / "cookies.js"
    cookies = traitlets.Dict({}).tag(sync=True)

    def __new__(cls, *args: Any, **kwargs: Any) -> Any:
        instance = super().__new__(cls)
        return headless(instance, *args, **kwargs)


class StorageItem(anywidget.AnyWidget):
    """Widget for interacting with browser storage (local/session)."""

    _esm = Path(__file__).parent / "static" / "storage.js"
    storage_type = traitlets.Enum(["local", "session"], default_value="local").tag(
        sync=True
    )
    key = traitlets.Unicode("").tag(sync=True)
    data = traitlets.Any().tag(sync=True)

    def __new__(cls, *args: Any, **kwargs: Any) -> Any:
        instance = super().__new__(cls)
        return headless(instance, *args, **kwargs)


class Slot(anywidget.AnyWidget):
    """Widget for creating a slot that can contain HTML and handle DOM events."""

    _esm = Path(__file__).parent / "static" / "slot.js"
    children = traitlets.Unicode("").tag(sync=True)
    events = traitlets.List([]).tag(sync=True)
    last_event = traitlets.Dict({}).tag(sync=True)

    def __init__(
        self,
        children: str = "",
        # Mouse events
        on_contextmenu: Optional[Callable[[dict[str, Any]], None]] = None,
        on_dblclick: Optional[Callable[[dict[str, Any]], None]] = None,
        on_mouseenter: Optional[Callable[[dict[str, Any]], None]] = None,
        on_mouseleave: Optional[Callable[[dict[str, Any]], None]] = None,
        on_mousemove: Optional[Callable[[dict[str, Any]], None]] = None,
        on_mouseout: Optional[Callable[[dict[str, Any]], None]] = None,
        on_mouseover: Optional[Callable[[dict[str, Any]], None]] = None,
        on_mouseup: Optional[Callable[[dict[str, Any]], None]] = None,
        # Keyboard events
        on_keydown: Optional[Callable[[dict[str, Any]], None]] = None,
        on_keypress: Optional[Callable[[dict[str, Any]], None]] = None,
        on_keyup: Optional[Callable[[dict[str, Any]], None]] = None,
        # Form events
        on_change: Optional[Callable[[dict[str, Any]], None]] = None,
        on_input: Optional[Callable[[dict[str, Any]], None]] = None,
        on_submit: Optional[Callable[[dict[str, Any]], None]] = None,
        on_reset: Optional[Callable[[dict[str, Any]], None]] = None,
        on_focusin: Optional[Callable[[dict[str, Any]], None]] = None,
        on_focusout: Optional[Callable[[dict[str, Any]], None]] = None,
        # Drag events
        on_drag: Optional[Callable[[dict[str, Any]], None]] = None,
        on_dragend: Optional[Callable[[dict[str, Any]], None]] = None,
        on_dragenter: Optional[Callable[[dict[str, Any]], None]] = None,
        on_dragleave: Optional[Callable[[dict[str, Any]], None]] = None,
        on_dragover: Optional[Callable[[dict[str, Any]], None]] = None,
        on_dragstart: Optional[Callable[[dict[str, Any]], None]] = None,
        on_drop: Optional[Callable[[dict[str, Any]], None]] = None,
        # Touch events
        on_touchstart: Optional[Callable[[dict[str, Any]], None]] = None,
        on_touchmove: Optional[Callable[[dict[str, Any]], None]] = None,
        on_touchend: Optional[Callable[[dict[str, Any]], None]] = None,
        on_touchcancel: Optional[Callable[[dict[str, Any]], None]] = None,
        # Pointer events
        on_pointerdown: Optional[Callable[[dict[str, Any]], None]] = None,
        on_pointermove: Optional[Callable[[dict[str, Any]], None]] = None,
        on_pointerup: Optional[Callable[[dict[str, Any]], None]] = None,
        on_pointercancel: Optional[Callable[[dict[str, Any]], None]] = None,
        on_pointerover: Optional[Callable[[dict[str, Any]], None]] = None,
        on_pointerout: Optional[Callable[[dict[str, Any]], None]] = None,
        on_pointerenter: Optional[Callable[[dict[str, Any]], None]] = None,
        on_pointerleave: Optional[Callable[[dict[str, Any]], None]] = None,
        # Scroll events
        on_scroll: Optional[Callable[[dict[str, Any]], None]] = None,
        on_scrollend: Optional[Callable[[dict[str, Any]], None]] = None,
        # Clipboard events
        on_copy: Optional[Callable[[dict[str, Any]], None]] = None,
        on_cut: Optional[Callable[[dict[str, Any]], None]] = None,
        on_paste: Optional[Callable[[dict[str, Any]], None]] = None,
        # Animation and transition
        on_animationstart: Optional[Callable[[dict[str, Any]], None]] = None,
        on_animationend: Optional[Callable[[dict[str, Any]], None]] = None,
        on_animationiteration: Optional[Callable[[dict[str, Any]], None]] = None,
        on_transitionend: Optional[Callable[[dict[str, Any]], None]] = None,
    ):
        """Initialize the Slot widget.

        Args:
            children: HTML content to render in the slot
            on_*: Event handlers for various DOM events
        """
        self.children = children

        # Define all event handlers
        event_handlers = {
            # Mouse events
            "contextmenu": on_contextmenu,
            "dblclick": on_dblclick,
            "mouseenter": on_mouseenter,
            "mouseleave": on_mouseleave,
            "mousemove": on_mousemove,
            "mouseout": on_mouseout,
            "mouseover": on_mouseover,
            "mouseup": on_mouseup,
            # Keyboard events
            "keydown": on_keydown,
            "keypress": on_keypress,
            "keyup": on_keyup,
            # Form events
            "change": on_change,
            "input": on_input,
            "submit": on_submit,
            "reset": on_reset,
            "focusin": on_focusin,
            "focusout": on_focusout,
            # Drag events
            "drag": on_drag,
            "dragend": on_dragend,
            "dragenter": on_dragenter,
            "dragleave": on_dragleave,
            "dragover": on_dragover,
            "dragstart": on_dragstart,
            "drop": on_drop,
            # Touch events
            "touchstart": on_touchstart,
            "touchmove": on_touchmove,
            "touchend": on_touchend,
            "touchcancel": on_touchcancel,
            # Pointer events
            "pointerdown": on_pointerdown,
            "pointermove": on_pointermove,
            "pointerup": on_pointerup,
            "pointercancel": on_pointercancel,
            "pointerover": on_pointerover,
            "pointerout": on_pointerout,
            "pointerenter": on_pointerenter,
            "pointerleave": on_pointerleave,
            # Scroll events
            "scroll": on_scroll,
            "scrollend": on_scrollend,
            # Clipboard events
            "copy": on_copy,
            "cut": on_cut,
            "paste": on_paste,
            # Animation and transition
            "animationstart": on_animationstart,
            "animationend": on_animationend,
            "animationiteration": on_animationiteration,
            "transitionend": on_transitionend,
        }

        def handle_event(change: Dict[str, Any]) -> None:
            """Handle DOM events by calling the appropriate callback."""
            payload = change["new"]
            event_name = payload["name"]
            event_payload = payload["payload"]

            if event_name in event_handlers and event_handlers[event_name] is not None:
                cb = event_handlers[event_name]
                if cb is None:
                    return

                try:
                    import inspect

                    sig = inspect.signature(cb)
                    if len(sig.parameters) > 0:
                        cb(event_payload)
                    else:
                        cb()
                except (ValueError, TypeError) as e:
                    import sys

                    sys.stderr.write(
                        f"Error calling event handler for {event_name}: {e}\n"
                    )
            else:
                import sys

                sys.stderr.write(f"Unknown event: {event_name}\n")

        events = [
            event_name
            for event_name, handler in event_handlers.items()
            if handler is not None
        ]
        self.events = events
        self.observe(handle_event, names=["last_event"])

        super().__init__(children=children, events=events)

    def __new__(cls, *args: Any, **kwargs: Any) -> Any:
        instance = super().__new__(cls)
        return headless(instance, *args, **kwargs)


class ShellWidget(anywidget.AnyWidget):
    """Interactive shell command widget for Jupyter notebooks."""

    _esm = Path(__file__).parent / "static" / "shell.js"
    _css = Path(__file__).parent / "static" / "shell.css"
    command = traitlets.Unicode("").tag(sync=True)
    working_directory = traitlets.Unicode(".").tag(sync=True)
    theme = traitlets.Unicode("dark").tag(sync=True)

    def __init__(self, command: str, working_directory: str = ".", run: bool = False, theme: str = "dark"):
        super().__init__()
        self.command = command
        self.working_directory = working_directory
        self.theme = theme
        self.on_msg(self._handle_custom_msg)
        self._process = None
        self._pgid = None
        self._master_fd = None
        self._slave_fd = None
        self._reader_task = None
        self._reader_installed = False

        # Auto-run if parameter is True
        if run:
            self.run()

    def _handle_custom_msg(self, data: dict, buffers: list):
        """Handle a custom message from the frontend.

        Messages arrive as plain dicts — model.send({ type: "execute" })
        on the JS side lands here with data = {"type": "execute"}.
        """
        msg_type = data.get("type", "")

        if msg_type == "execute":
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self._execute_command_async())
                else:
                    loop.run_until_complete(self._execute_command_async())
            except RuntimeError:
                asyncio.run(self._execute_command_async())

        elif msg_type == "terminate":
            self.terminate()

        elif msg_type == "kill":
            self.kill()

        elif msg_type == "input":
            text = data.get("data", "")
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self._send_input(text))
                else:
                    loop.run_until_complete(self._send_input(text))
            except RuntimeError:
                asyncio.run(self._send_input(text))

    async def _execute_command_async(self):
        """Execute the shell command asynchronously using a PTY to support interactive input."""
        try:
            if sys.platform == "win32":
                raise RuntimeError("PTY-based shell not supported on Windows")

            shell = "/bin/bash"
            shell_args = ["-c", self.command]

            self._master_fd, self._slave_fd = os.openpty()
            loop = asyncio.get_event_loop()

            # Spawn the child process
            self._process = await asyncio.create_subprocess_exec(
                shell,
                *shell_args,
                cwd=self.working_directory,
                stdin=self._slave_fd,
                stdout=self._slave_fd,
                stderr=self._slave_fd,
                start_new_session=True,
            )

            # POSIX: start_new_session=True → child's PGID == child's PID.
            pid = self._process.pid
            self._pgid = pid
            self.send({"type": "started", "pid": pid, "pgid": self._pgid})
            self.send({"type": "output", "data": f"$ {self.command}\n"})

            # Register reader AFTER spawning the child (simple, unified behavior)
            def _remove_reader_safely():
                if self._reader_installed:
                    try:
                        loop.remove_reader(self._master_fd)
                    except Exception:
                        pass
                    self._reader_installed = False

            def _on_master_readable():
                """Pump PTY output; suppress benign OSErrors when process exits."""
                try:
                    data = os.read(self._master_fd, 1024)
                    if not data:
                        _remove_reader_safely()
                        return
                    self.send(
                        {
                            "type": "output",
                            "data": data.decode("utf-8", errors="replace"),
                        }
                    )
                except OSError:
                    # Treat read errors after process exit as EOF without surfacing an error.
                    _remove_reader_safely()
                except Exception as e:
                    self.send({"type": "error", "error": str(e)})
                    _remove_reader_safely()

            try:
                loop.add_reader(self._master_fd, _on_master_readable)
                self._reader_installed = True
            except NotImplementedError:

                async def _fallback_reader():
                    try:
                        while True:
                            data = await loop.run_in_executor(
                                None, os.read, self._master_fd, 1024
                            )
                            if not data:
                                break
                            self.send(
                                {
                                    "type": "output",
                                    "data": data.decode("utf-8", errors="replace"),
                                }
                            )
                    except Exception:
                        # Suppress benign errors when process has already exited
                        pass

                self._reader_task = asyncio.create_task(_fallback_reader())

            return_code = await self._process.wait()
            # Optionally wait for fallback reader if it was used
            if self._reader_task:
                try:
                    await self._reader_task
                except Exception:
                    pass
            self.send({"type": "completed", "returncode": return_code})

        except Exception as e:
            self.send({"type": "error", "error": str(e)})
        finally:
            # Remove reader (if still installed) and close fds
            try:
                if self._reader_installed and self._master_fd is not None:
                    loop = asyncio.get_event_loop()
                    loop.remove_reader(self._master_fd)
            except Exception:
                pass
            self._reader_installed = False
            if self._master_fd:
                try:
                    os.close(self._master_fd)
                except Exception:
                    pass
            if self._slave_fd:
                try:
                    os.close(self._slave_fd)
                except Exception:
                    pass
            self._process = None
            self._pgid = None
            self._master_fd = None
            self._slave_fd = None
            self._reader_task = None

    async def _send_input(self, text: str):
        if self._process and self._master_fd:
            os.write(self._master_fd, text.encode() + b"\n")
            self.send({"type": "input_sent", "data": text})

    def run(self):
        """Public method to start execution without frontend button."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self._execute_command_async())
            else:
                loop.run_until_complete(self._execute_command_async())

        except RuntimeError:
            asyncio.run(self._execute_command_async())

        except Exception as e:
            self.send({"type": "error", "error": str(e)})

    def terminate(self):
        """Send SIGTERM to the process group (all children)."""
        if not self._process or self._process.returncode is not None:
            self.send({"type": "not_running"})
            return
        try:
            if self._pgid:
                os.killpg(self._pgid, signal.SIGTERM)
            else:
                self._process.terminate()
            self.send({"type": "terminated"})
        except Exception as e:
            self.send({"type": "error", "error": f"Terminate failed: {e}"})

    def kill(self):
        """Send SIGKILL to the process group (all children)."""
        if not self._process or self._process.returncode is not None:
            self.send({"type": "not_running"})
            return
        try:
            if self._pgid:
                os.killpg(self._pgid, signal.SIGKILL)
            else:
                self._process.kill()
            self.send({"type": "killed"})
        except Exception as e:
            self.send({"type": "error", "error": f"Kill failed: {e}"})

    def __new__(cls, *args: Any, **kwargs: Any) -> Any:
        instance = super().__new__(cls)
        return _wrap_marimo(instance, *args, **kwargs)


def shell(command: str, working_directory: str = ".", run: bool = False, theme: str = "dark") -> ShellWidget:
    """
    Create a shell command widget.

    Args:
        command: The shell command to execute
        working_directory: Directory to run the command in (defaults to current directory)
        theme: Color theme — "dark" (default) or "light"

    Returns:
        ShellWidget: An interactive widget with a button to run the command

    Examples:
        shell("ls -la")
        shell("python --version")
        shell("find . -name '*.py' | head -10")
        shell("npm install", working_directory="./frontend")
    """
    return ShellWidget(command, working_directory, run=run, theme=theme)


class CopyToClipboard(anywidget.AnyWidget):
    """Widget for copying text to clipboard."""

    _esm = Path(__file__).parent / "static" / "copy.js"
    text = traitlets.Unicode("").tag(sync=True)
    success = traitlets.Bool(False).tag(sync=True)
    button_text = traitlets.Unicode("").tag(sync=True)
    success_text = traitlets.Unicode("").tag(sync=True)

    def __new__(cls, *args: Any, **kwargs: Any) -> Any:
        instance = super().__new__(cls)
        return _wrap_marimo(instance, *args, **kwargs)


class ColorScheme(anywidget.AnyWidget):
    """Widget for detecting the user's preferred color scheme (light/dark mode)."""

    _esm = Path(__file__).parent / "static" / "colorscheme.js"
    scheme = traitlets.Unicode("light").tag(sync=True)
    prefers_dark = traitlets.Bool(False).tag(sync=True)

    def __new__(cls, *args: Any, **kwargs: Any) -> Any:
        instance = super().__new__(cls)
        return headless(instance, *args, **kwargs)


class ViewportSize(anywidget.AnyWidget):
    """Widget for detecting window/viewport dimensions."""

    _esm = Path(__file__).parent / "static" / "viewport.js"
    width = traitlets.Int(0).tag(sync=True)
    height = traitlets.Int(0).tag(sync=True)

    def __new__(cls, *args: Any, **kwargs: Any) -> Any:
        instance = super().__new__(cls)
        return headless(instance, *args, **kwargs)


class OnlineStatus(anywidget.AnyWidget):
    """Widget for detecting network connectivity status."""

    _esm = Path(__file__).parent / "static" / "online.js"
    online = traitlets.Bool(True).tag(sync=True)

    def __new__(cls, *args: Any, **kwargs: Any) -> Any:
        instance = super().__new__(cls)
        return headless(instance, *args, **kwargs)


class PageVisibility(anywidget.AnyWidget):
    """Widget for detecting if the browser tab is active."""

    _esm = Path(__file__).parent / "static" / "visibility.js"
    visible = traitlets.Bool(True).tag(sync=True)
    state = traitlets.Unicode("visible").tag(sync=True)

    def __new__(cls, *args: Any, **kwargs: Any) -> Any:
        instance = super().__new__(cls)
        return headless(instance, *args, **kwargs)


class Geolocation(anywidget.AnyWidget):
    """Widget for getting the user's geographic coordinates."""

    _esm = Path(__file__).parent / "static" / "geolocation.js"
    latitude = traitlets.Float(0.0).tag(sync=True)
    longitude = traitlets.Float(0.0).tag(sync=True)
    accuracy = traitlets.Float(0.0).tag(sync=True)
    error = traitlets.Unicode("").tag(sync=True)
    enabled = traitlets.Bool(False).tag(sync=True)

    def __new__(cls, *args: Any, **kwargs: Any) -> Any:
        instance = super().__new__(cls)
        return headless(instance, *args, **kwargs)


class CameraCapture(anywidget.AnyWidget):
    """Widget for capturing a still image from the webcam."""

    _esm = Path(__file__).parent / "static" / "camera.js"
    _css = Path(__file__).parent / "static" / "camera.css"
    image_data = traitlets.Unicode("").tag(sync=True)
    width = traitlets.Int(640).tag(sync=True)
    height = traitlets.Int(480).tag(sync=True)
    enabled = traitlets.Bool(False).tag(sync=True)

    def __new__(cls, *args: Any, **kwargs: Any) -> Any:
        instance = super().__new__(cls)
        return headless(instance, *args, **kwargs)


class Notification(anywidget.AnyWidget):
    """Widget for sending browser notifications."""

    _esm = Path(__file__).parent / "static" / "notification.js"
    title = traitlets.Unicode("").tag(sync=True)
    body = traitlets.Unicode("").tag(sync=True)
    icon = traitlets.Unicode("").tag(sync=True)
    permission = traitlets.Unicode("default").tag(sync=True)
    send = traitlets.Bool(False).tag(sync=True)

    def __new__(cls, *args: Any, **kwargs: Any) -> Any:
        instance = super().__new__(cls)
        return headless(instance, *args, **kwargs)


class KeyboardShortcut(anywidget.AnyWidget):
    """Widget for listening to global keyboard shortcuts."""

    _esm = Path(__file__).parent / "static" / "keyboard.js"
    shortcut = traitlets.Unicode("").tag(sync=True)
    pressed = traitlets.Bool(False).tag(sync=True)
    event = traitlets.Dict({}).tag(sync=True)

    def __new__(cls, *args: Any, **kwargs: Any) -> Any:
        instance = super().__new__(cls)
        return headless(instance, *args, **kwargs)


class PrintPageButton(anywidget.AnyWidget):
    """Button widget that opens the browser print dialog."""

    _esm = Path(__file__).parent / "static" / "print_page_button.js"

    def __new__(cls, *args: Any, **kwargs: Any) -> Any:
        instance = super().__new__(cls)
        return _wrap_marimo(instance, *args, **kwargs)


class _PrintPage(anywidget.AnyWidget):
    _esm = Path(__file__).parent / "static" / "print_page.js"
    trigger = traitlets.Bool(True).tag(sync=True)

    def __new__(cls, *args: Any, **kwargs: Any) -> Any:
        instance = super().__new__(cls)
        return headless(instance, *args, **kwargs)


def print_page():
    """Programmatically trigger the browser print dialog."""
    return _PrintPage()


class ScreenshotButton(anywidget.AnyWidget):
    """Button widget that captures a screenshot of a DOM element."""

    _esm = Path(__file__).parent / "static" / "screenshot_button.js"
    locator = traitlets.Unicode("").tag(sync=True)
    filename = traitlets.Unicode("").tag(sync=True)

    def __new__(cls, *args: Any, **kwargs: Any) -> Any:
        instance = super().__new__(cls)
        return _wrap_marimo(instance, *args, **kwargs)


class _Screenshot(anywidget.AnyWidget):
    _esm = Path(__file__).parent / "static" / "screenshot.js"
    locator = traitlets.Unicode("").tag(sync=True)
    filename = traitlets.Unicode("").tag(sync=True)
    trigger = traitlets.Bool(True).tag(sync=True)

    def __new__(cls, *args: Any, **kwargs: Any) -> Any:
        instance = super().__new__(cls)
        return headless(instance, *args, **kwargs)


def screenshot(locator="", filename=None):
    """Programmatically screenshot a DOM element and download as PNG."""
    return _Screenshot(locator=locator, filename=filename or "")
