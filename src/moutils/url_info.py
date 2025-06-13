"""URL info widget for marimo notebooks."""

from pathlib import Path
from typing import Any, Dict

import anywidget
import traitlets


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
        try:
            import marimo
            instance.__init__(*args, **kwargs)
            as_widget = marimo.ui.anywidget(instance)
            if getattr(instance, "debug", False):
                print("[moutils:urlinfo] Created marimo widget")
            return as_widget
        except (ImportError, ModuleNotFoundError):
            return instance 