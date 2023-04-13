# Health Check

Once an Orchestration is running, you can use `jina ping` [CLI](../../api/jina_cli.rst) to run a health check of the complete Orchestration or (in the case of a Flow) individual Executors or Gateway.

````{tab} Deployment
Start a Deployment in Python:

```python
from jina import Deployment

dep = Deployment(protocol='grpc', port=12345)

with dep:
    dep.block()
```

Check the readiness of the Deployment:

```bash
jina ping deployment grpc://localhost:12345
```
````
````{tab} Flow
Start a Flow in Python:

```python
from jina import Flow

f = Flow(protocol='grpc', port=12345).add(port=12346)

with f:
    f.block()
```

Check the readiness of the Flow:

```bash
jina ping flow grpc://localhost:12345
```

You can also check the readiness of an individual Executor:

```bash
jina ping executor localhost:12346
```

...or the readiness of the Gateway service:

```bash
jina ping gateway  grpc://localhost:12345
```
````

When these commands succeed, you should see something like:

```text
INFO   JINA@28600 readiness check succeeded 1 times!!! 
```

```{admonition} Use in Kubernetes
:class: note
The CLI exits with code 1 when the readiness check is not successful, which makes it a good choice to be used as readinessProbe for Executor and Gateway when
deployed in Kubernetes.
```
