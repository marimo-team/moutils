"""Tests for the OnnxRuntime cache stub."""

import asyncio

import numpy as np
import pytest

from moutils.onnx import OnnxRuntime


def test_import_and_bytes():
    rt = OnnxRuntime(b"model-bytes")
    assert rt.onnx_bytes == b"model-bytes"
    # Session builds lazily. Construction does nothing heavy.
    assert rt._session is None


def test_stub_registered():
    from marimo._save.stubs import CUSTOM_STUBS

    assert OnnxRuntime in CUSTOM_STUBS


def test_stub_serializes_to_model_bytes():
    from moutils.onnx import OnnxRuntimeStub

    stub = OnnxRuntimeStub(OnnxRuntime(b"abc"))
    assert stub.to_bytes() == b"abc"
    restored = stub.load({})
    assert isinstance(restored, OnnxRuntime)
    assert restored.onnx_bytes == b"abc"
    assert restored._session is None


def test_pickle_roundtrip_keeps_only_bytes():
    import pickle

    rt = OnnxRuntime(b"payload")
    rt._session = object()  # a live session must never be serialized
    restored = pickle.loads(pickle.dumps(rt))
    assert restored.onnx_bytes == b"payload"
    assert restored._session is None


def _double_model_bytes() -> bytes:
    # Minimal ONNX model: y = x + x, so run() output should be 2*x.
    pytest.importorskip("onnx")
    from onnx import TensorProto, helper

    node = helper.make_node("Add", ["x", "x"], ["y"])
    graph = helper.make_graph(
        [node],
        "double",
        [helper.make_tensor_value_info("x", TensorProto.FLOAT, [None, 2])],
        [helper.make_tensor_value_info("y", TensorProto.FLOAT, [None, 2])],
    )
    model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 13)])
    return model.SerializeToString()


def test_native_run_executes_model():
    pytest.importorskip("onnxruntime")
    rt = OnnxRuntime(_double_model_bytes())
    x = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)
    (y,) = asyncio.run(rt.run({"x": x}, ["y"]))
    np.testing.assert_array_equal(y, 2 * x)
    assert rt._kind == "native"


def test_native_run_defaults_to_all_outputs():
    pytest.importorskip("onnxruntime")
    rt = OnnxRuntime(_double_model_bytes())
    x = np.array([[5.0, 6.0]], dtype=np.float32)
    outputs = asyncio.run(rt.run({"x": x}))  # output_names=None
    assert len(outputs) == 1
    np.testing.assert_array_equal(outputs[0], 2 * x)


def test_marimo_cache_conversion():
    # Exercise marimo's real save/restore path: maybe_get_custom_stub routes an
    # OnnxRuntime to its stub, which restores just the model bytes, no session.
    from marimo._save.stubs import maybe_get_custom_stub

    stub = maybe_get_custom_stub(OnnxRuntime(b"trained-model-bytes"))
    assert stub is not None
    restored = stub.load({})
    assert isinstance(restored, OnnxRuntime)
    assert restored.onnx_bytes == b"trained-model-bytes"
    assert restored._session is None
