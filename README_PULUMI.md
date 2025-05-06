# Install Pulumi

```
curl -fsSL https://get.pulumi.com | sh  # For macOS/Linux
# For Windows, download from https://www.pulumi.com/docs/get-started/install/
```

# Create a project:

```

mkdir my-pulumi-project
cd my-pulumi-project
pulumi new python

Using pip:
source venv/bin/activate

```

**Using poetry**
When you create a Pulumi project with  **Poetry** , it automatically uses a **virtual environment** to isolate your project's dependencies.

The location depends slightly on how your Poetry is configured:

* **Default behavior** (most common): Poetry creates the virtual environment **outside** your project folder, typically somewhere like:

`~/.cache/pypoetry/virtualenvs/`

* It creates a separate folder for each project, named something like:

`<your-project-name>-<randomhash>/bin/python`

* **Project-local behavior** (optional): If you configure Poetry to create virtual environments **inside** your project directory, it would appear under:

`./venv/`

You can check **where exactly** the virtualenv is for your project by running this command inside your project:

`poetry env info --path`

It'll print the **full path** to your environment.

---

### How Should You Install New Packages?

When using Poetry, you should **always** install packages using `poetry add` rather than `pip install`.

This way, Poetry updates both your `pyproject.toml` and your `poetry.lock` files properly.

Example to install a new package (e.g., `requests`):

`poetry add requests`

This does 3 things:

* Installs the package into your virtualenv
* Updates your `pyproject.toml` dependencies section
* Locks the exact version into `poetry.lock` for reproducible installs later.

 **Important** :

Don't manually activate the virtualenv and use `pip install`. Poetry manages everything for you safely.

# Create a new stack:

```
pulumi stack init dev

```

Pulumi **creates a new stack** in its backend (local or Pulumi Cloud), **but it does not immediately create a `Pulumi.dev.yaml` file**  **until you set at least one config value or run a deployment** .

```
pulumi config set aws:region eu-west-2

```

# Delete a stack

```
pulumi stack rm dev

```

**Permanently deletes the `dev` stack** , including:

* All its configuration (`Pulumi.dev.yaml`)
* Any stack-specific secrets
* References to its state in the Pulumi backend (local or cloud)
