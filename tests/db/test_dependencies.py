"""Tests for optional database dependency validation."""

from types import SimpleNamespace

import pytest

from moutils.db._dependencies import require_dependency


def test_require_dependency_has_actionable_error(monkeypatch):
    def missing(_module_name):
        raise ModuleNotFoundError(name="client_module")

    monkeypatch.setattr("moutils.db._dependencies.import_module", missing)

    with pytest.raises(
        ImportError,
        match=r"ExampleConnection requires `client-package`.*pip install client-package",
    ):
        require_dependency(
            "client_module",
            connection_name="ExampleConnection",
            package_name="client-package",
        )


def test_require_dependency_does_not_cache_missing_package(monkeypatch):
    calls = []
    installed = SimpleNamespace()

    def install_between_calls(module_name):
        calls.append(module_name)
        if len(calls) == 1:
            raise ModuleNotFoundError(name=module_name)
        return installed

    monkeypatch.setattr("moutils.db._dependencies.import_module", install_between_calls)

    with pytest.raises(ImportError):
        require_dependency("client_module", connection_name="ExampleConnection")

    assert (
        require_dependency("client_module", connection_name="ExampleConnection")
        is installed
    )
    assert calls == ["client_module", "client_module"]


def test_require_dependency_preserves_transitive_import_error(monkeypatch):
    def broken_dependency(_module_name):
        raise ModuleNotFoundError(name="transitive_dependency")

    monkeypatch.setattr("moutils.db._dependencies.import_module", broken_dependency)

    with pytest.raises(ModuleNotFoundError) as exc_info:
        require_dependency("client_module", connection_name="ExampleConnection")

    assert exc_info.value.name == "transitive_dependency"
