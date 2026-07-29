"""Read-only DB-API 2.0 connections over REST query APIs, for marimo SQL cells.

Import a connection from its submodule and assign it to a notebook variable;
marimo then detects it as a SQL engine and you can query it from SQL cells:

    from moutils.db.posthog import PostHogConnection
    from moutils.db.datasette import DatasetteConnection

    posthog = PostHogConnection(api_key="phx_...", project_id=123)
    datasette = DatasetteConnection("https://example.com", "mydb")

PostHog uses ``requests`` (a base moutils dependency); Datasette uses ``httpx``,
available via the optional extra: ``pip install moutils[db]``.
"""
