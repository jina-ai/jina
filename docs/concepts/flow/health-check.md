# Health Check

Once a Flow is running, you can use `jina ping`  {ref}`CLI <../api/jina_cli>` to run a health check of the complete Flow or of individual Executors or Gateway.

Start a Flow in Python:

```python
from jina import Flow

with Flow(protocol='grpc', port=12345).add(port=12346) as f:
    f.block()
```

Check the readiness of the Flow:

```bash
jina ping flow grpc://localhost:12345
```

You can also check the readiness of an Executor:

```bash
jina ping executor localhost:12346
```

...or the readiness of the Gateway service:

```bash
jina ping gateway  grpc://localhost:12345
```

When these commands succeed, you should see something like:

```text
INFO   JINA@28600 readiness check succeeded 1 times!!! 
```

```{admonition} Use in Kubernetes
:class: note
The CLI exits with code 1 when the readiness check is not successful, which makes it a good choice to be used as readinessProbe for Executor and Gateway when
deployed in Kubernetes.
```


