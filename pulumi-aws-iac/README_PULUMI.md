# Create a project:

```
mkdir my-pulumi-project
cd my-pulumi-project
pulumi new python

source venv/bin/activate

```

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
