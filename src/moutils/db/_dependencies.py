"""Helpers for optional database client dependencies."""

from importlib import import_module
from types import ModuleType


def require_dependency(
    module_name: str,
    *,
    connection_name: str,
    package_name: str | None = None,
) -> ModuleType:
    """Import an optional dependency or raise an actionable error.

    Imports are attempted on every call. In particular, this function does not
    cache failures so a package installed during a notebook session is available
    when the connection is constructed again.
    """
    try:
        return import_module(module_name)
    except ModuleNotFoundError as exc:
        if exc.name != module_name.split(".", 1)[0]:
            raise
        install_name = package_name or module_name
        raise ImportError(
            f"{connection_name} requires `{install_name}`. "
            f"Install it with `pip install {install_name}`."
        ) from exc
