(use-hub-executor)=
# Use Hub Executor

## Use as-is

```{tip}
Starting `jina>=2.2.5`, you can directly use Hub Executor as native Python object *without* putting it into a Flow.  
```

You can use Hub Executor as-is via `Executor.from_hub()`:

```python
from jina import Executor, DocumentArray, Document

exec = Executor.from_hub('jinahub://DummyHubExecutor')
da = DocumentArray([Document()])
exec.foo(da)
assert da.texts == ['hello']
```

The Hub Executor will be pulled to local and run as a native Python object. You can use line-debugger to step in/out `exec` object, set breakpoint, and observe how it behaves. You can directly feed `DocumentArray` to it. After you build some confidence about that Executor, you can move to the next step: using it as a part of your Flow pipeline.

```{caution}
Not all executors on the Hub can be directly run in this way, some requires extra dependencies. In that case you can add `.from_hub(..., install_requirements=True)`, it will install the requirements automatically. Be careful, these dependencies may not be compatible to your local packages and may override your local dev environment.
```

```{tip}
Hub Executor are cached to local on the first pulling. Afterwards, it will not be updated. 

To keep up-to-date with upstream, use `.from_hub(..., force_update=True)`.
```

## Use in a Flow: via Docker

Use the prebuilt images from Hub in your python codes,

```python
from jina import Flow

# SECRET must be provided for private Executor
f = Flow().add(uses='jinahub+docker://<UUID>[:<SECRET>][/<TAG>]')
```

If there is no `/<TAG>` provided when using, it by default equals to `/latest`, which means using the `latest` tag.

````{important}
To use private Executor, you must provide the `SECRET`. It is generated after `jina hub push`.

```{figure} screenshots/secret.png
:align: center
```

````

````{admonition} Attention
:class: attention

If you are a Mac user, please use `host.docker.internal` as your url when you want to connect a local port from Executor
docker container.

For example: [PostgreSQLStorage](https://hub.jina.ai/executor/d45rawx6)
will connect PostgreSQL server which was started at local. Then you must use it with:

```python
from jina import Flow, Document

f = Flow().add(uses='jinahub+docker://PostgreSQLStorage', 
               uses_with={'hostname': 'host.docker.internal'})
with f:
    resp = f.post(on='/index', inputs=Document(), return_results=True)
    print(f'{resp}')
```
````

## Use in a Flow: via source code

Use the source codes from `Hubble` in your python codes,

```python
from jina import Flow

f = Flow().add(uses='jinahub://<UUID>[:<SECRET>][/<TAG>]')
```

## Override default parameters

It is possible that the default parameters of the published Executor may not be ideal for your use case. You can override
any of these parameters by passing `uses_with` and `uses_metas` as parameters.

```python
from jina import Flow

f = Flow().add(uses='jinahub://<UUID>[:<SECRET>][/<TAG>]', 
               uses_with={'param1': 'new_value'},
               uses_metas={'name': 'new_name'})
```

This way, the Executor will work with the overridden parameters.


(pull-executor)=
## Pulling without using

You can also use `jina hub` CLI to pull an executor without actually using it in the Flow.

### Pull the Docker image

```bash
jina hub pull jinahub+docker://<UUID>[:<SECRET>][/<TAG>]
```


You can find the Executor by running this command `docker images`. You can also indicate which version of the Executor you want to use by naming the `/<TAG>`.

```bash
jina hub pull jinahub+docker://DummyExecutor/v1.0.0
```

### Pull the source code

```bash
jina hub pull jinahub://<UUID>[:<SECRET>][/<TAG>]
```


The source code of the Executor will be stored at `~/.jina/hub-packages`.

