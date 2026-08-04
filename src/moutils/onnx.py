"""A cache-friendly ONNX inference runtime for marimo notebooks.

`OnnxRuntime` holds a serialized ONNX model and runs it lazily, adapting to its
environment: native `onnxruntime` on a host, and `onnxruntime-web` (loaded from
a CDN) when the notebook runs in the browser via WASM/pyodide.

Importing this module registers a marimo cache stub, so a cached `OnnxRuntime`
round-trips as exactly its model bytes. A torch or jax model trained at export
time then restores as a working inference session inside a static WASM export.

Example:
    ```python
    from moutils.onnx import OnnxRuntime

    # From a torch model (torch.onnx.export kwargs pass through):
    runtime = OnnxRuntime.from_torch(model, (example_input,), output_names=["y"])
    # Or wrap serialized ONNX bytes directly:
    runtime = OnnxRuntime(onnx_bytes)

    logits = (await runtime.run({"x": x}))[0]  # x: a numpy input array
    ```
"""

from __future__ import annotations

import re
from typing import Any

__all__ = ["OnnxRuntime"]

# onnxruntime-web build loaded in the browser backend. Pinned for
# reproducibility; override per instance via the `wasm_version` argument.
# Tracks the current onnxruntime-web release (what the unpinned CDN URL served,
# now made explicit). Native `onnxruntime` in the lock is 1.28.0.
DEFAULT_WASM_VERSION = "1.27.0"

# `wasm_version` is interpolated into the browser's `js.eval` URL, so restrict
# it to version-string characters — no quotes, whitespace, or `);` that could
# break out of the string and inject JavaScript.
_WASM_VERSION_RE = re.compile(r"\A[0-9A-Za-z][0-9A-Za-z._+-]*\Z")


