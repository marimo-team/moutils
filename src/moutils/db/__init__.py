"""Read-only DB-API 2.0 connections over REST query APIs, for marimo SQL cells.

Assign a connection to a notebook variable and marimo detects it as a SQL engine:

    from moutils.db import PostHogConnection, DatasetteConnection

    posthog = PostHogConnection(api_key="phx_...", project_id=123)
    datasette = DatasetteConnection("https://example.com", "mydb")

PostHog uses ``requests`` (a base moutils dependency); Datasette uses ``httpx``,
available via the optional extra: ``pip install moutils[db]``.
"""

from ._core import Connection, Cursor
from .datasette import DatasetteConnection, databases
from .posthog import PostHogConnection

__all__ = [
    "PostHogConnection",
    "DatasetteConnection",
    "databases",
    "Connection",
    "Cursor",
]
