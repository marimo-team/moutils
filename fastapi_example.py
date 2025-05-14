import marimo

__generated_with = "0.13.8"
app = marimo.App(width="medium")

with app.setup:
    from fastapi import FastAPI

    fast = FastAPI()


@app.function
@fast.post("/add")
def add(x: int, y: int):
    """Add two numbers."""
    return x + y


@app.function
@fast.get("/me")
def me():
    """Add two numbers."""
    return "hi"


@app.cell
def _():
    fast
    return


if __name__ == "__main__":
    app.run()
