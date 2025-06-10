import marimo

__generated_with = "0.13.15"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    from moutils import shell

    return mo, shell


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # Shell Widget Examples

    The ShellWidget allows you to run shell commands interactively in your notebook.
    Click the buttons below to execute various shell commands.
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Basic Commands""")
    return


@app.cell
def _(shell):
    # List current directory contents
    ls_widget = shell("ls -la")
    ls_widget
    return


@app.cell
def _(shell):
    # Show current working directory
    pwd_widget = shell("pwd")
    pwd_widget
    return


@app.cell
def _(shell):
    # Check Python version
    python_version = shell("python --version")
    python_version
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## System Information""")
    return


@app.cell
def _(shell):
    # Show system information (works on macOS/Linux)
    uname_widget = shell("uname -a")
    uname_widget
    return


@app.cell
def _(shell):
    # Show disk usage
    disk_usage = shell("df -h")
    disk_usage
    return


@app.cell
def _(shell):
    # Show running processes
    processes = shell("ps aux | head -10")
    processes
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Development Commands""")
    return


@app.cell
def _(shell):
    # Find Python files in current directory
    shell("find . -name '*.py' -type f | head -10")
    return


@app.cell
def _(shell):
    # Show git status (if in a git repo)
    shell("git status --porcelain")
    return


@app.cell
def _(shell):
    # Check if we're in a Python environment
    shell("pip list | head -10")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Working Directory Example""")
    return


@app.cell
def _(shell):
    # Run command in a specific directory
    # This will list the contents of the notebooks directory
    shell("ls -la", working_directory="./notebooks")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## Tips

    - Commands run asynchronously and stream output in real-time
    - Use the `working_directory` parameter to run commands in specific directories
    - Commands that require user input won't work (they're non-interactive)
    - Long-running commands can be interrupted by refreshing the page
    - Error codes and completion status are shown at the end of execution
    """
    )
    return


if __name__ == "__main__":
    app.run()