class OnnxRuntime:
    """Lazy, environment-adaptive ONNX inference session.

    Holds only the serialized model. The live session is built on the first
    `run()` call and is never serialized. Pickling or caching an instance
    round-trips just the model bytes.
    """

    def __init__(
        self, onnx_bytes: bytes, *, wasm_version: str = DEFAULT_WASM_VERSION
    ) -> None:
        if not _WASM_VERSION_RE.match(wasm_version):
            raise ValueError(
                f"invalid wasm_version {wasm_version!r}: expected a version "
                "string such as '1.27.0'."
            )
        self.onnx_bytes = onnx_bytes
        self.wasm_version = wasm_version
        self._session: Any = None
        self._ort: Any = None
        self._kind: str | None = None

    @classmethod
    def from_torch(
        cls,
        model: Any,
        args: Any,
        *,
        wasm_version: str = DEFAULT_WASM_VERSION,
        **export_kwargs: Any,
    ) -> OnnxRuntime:
        """Export a torch model to ONNX and wrap the bytes.

        `args` and `export_kwargs` pass through to `torch.onnx.export`.
        """
        import io

        import torch

        buf = io.BytesIO()
        torch.onnx.export(model, args, buf, **export_kwargs)
        return cls(buf.getvalue(), wasm_version=wasm_version)

    @classmethod
    def from_jax(
        cls,
        fn: Any,
        inputs: Any,
        *,
        wasm_version: str = DEFAULT_WASM_VERSION,
        **to_onnx_kwargs: Any,
    ) -> OnnxRuntime:
        """Convert a JAX function to ONNX and wrap the bytes.

        Uses [`jax2onnx`](https://pypi.org/project/jax2onnx/). `inputs` (a
        sequence of shapes) and `to_onnx_kwargs` pass through to
        `jax2onnx.to_onnx`.
        """
        from jax2onnx import to_onnx

        model = to_onnx(fn, inputs, **to_onnx_kwargs)
        return cls(model.SerializeToString(), wasm_version=wasm_version)

    def __getstate__(self) -> dict[str, Any]:
        return {
            "onnx_bytes": self.onnx_bytes,
            "wasm_version": self.wasm_version,
        }

    def __setstate__(self, state: dict[str, Any]) -> None:
        self.onnx_bytes = state["onnx_bytes"]
        self.wasm_version = state.get("wasm_version", DEFAULT_WASM_VERSION)
        self._session = None
        self._ort = None
        self._kind = None

    @staticmethod
    def _in_browser() -> bool:
        from importlib.util import find_spec

        return find_spec("js") is not None and find_spec("pyodide") is not None

    async def _ensure(self) -> None:
        if self._session is not None:
            return
        if self._in_browser():
            import js  # type: ignore[import-not-found]
            from pyodide.ffi import to_js  # type: ignore[import-not-found]

            base = f"https://cdn.jsdelivr.net/npm/onnxruntime-web@{self.wasm_version}"
            ort = await js.eval(f"import('{base}/dist/ort.all.bundle.min.mjs')")
            ort.env.wasm.wasmPaths = f"{base}/dist/"
            opts = js.Object.new()
            opts.executionProviders = to_js(["wasm"])
            self._ort = ort
            self._session = await ort.InferenceSession.create(
                to_js(self.onnx_bytes), opts
            )
            self._kind = "web"
        else:
            try:
                import onnxruntime as ort
            except ImportError as e:
                raise RuntimeError(
                    "OnnxRuntime.run() outside the browser requires the "
                    "`onnxruntime` package (`pip install onnxruntime`)."
                ) from e

            self._session = ort.InferenceSession(self.onnx_bytes)
            self._kind = "native"

    async def run(
        self,
        inputs: dict[str, Any],
        output_names: list[str] | None = None,
    ) -> list[Any]:
        """Run inference and return the outputs in `output_names` order.

        Args:
            inputs: Mapping of input name to a numpy array.
            output_names: Names of the outputs to return, in order. When `None`,
                returns all outputs in the session's declared order.
        """
        import numpy as np

        await self._ensure()
        if self._kind == "native":
            return self._session.run(output_names, inputs)

        from pyodide.ffi import to_js  # type: ignore[import-not-found]

        feeds = {}
        for name, arr in inputs.items():
            # Preserve the caller's dtype — int64 token ids, bool masks, etc.
            arr = np.ascontiguousarray(arr)
            feeds[name] = self._ort.Tensor.new(
                str(arr.dtype), to_js(arr.ravel()), to_js(list(arr.shape))
            )
        # Pass the requested names as `fetches` so the runtime computes only
        # those outputs, matching the native path. Default to the session's
        # declared outputs when none are requested.
        names = list(output_names) if output_names else list(self._session.outputNames)
        results = await self._session.run(to_js(feeds), to_js(names))
        out = []
        for name in names:
            tensor = getattr(results, name)
            # to_py() yields the tensor's native dtype; do not coerce it.
            out.append(
                np.asarray(tensor.data.to_py()).reshape(list(tensor.dims.to_py()))
            )
        return out


# Register a marimo cache stub: caching an `OnnxRuntime` then stores exactly its
# ONNX bytes and restores a working session. Guarded so `moutils.onnx` imports
# without marimo — the stub is only used inside a marimo cache.
try:
    from marimo._save.stubs import CustomStub, register_stub
except ImportError:  # pragma: no cover - marimo not installed
    pass
else:

    class OnnxRuntimeStub(CustomStub):
        """Store an `OnnxRuntime`'s model bytes and pinned wasm version."""

        __slots__ = ("onnx_bytes", "wasm_version")

        def __init__(self, runtime: Any) -> None:
            self.onnx_bytes = runtime.onnx_bytes
            self.wasm_version = runtime.wasm_version

        def load(self, glbls: dict[str, Any]) -> Any:
            del glbls
            return OnnxRuntime(self.onnx_bytes, wasm_version=self.wasm_version)

        @staticmethod
        def get_type() -> type:
            return OnnxRuntime

        def to_bytes(self) -> bytes:
            return self.onnx_bytes

    register_stub(OnnxRuntime, OnnxRuntimeStub)
