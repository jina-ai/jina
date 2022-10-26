(flow)=
# Basic


{class}`~jina.Flow` defines how your Executors are connected together and how your data *flows* through them.


## Create

The most trivial {class}`~jina.Flow` is the empty Flow. It can be defined purely in Python or from a YAML file:

````{tab} Python

```python
from jina import Flow

f = Flow()
```
````

`````{tab} YAML
```yaml
jtype: Flow
```
`````

```{tip}
An empty Flow contains only {ref}`the Gateway<flow>`.
```

For production, we recommend YAML files to define the Flows. This is because YAML files are independent of Python logic code and easy to maintain.




### Conversion between Python and YAML

Python Flow definition can be easily converted to/from YAML definition.

To load a Flow from a YAML file, use the {meth}`~jina.Flow.load_config`:

```python
from jina import Flow

f = Flow.load_config('flow.yml')
```

To export an existing Flow definition to a YAML file use {meth}`~jina.Flow.save_config`:

```python
from jina import Flow

f = Flow().add().add()  # Create a Flow with two Executors

f.save_config('flow.yml')
```

## Start and stop

When a {class}`~jina.Flow` starts, all its {ref}`added Executors <flow-add-executors>` will start as well, making it possible to {ref}`reach the service through its API <access-flow-api>`.

There are three ways to start a Flow. Depending on the use case, you can start a Flow either in Python, or from a YAML file, or from the terminal.

- Generally in Python: use Flow as a context manager in Python.
- As an entrypoint from terminal: use Jina CLI and a Flow YAML.
- As an entrypoint from Python code: use Flow as a context manager inside `if __name__ == '__main__'`
- No context manager: manually call {meth}`~jina.Flow.start`  and {meth}`~jina.Flow.close`.


````{tab} General in Python
```python
from jina import Flow

f = Flow()

with f:
    pass
```
````

````{tab} Jina CLI entrypoint
```bash
jina flow --uses flow.yml
```
````

````{tab} Python entrypoint
```python
from jina import Flow

f = Flow()

if __name__ == '__main__':
    with f:
        pass
```
````

````{tab} Python no context manager
```python
from jina import Flow

f = Flow()

f.start()

f.close()
```
````

The statement `with f:` starts the Flow, and exiting the indented `with` block stops the Flow, including all Executors defined in it.


A successful start of a Flow looks like this:

```{figure} success-flow.png
:scale: 70%
```

Your addresses and entrypoints can be found in the output. When enabling more features such as monitoring, HTTP gateway, TLS encryption, this display will also expand to contain more information.


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
This can be achieved by `jina flow --uses flow.yml` from terminal.


Or if you are serving a Flow from Python:

```python
from jina import Flow

f = Flow()

with f:
    f.block()
```

The `.block()` method blocks the execution of the current thread or process, which enables external clients to access the Flow.

In this case, the Flow can be stopped by interrupting the thread or process. 

### Server until an event

Alternatively, a `multiprocessing` or `threading` `Event` object can be passed to `.block()`, which stops the Flow once set.

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

A {class}`~jina.Flow` has a built-in `.plot()` function which can be used to visualize a `Flow`:
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

One can also visualize a remote Flow by passing the URL to `jina export flowchart`.

## Export

A {class}`~jina.Flow` YAML can be exported as a Docker Compose YAML or a Kubernetes YAML bundle. 

### Docker Compose
```python
from jina import Flow

f = Flow().add()
f.to_docker_compose_yaml()
```

One can also do it in the terminal via:

```shell
jina export docker-compose flow.yml docker-compose.yml 
```

This will generate a single `docker-compose.yml` file containing all the Executors of the Flow.

For an advance utilisation of Docker Compose with jina please refer to this {ref}`How to <docker-compose>` 


### Kubernetes

```python
from jina import Flow

f = Flow().add()
f.to_kubernetes_yaml('flow_k8s_configuration')
```

One can also do it in the terminal via:

```shell
jina export kubernetes flow.yml ./my-k8s 
```

This will generate the necessary Kubernetes configuration files for all the {class}`~jina.Executor`s of the Flow.
The generated folder can be used directly with `kubectl` to deploy the Flow to an existing Kubernetes cluster.

For an advance utilisation of Kubernetes with jina please refer to this {ref}`How to <kubernetes>` 


```{tip}
Based on your local Jina version, Jina Hub may rebuild the Docker image during the YAML generation process.
If you do not wish to rebuild the image, set the environment variable `JINA_HUB_NO_IMAGE_REBUILD`.
```


```{admonition} See also
:class: seealso
For more in-depth guides on Flow deployment, take a look at our how-tos for {ref}`Docker compose <docker-compose>` and
{ref}`Kubernetes <kubernetes>`.
```

