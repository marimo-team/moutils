# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo",
#     "numpy",
#     "matplotlib",
#     "moutils",
#     "mnist1d; sys_platform != 'emscripten'",
#     "pymde; sys_platform != 'emscripten'",
#     "torch; sys_platform != 'emscripten'",
#     "onnx; sys_platform != 'emscripten'",
#     "onnxruntime; sys_platform != 'emscripten'",
# ]
#
# [tool.uv.sources.torch]
# index = "pytorch-cpu"
#
# [[tool.uv.index]]
# name = "pytorch-cpu"
# url = "https://download.pytorch.org/whl/cpu"
# explicit = true
#
# [tool.marimo.runtime]
# cache_cells = true
#
# [tool.marimo.export]
# lock_kind = "observed"
# ///
"""Cache a live ONNX runtime object and restore it without the training framework.

A `_train()` helper trains an MLP on MNIST-1D and computes a PyMDE embedding.
Cell caching bundles its torch-free results into the export, and moutils' cache
stub stores the `OnnxRuntime` as exactly its ONNX bytes. On a cache hit (the
exported page) marimo skips `_train()` — torch / pymde / mnist1d never import —
yet `runtime` restores as a working inference session. Lasso a region in the
embedding and inference runs through it: native `onnxruntime` on a host,
`onnxruntime-web` in the browser via WASM.
"""

import marimo

__generated_with = "0.23.10"
app = marimo.App(width="medium")

with app.setup(hide_code=True):
    import time

    import marimo as mo
    import matplotlib.pyplot as plt
    import numpy as np

    from moutils.onnx import OnnxRuntime


@app.cell(hide_code=True)
def intro():
    mo.md(r"""
    # A live ONNX runtime, restored straight from the cache

    An MLP trained on MNIST-1D and a PyMDE embedding of the held-out set. The
    training runs in a cached `_train()` helper that returns a
    `moutils.onnx.OnnxRuntime`. Moutils' cache stub serializes that runtime as
    exactly its ONNX bytes. On a cache hit, torch / pymde / mnist1d never import,
    yet `runtime` restores as a working session.

    Lasso a region below, then toggle through the selected samples: each runs
    through the restored runtime — `onnxruntime-web` in the browser — and the
    confusion matrix summarizes the region from cached predictions.
    """)
    return


@app.cell(hide_code=True)
def train():
    def _train():
        # torch / pymde / mnist1d import here, so they stay local to this
        # function and never become cached cell defs. Only the torch-free
        # results returned below are cached, and cell caching bundles them
        # into the export.
        import io

        import pymde
        import torch
        from mnist1d.data import get_dataset_args, make_dataset

        args = get_dataset_args()
        args.num_samples = 10000  # 80/20 -> 8000 train / 2000 test
        data = make_dataset(args)
        x_train = torch.tensor(data["x"], dtype=torch.float32)
        y_train = torch.tensor(data["y"])
        x_test_np = data["x_test"].astype("float32")
        y_test = data["y_test"].astype(int)

        model = torch.nn.Sequential(
            torch.nn.Linear(40, 256),
            torch.nn.ReLU(),
            torch.nn.Linear(256, 100),
            torch.nn.ReLU(),
            torch.nn.Linear(100, 10),
        )
        opt = torch.optim.Adam(model.parameters(), lr=3e-3)
        loss_fn = torch.nn.CrossEntropyLoss()
        for _ in range(400):
            opt.zero_grad()
            loss_fn(model(x_train), y_train).backward()
            opt.step()

        model.eval()
        with torch.no_grad():
            test_logits = model(torch.tensor(x_test_np))
        test_pred = test_logits.argmax(1).numpy()
        acc = float((test_pred == y_test).mean())

        buf = io.BytesIO()
        torch.onnx.export(
            model,
            (torch.zeros(1, 40),),
            buf,
            input_names=["x"],
            output_names=["logits"],
            dynamic_axes={"x": {0: "n"}, "logits": {0: "n"}},
            dynamo=False,
        )
        runtime = OnnxRuntime(buf.getvalue())

        mde = pymde.preserve_neighbors(
            torch.tensor(x_test_np),
            embedding_dim=2,
            constraint=pymde.Standardized(),
            repulsive_fraction=1.5,
            verbose=False,
        )
        embedding_2d = mde.embed(verbose=False).cpu().numpy()
        return acc, embedding_2d, runtime, test_pred, x_test_np, y_test

    acc, embedding_2d, runtime, test_pred, x_test_np, y_test = _train()
    trained_at = time.time()
    return acc, embedding_2d, runtime, test_pred, trained_at, x_test_np, y_test


@app.cell(hide_code=True)
def status(acc, trained_at):
    _age_min = (time.time() - trained_at) / 60
    mo.md(
        f"""
        {
            "⚡ **Restored from the cache** — this MLP was trained "
            f"{_age_min:,.0f} minutes ago. The OnnxRuntime and PyMDE embedding "
            "bound here without re-running a step."
            if _age_min > 1
            else "🔥 **Cold run** — the export will carry these results as cache blobs."
        }
        Held-out accuracy **{acc:.1%}** · 400 Adam steps · 40→256→100→10 MLP
        """
    )
    return


