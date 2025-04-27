# Install Poetry and Black

**Poetry** as a general-purpose tool to  **set up and manage Python environments and dependencies** .

The following link, installs poetry globally. So, you can run it from any project and environment

[https://python-poetry.org/docs/#installing-with-the-official-installer](https://python-poetry.org/docs/#installing-with-the-official-installer)

`curl -sSL [<https://install.python-poetry.org>](<https://install.python-poetry.org/>) | python3 -`

`poetry --version`

### Create a New Project

`poetry new my_project`

This setup a basic file structure and Initialize `pyproject.toml`, which is the **main file** where dependencies and settings live.

`my_project/ ├── my_project/ │    └── **init**.py ├── tests/ │    └── **init**.py ├── pyproject.toml`

If you already have a project folder, just `cd` into it and do:

`poetry init`

### Create / Manage the Virtual Environment

Poetry automatically manages a **virtual environment** for your project.

When you run any Poetry command (like `install` or `add`), it:

* Creates a venv if none exists.
* Reuses the project's venv if it exists.

No need to `python -m venv` manually!

You can check the current environment’s location:

`poetry env info --path`

You can also manually spawn a shell inside it:

`poetry shell`

or just run one-off commands inside the env:

`poetry run python [script.py](<http://script.py/>)`

### Add Dependencies

Instead of `pip install`, use:

`poetry add requests`

It updates both:

* `pyproject.toml` → adds `requests` under `[tool.poetry.dependencies]`
* `poetry.lock` → locks the exact working version for reproducibility.

**Add Dev-Only Packages** (things like linters, pytest, etc)

`poetry add --group dev black pytest`

### Install All Dependencies

When you clone someone else's repo or reset your machine

`poetry install`

Poetry will:

* Read `poetry.lock` (or `pyproject.toml`)
* Install exactly pinned versions into a fresh virtual environment.

No more `pip freeze > requirements.txt` needed!

### Remove a Package

`poetry remove <package-name>`

Example

### Configure Where the venv Lives (Optional)

By default, virtual environments are **outside** your project (`~/.cache/pypoetry/virtualenvs/`).

You can change to **local venvs** (inside your project folder):

`poetry config virtualenvs.in-project true`

### Example:

**`Install poetry globally`**

`curl -sSL [<https://install.python-poetry.org>](<https://install.python-poetry.org/>) | python3 -`

`Start a new project`

`poetry new fastapi-server`

`cd fastapi-server`

`Add FastAPI + Uvicorn`

`poetry add fastapi uvicorn`

`Start a shell inside the environment`

`poetry shell`

`Run the server`

`uvicorn fastapi_server.main:app --reload`

You need step vs code for this env.
