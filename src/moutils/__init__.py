"""moutils - A collection of browser utilities for marimo notebooks.

This module provides various widgets for interacting with browser features like URL, storage,
cookies, and DOM elements in marimo notebooks.
"""

import importlib.metadata
from pathlib import Path
from typing import Any, Callable, Dict, Optional
import asyncio
import sys

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
    command = traitlets.Unicode("").tag(sync=True)
    working_directory = traitlets.Unicode(".").tag(sync=True)

    def __init__(self, command: str, working_directory: str = "."):
        super().__init__()
        self.command = command
        self.working_directory = working_directory
        self.on_msg(self._handle_msg)

    def _handle_msg(self, widget, content, buffers):
        if content == "execute_command":
            # Handle async execution properly in Jupyter
            if hasattr(asyncio, "current_task") and asyncio.current_task():
                # We're already in an async context
                asyncio.create_task(self._execute_command_async())
            else:
                # Create new event loop if needed
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.create_task(self._execute_command_async())
                    else:
                        loop.run_until_complete(self._execute_command_async())
                except RuntimeError:
                    # Fallback for environments without event loop
                    asyncio.run(self._execute_command_async())

    async def _execute_command_async(self):
        """Execute the shell command asynchronously and stream output."""
        try:
            # Determine shell based on platform
            shell = "/bin/bash" if sys.platform != "win32" else "cmd"
            shell_args = ["-c"] if sys.platform != "win32" else ["/c"]

            # Create async subprocess
            process = await asyncio.create_subprocess_exec(
                shell,
                *shell_args,
                self.command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=self.working_directory,
            )

            # Stream output
            while True:
                chunk = await process.stdout.read(1024)
                if not chunk:
                    break

                try:
                    decoded_chunk = chunk.decode("utf-8", errors="replace")
                except UnicodeDecodeError:
                    decoded_chunk = chunk.decode("latin-1", errors="replace")

                self.send({"type": "output", "data": decoded_chunk})

            # Wait for completion
            return_code = await process.wait()
            self.send({"type": "completed", "returncode": return_code})

        except Exception as e:
            self.send({"type": "error", "error": str(e)})

    def __new__(cls, *args: Any, **kwargs: Any) -> Any:
        instance = super().__new__(cls)
        return _wrap_marimo(instance, *args, **kwargs)


def shell(command: str, working_directory: str = ".") -> ShellWidget:
    """
    Create a shell command widget.

    Args:
        command: The shell command to execute
        working_directory: Directory to run the command in (defaults to current directory)

    Returns:
        ShellWidget: An interactive widget with a button to run the command

    Examples:
        shell("ls -la")
        shell("python --version")
        shell("find . -name '*.py' | head -10")
        shell("npm install", working_directory="./frontend")
    """
    return ShellWidget(command, working_directory)


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
