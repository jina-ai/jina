(use-hub-executor)=
# Use Hub Executors Locally


We provide three ways of using Hub Executors in your project. Each has its own use case and benefits.

## Use as-is

You can use a Hub Executor as-is via `Executor.from_hub()`:

```python
from docarray import Document, DocumentArray
from jina import Executor

exec = Executor.from_hub('jinahub://DummyHubExecutor')
da = DocumentArray([Document()])
exec.foo(da)
assert da.texts == ['hello']
```

The Hub Executor will be pulled to your local machine and run as a native Python object. You can use a line-debugger to step in/out `exec` object, set breakpoints, and observe how it behaves. You can directly feed in a `DocumentArray`. After you build some confidence in that Executor, you can move to the next step: Using it as a part of your Flow.

```{caution}
Not all Executors on the Hub can be directly run in this way - some require extra dependencies. In that case, you can add `.from_hub(..., install_requirements=True)` to install the requirements automatically. Be careful - these dependencies may not be compatible with your local packages and may override your local development environment.
```

```{tip}
Hub Executors are cached locally on the first pull. Afterwards, they will not be updated. 

To keep up-to-date with upstream, use `.from_hub(..., force_update=True)`.
```

## Use in a Flow: via Docker

Use prebuilt images from Hub in your Python code:

```python
from jina import Flow

# SECRET must be provided for private Executor
f = Flow().add(uses='jinahub+docker://<UUID>[:<SECRET>][/<TAG>]')
```

If you do not provide a `/<TAG>`, it defaults to `/latest`, which means using the `latest` tag.

````{important}
To use a private Executor, you must provide the `SECRET` which is generated after `jina hub push`.

```{figure} screenshots/secret.png
:align: center
```

````

````{admonition} Attention
:class: attention

If you are a Mac user, please use `host.docker.internal` as your URL when you want to connect a local port from an Executor
Docker container.

For example: [PostgreSQLStorage](https://hub.jina.ai/executor/d45rawx6)
will connect PostgreSQL server which was started locally. Then you must use it with:

```python
from docarray import Document
from jina import Flow

f = Flow().add(uses='jinahub+docker://PostgreSQLStorage', 
               uses_with={'hostname': 'host.docker.internal'})
with f:
    resp = f.post(on='/index', inputs=Document(), return_results=True)
    print(f'{resp}')
```
````

## Use in a Flow: via source code

Use the source code from `Hubble` in your Python code:

```python
from jina import Flow

f = Flow().add(uses='jinahub://<UUID>[:<SECRET>][/<TAG>]')
```

## Override default parameters

The default parameters of the published Executor may not be ideal for your use case. You can override
any of these by passing `uses_with` and `uses_metas` as parameters.

```python
from jina import Flow

f = Flow().add(uses='jinahub://<UUID>[:<SECRET>][/<TAG>]', 
               uses_with={'param1': 'new_value'},
               uses_metas={'name': 'new_name'})
```


(pull-executor)=
## Pulling without using

You can also use `jina hub` CLI to pull an Executor without actually using it in the Flow.

### Pull the Docker image

```bash
jina hub pull jinahub+docker://<UUID>[:<SECRET>][/<TAG>]
```


You can find the Executor by running `docker images`. You can also indicate which version of the Executor you want to use by naming the `/<TAG>`.

```bash
jina hub pull jinahub+docker://DummyExecutor/v1.0.0
```

### Pull the source code

```bash
jina hub pull jinahub://<UUID>[:<SECRET>][/<TAG>]
```


The source code of the Executor will be stored at `~/.jina/hub-packages`.

