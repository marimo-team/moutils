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


def test_from_torch_builds_runnable_model():
    torch = pytest.importorskip("torch")
    pytest.importorskip("onnxruntime")
    model = torch.nn.Linear(3, 2)
    rt = OnnxRuntime.from_torch(
        model,
        (torch.zeros(1, 3),),
        input_names=["x"],
        output_names=["y"],
        dynamo=False,
    )
    assert isinstance(rt.onnx_bytes, bytes)
    assert rt.onnx_bytes
    x = np.zeros((1, 3), dtype=np.float32)
    (y,) = asyncio.run(rt.run({"x": x}, ["y"]))
    assert y.shape == (1, 2)


def test_wasm_version_pins_and_round_trips():
    from moutils.onnx import DEFAULT_WASM_VERSION, OnnxRuntimeStub

    assert OnnxRuntime(b"m").wasm_version == DEFAULT_WASM_VERSION
    rt = OnnxRuntime(b"m", wasm_version="1.20.1")
    assert rt.wasm_version == "1.20.1"
    # The pin survives a pickle round-trip and the marimo cache stub.
    import pickle

    assert pickle.loads(pickle.dumps(rt)).wasm_version == "1.20.1"
    restored = OnnxRuntimeStub(rt).load({})
    assert restored.wasm_version == "1.20.1"
    assert restored.onnx_bytes == b"m"


def test_wasm_version_rejects_injection():
    OnnxRuntime(b"m", wasm_version="1.27.0")  # a valid version does not raise
    for bad in ["1.0'); alert(1); //", "1 2", 'a"b', "x)", "v/../../etc"]:
        with pytest.raises(ValueError):
            OnnxRuntime(b"m", wasm_version=bad)


def test_from_jax_builds_runnable_model():
    pytest.importorskip("jax")
    pytest.importorskip("jax2onnx")
    pytest.importorskip("onnxruntime")
    import jax.numpy as jnp

    def fn(x):
        return jnp.tanh(x) * 2.0

    rt = OnnxRuntime.from_jax(fn, [("B", 3)], input_names=["x"])
    assert isinstance(rt.onnx_bytes, bytes)
    assert rt.onnx_bytes
    x = np.ones((1, 3), dtype=np.float32)
    (y,) = asyncio.run(rt.run({"x": x}))
    np.testing.assert_allclose(y, np.tanh(1.0) * 2.0, rtol=1e-4)


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
