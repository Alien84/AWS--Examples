# Step-by-Step: Full Remote Debugging Pulumi in VS Code

---

---


1. Install the `debugpy` package: This allows your running Pulumi app to open a remote debug server.
2. At the very **top** of your `__main__.py`, insert:

**
    What happens?**

* Your program starts
* It **waits** until you attach a debugger to port **5678**
* After attaching, Pulumi continues running normally

```bash
import debugpy

# Allow other machines to attach if needed
debugpy.listen(("0.0.0.0", 5678))
print("⏳ Waiting for debugger attach...")

# Pause the program until VS Code attaches
debugpy.wait_for_client()
print("✅ Debugger attached, continuing execution.")

```

3. Create a `.vscode/launch.json` (or edit if already there) and add. This tells VS Code **where** to find the running debug server.

```bash
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Attach to Pulumi Debugpy",
      "type": "debugpy",
      "request": "attach",
      "connect": {
        "host": "localhost",
        "port": 5678
      },
      "pathMappings": [
        {
          "localRoot": "${workspaceFolder}",
          "remoteRoot": "."
        }
      ]
    }
  ]
}

```


4. In your terminal,  **run Pulumi normally** :

```bash
pulumi up
```

5. Start debugging