@app.cell(hide_code=True)
def embedding_plot(embedding_2d, y_test):
    _fig, _ax = plt.subplots(figsize=(6, 5))
    _sc = _ax.scatter(
        embedding_2d[:, 0],
        embedding_2d[:, 1],
        c=y_test,
        cmap="tab10",
        s=10,
        alpha=0.6,
    )
    _ax.set_title("MNIST-1D held-out embedding (PyMDE) — lasso to pick a sample")
    _ax.set_axis_off()
    _fig.colorbar(_sc, ax=_ax, ticks=np.arange(10), shrink=0.8)
    _fig.tight_layout()
    embed_plot = mo.ui.matplotlib(_ax)
    embed_plot
    return (embed_plot,)


@app.cell(hide_code=True)
def select(embed_plot, embedding_2d):
    # Which held-out samples fall inside the lasso.
    _mask = embed_plot.value.get_mask(embedding_2d[:, 0], embedding_2d[:, 1])
    sel = np.nonzero(_mask)[0]
    return (sel,)


@app.cell(hide_code=True)
def toggle(sel):
    mo.stop(
        len(sel) == 0,
        mo.md(
            "*Lasso-select a region in the embedding above to run samples "
            "through the model.*"
        ),
    )
    pick = (
        mo.ui.slider(
            0,
            len(sel) - 1,
            value=0,
            full_width=True,
            label=f"sample within selection ({len(sel)} selected)",
        )
        if len(sel) > 1
        else None
    )
    pick if pick is not None else mo.md("**1 sample selected.**")
    return (pick,)


@app.cell(hide_code=True)
async def inference(pick, runtime, sel, test_pred, x_test_np, y_test):
    _k = pick.value if pick is not None else 0
    _i = int(sel[_k])

    # Inference runs through the cached runtime — native onnxruntime on a host,
    # onnxruntime-web in the browser.
    _logits = (await runtime.run({"x": x_test_np[_i : _i + 1]}, ["logits"]))[0][0]
    _p = np.exp(_logits - _logits.max())
    _p = _p / _p.sum()
    _pred = int(_p.argmax())

    _fig, (_ax_sig, _ax_bar) = plt.subplots(
        1, 2, figsize=(9, 2.6), width_ratios=[1, 1.2]
    )
    _ax_sig.plot(x_test_np[_i], color="#2563eb")
    _ax_sig.set_title(f"selected signal · true label {int(y_test[_i])}")
    _ax_sig.set_axis_off()

    _colors = ["#2563eb" if k == _pred else "#cbd5e1" for k in range(10)]
    _ax_bar.bar(range(10), _p, color=_colors)
    _ax_bar.set_xticks(range(10))
    _ax_bar.set_title(
        f"live ONNX prediction: {_pred} ({_p[_pred]:.0%})"
        + ("" if _pred == int(test_pred[_i]) else " · differs from cache!")
    )
    _ax_bar.set_ylim(0, 1)
    _fig.tight_layout()
    _fig
    return


@app.cell(hide_code=True)
def confusion(sel, test_pred, y_test):
    mo.stop(
        len(sel) < 5,
        mo.md("*Select at least 5 points to see a confusion matrix for the region.*"),
    )
    import matplotlib.patches as mpatches

    _yt, _yp = y_test[sel], test_pred[sel]
    _cm = np.zeros((10, 10), int)
    for _t, _p in zip(_yt, _yp):
        _cm[_t, _p] += 1

    _fig, _ax = plt.subplots(figsize=(4.6, 4.2))
    _ax.imshow(_cm, cmap="Blues")
    _ax.set_xticks(range(10))
    _ax.set_yticks(range(10))
    _ax.set_xlabel("predicted")
    _ax.set_ylabel("true")
    _ax.set_title(
        f"confusion on selection · n={len(sel)} · acc {(_yt == _yp).mean():.0%}"
    )

    _hi = _cm.max() / 2 if _cm.max() else 1
    for _t in range(10):
        for _p in range(10):
            if _cm[_t, _p]:
                _ax.text(
                    _p,
                    _t,
                    _cm[_t, _p],
                    ha="center",
                    va="center",
                    color="white" if _cm[_t, _p] > _hi else "black",
                    fontsize=8,
                )
    for _d in range(10):
        _ax.add_patch(
            mpatches.Rectangle(
                (_d - 0.5, _d - 0.5),
                1,
                1,
                fill=False,
                edgecolor="#16a34a",
                linewidth=2,
            )
        )
    _fig.tight_layout()

    mo.vstack(
        [
            mo.md(
                "*The confusion matrix uses the model's cached test predictions, "
                "which ship in the export. No per-point inference is needed.*"
            ),
            _fig,
        ]
    )
    return


@app.cell(hide_code=True)
def footer():
    mo.md(r"""
    ---
    The cached value here is the `OnnxRuntime` object itself: moutils'
    `CustomStub` stores it as exactly its ONNX bytes and restores a working
    session on the other side of the cache — including inside a static WASM
    export, where `onnxruntime-web` runs it in the browser.
    """)
    return


if __name__ == "__main__":
    app.run()
