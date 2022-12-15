(flow)=
# Basic


Flow defines how your Executors are connected together and how your data *flows* through them.

Every Flow can be defined either purely in Python, or be loaded from a YAML file.

````{admonition} Best practice
:class: hint

For production use we recommend YAML files to configure your Flows. This is because YAML files are:

- independent of Python source code
- easy to edit, maintain and extend
- human-readable

````

## Create

The most trivial Flow is the empty Flow and, like any other Flow, it can be instantiated purely in Python, or from a
YAML file:

````{tab} Python

```python
from jina import Flow

f = Flow()  # Create the empty Flow
with f:  # Using it as a Context Manager will start the Flow
    f.post(on='/search')  # This sends a request to the /search endpoint of the Flow
```
````

`````{tab} YAML
`flow.yml`:

```yaml
jtype: Flow
```

```python
from jina import Flow

f = Flow.load_config('flow.yml')  # Load the Flow definition from Yaml file

with f:  # Using it as a Context Manager will start the Flow
    f.post(on='/search')  # This sends a request to the /search endpoint of the Flow
```

````{admonition} Hint: Dump Flow configuration
:class: hint

In addition to loading a Flow from a YAML file, you can also save an existing Flow configuration to YAML. To do so, execute `f.save_config('path/to/flow.yml')`.
````
`````


## Start and stop

When a Flow starts, all its {ref}`added Executors <flow-add-executors>` will start as well, making it possible to {ref}`reach the service through its API <access-flow-api>`.

Jina Flows are context managers and can be started and stopped using Pythons `with` notation:

```python
from jina import Flow

f = Flow()

with f:
    pass
```

The statement `with f:` starts the Flow, and exiting the indented `with` block stops the Flow, including all Executors defined in it.


### Start inside `__main__`

If applicable, always start the Flow inside `if __name__ == '__main__'`. For example:

````{tab} ✅ Do
```{code-block} python
---
emphasize-lines: 13, 14
---

from jina import Flow, Executor, requests

class CustomExecutor(Executor):
    @requests
    async def foo(self, **kwargs):
        ...

f = Flow().add(uses=CustomExecutor)

if __name__ == '__main__':
    with f:
        ...
```
````

````{tab} 😔 Don't
```{code-block} python
---
emphasize-lines: 2
---

from jina import Flow, Executor, requests

class CustomExecutor(Executor):
    @requests
    def foo(self, **kwargs):
        ...

f = Flow().add(uses=CustomExecutor)
with f:
    ...

"""
# error
This probably means that you are not using fork to start your
child processes and you have forgotten to use the proper idiom
in the main module:

    if _name_ == '_main_':
        freeze_support()
        ...

The "freeze_support()" line can be omitted if the program
is not going to be frozen to produce an executable.

"""
```

````

### Set multiprocessing `spawn` 

Some cornet cases require to force `spawn` start method for multiprocessing, e.g. if you encounter "Cannot re-initialize CUDA in forked subprocess". 

You may try `JINA_MP_START_METHOD=spawn` before starting the Python script to enable this.

```bash
JINA_MP_START_METHOD=spawn python app.py
```

````{hint}
There's no need to set this for Windows, as it only supports spawn method for multiprocessing. 
````

## Serve forever

In most scenarios, a Flow should remain reachable for prolonged periods of time.
This can be achieved by *blocking* the execution:

```python
from jina import Flow

f = Flow()
with f:
    f.block()
```

The `.block()` method blocks the execution of the current thread or process, which enables external clients to access the Flow.

In this case, the Flow can be stopped by interrupting the thread or process. Alternatively, a `multiprocessing` or `threading` `Event` object can be passed to `.block()`, which stops the Flow once set.

```python
from jina import Flow
import threading


def start_flow(stop_event):
    """start a blocking Flow."""
    with Flow() as f:
        f.block(stop_event=stop_event)


e = threading.Event()  # create new Event

t = threading.Thread(name='Blocked-Flow', target=start_flow, args=(e,))
t.start()  # start Flow in new Thread

# do some stuff

e.set()  # set event and stop (unblock) the Flow
```



## Visualize

Flow has a built-in `.plot()` function which can be used to visualize a `Flow`:
```python
from jina import Flow

f = Flow().add().add()
f.plot('flow.svg')
```

```{figure} flow.svg
:width: 70%

```

```python
from jina import Flow

f = Flow().add(name='e1').add(needs='e1').add(needs='e1')
f.plot('flow-2.svg')
```

```{figure} flow-2.svg
:width: 70%
```

One can also do it in the terminal via:

```bash
jina export flowchart flow.yml flow.svg 
```

## Export

Flow YAML can be exported as a Docker Compose YAML or a Kubernetes YAML bundle. 

### Docker Compose
```python
from jina import Flow

f = Flow().add()
f.to_docker_compose_yaml()
```

One can also do it in the terminal via:

```bash
jina export docker-compose flow.yml docker-compose.yml 
```

This will generate a single `docker-compose.yml` file containing all the Executors of the Flow.



### Kubernetes

```python
from jina import Flow

f = Flow().add()
f.to_kubernetes_yaml('flow_k8s_configuration')
```

One can also do it in the terminal via:

```bash
jina export docker-compose flow.yml ./my-k8s 
```

This will generate the necessary Kubernetes configuration files for all the `Executors` of the `Flow`.
The generated folder can be used directly with `kubectl` to deploy the `Flow` to an existing Kubernetes cluster.



```{tip}
Based on your local Jina version, Jina Hub may rebuild the Docker image during the YAML generation process.
If you do not wish to rebuild the image, set the environment variable `JINA_HUB_NO_IMAGE_REBUILD`.
```


```{admonition} See also
:class: seealso
For more in-depth guides on Flow deployment, take a look at our how-tos for {ref}`Docker compose <docker-compose>` and
{ref}`Kubernetes <kubernetes>`.
```

