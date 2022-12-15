(use-hub-executor)=
# Use


We provide three ways of using Hub {class}`~jina.Executor`s in your project. Each has its own use case and benefits.

## Use as-is

You can use a Hub Executor as-is via `Executor.from_hub()`:

```python
from jina import Executor, Document, DocumentArray

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

## Use in Flow as container

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
from jina import Flow, Document

f = Flow().add(
    uses='jinahub+docker://PostgreSQLStorage',
    uses_with={'hostname': 'host.docker.internal'},
)
with f:
    resp = f.post(on='/index', inputs=Document())
    print(f'{resp}')
```
````


When `jinahub+docker://` executors are not loading properly or are having issues during initialization, please ensure sufficient Docker resources are allocated.


### Mount local volumes

You can mount volumes into your dockerized Executor by passing a list of volumes to the `volumes` argument:

```python
f = Flow().add(
    uses='docker://my_containerized_executor',
    volumes=['host/path:/path/in/container', 'other/volume:/app'],
)
```

````{admonition} Hint
:class: hint
If you want your containerized Executor to operate inside one of these volumes, remember to set its {ref}`workspace <executor-workspace>` accordingly!
````

If you do not specify `volumes`, Jina will automatically mount a volume into the container.
In this case, the volume source will be your {ref}`default Executor workspace <executor-workspace>`, and the volume destination will
be `/app`. Additionally, automatic volume setting will try to move the Executor's workspace into the volume destination.
Depending on the default executor workspace on your system this may not always succeed, so explicitly mounting a volume and setting
a workspace is recommended.

You can disable automatic volume setting by passing `f.add(..., disable_auto_volume=True)`.

## Use in Flow via source code

Use the source code from `Hubble` in your Python code:

```python
from jina import Flow

f = Flow().add(uses='jinahub://<UUID>[:<SECRET>][/<TAG>]')
```

## Set/override default parameters

The default parameters of the published Executor may not be ideal for your use case. You can override
any of these by passing `uses_with` and `uses_metas` as parameters.

```python
from jina import Flow

f = Flow().add(
    uses='jinahub://<UUID>[:<SECRET>][/<TAG>]',
    uses_with={'param1': 'new_value'},
    uses_metas={'name': 'new_name'},
)
```


(pull-executor)=
## Pull only

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

