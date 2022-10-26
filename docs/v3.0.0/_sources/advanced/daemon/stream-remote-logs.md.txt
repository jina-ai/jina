# Remote Logs

We can stream logs from a JinaD server for a running Flow/Pod/Deployment/Workspace.

Unlike other modules, this needs to be awaited.

```python
from daemon.clients import AsyncJinaDClient

client = AsyncJinaDClient(host=HOST, port=PORT)
await client.logs(id=my_workspace_id)
```

```text
🌏 2358d9ab978a DaemonWorker8 INFO Step 1/5 : ARG LOCALTAG=test
🌏 2358d9ab978a DaemonWorker8 INFO Step 2/5 : FROM jinaai/jina:$LOCALTAG-daemon
🌏 2358d9ab978a DaemonWorker8 INFO  ---> c7d3770bb8bf
🌏 2358d9ab978a DaemonWorker8 INFO Step 3/5 : ARG PIP_REQUIREMENTS
🌏 2358d9ab978a DaemonWorker8 INFO  ---> Using cache
🌏 2358d9ab978a DaemonWorker8 INFO  ---> fef3bbb778c9
🌏 2358d9ab978a DaemonWorker8 INFO Step 4/5 : RUN if [ -n "$PIP_REQUIREMENTS" ]; then         echo "Installing ${PIP_REQUIREMENTS}";         for package in ${PIP_REQUIREMENTS}; do             pip install "${package}";         done;     fi
🌏 2358d9ab978a DaemonWorker8 INFO  ---> Using cache
🌏 2358d9ab978a DaemonWorker8 INFO  ---> 30ad9229b620
🌏 2358d9ab978a DaemonWorker8 INFO Step 5/5 : WORKDIR /workspace
🌏 2358d9ab978a DaemonWorker8 INFO  ---> Using cache
🌏 2358d9ab978a DaemonWorker8 INFO  ---> ee1abbf16f0e
🌏 2358d9ab978a DaemonWorker8 INFO Successfully built ee1abbf16f0e
🌏 2358d9ab978a DaemonWorker8 INFO Successfully tagged jworkspace:13305e16-aa7b-4f58-b0e9-1f420eb8be8b
🌏 2358d9ab978a DaemonWorker8 Level SUCCESS workspace jworkspace-13305e16-aa7b-4f58-b0e9-1f420eb8be8b is updated
```

