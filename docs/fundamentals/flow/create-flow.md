(flow)=
# Basics


A {class}`~jina.Flow` defines how your Executors are connected together and how your data *flows* through them.


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

```{figure} zero-flow.svg
:scale: 70%
```

For production, you should define your Flows with YAML. This is because YAML files are independent of the Python logic code and easier to maintain.


### Conversion between Python and YAML

A Python Flow definition can be easily converted to/from a YAML definition.

To load a Flow from a YAML file, use {meth}`~jina.Flow.load_config`:

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

There are three ways to start a Flow: In Python, from a YAML file, or from the terminal.

- Generally in Python: use Flow as a context manager in Python.
- As an entrypoint from terminal: use `Jina CLI <cli>` and a Flow YAML file.
- As an entrypoint from Python code: use Flow as a context manager inside `if __name__ == '__main__'`
- No context manager: manually call {meth}`~jina.Flow.start` and {meth}`~jina.Flow.close`.


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

Your addresses and entrypoints can be found in the output. When you enable more features such as monitoring, HTTP gateway, TLS encryption, this display expands to contain more information.

(multiprocessing-spawn)
### Set multiprocessing `spawn` 

Some corner cases require forcing a `spawn` start method for multiprocessing, for example if you encounter "Cannot re-initialize CUDA in forked subprocess". 

You can use `JINA_MP_START_METHOD=spawn` before starting the Python script to enable this.

```bash
JINA_MP_START_METHOD=spawn python app.py
```

```{caution}
In case you set `JINA_MP_START_METHOD=spawn`, make sure to use Flow as a context manager inside `if __name__ == '__main__'`.
The script entrypoint (starting the flow) [needs to be protected when using `spawn` start method](https://docs.python.org/3/library/multiprocessing.html#the-spawn-and-forkserver-start-methods). 
```

````{hint}
There's no need to set this for Windows, as it only supports spawn method for multiprocessing. 
````

## Serve forever

In most scenarios, a Flow should remain reachable for prolonged periods of time.
This can be achieved by `jina flow --uses flow.yml` from the terminal.

Or if you are serving a Flow from Python:

```python
from jina import Flow

f = Flow()

with f:
    f.block()
```

The `.block()` method blocks the execution of the current thread or process, enabling external clients to access the Flow.

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

(restart-flow)=
## Restart

While developing your Flow, it can be useful to have the Flow be restarted automatically as you keep applying changes to the Flow YAML.

For this you can use the `restart` argument for the Flow so that it watches changes in the configuration YAML code and makes sure that the Flow is restarted with the new configuration.

````{admonition} Caution
:class: caution
This feature is thought to let the developer iterate faster while developing but is not intended to be used in production environment.
````

````{admonition} Note
:class: note
This feature requires watchfiles>=0.18 package to be installed.
````

To see how this would work, let's have a Flow defined in a file `flow.yml` with restart option.
```yaml
jtype: Flow
with:
  port: 12345
  restart: True
executors:
- name: exec1
  uses: ConcatenateTextExecutor
```

We build a Flow and expose it:

```python
import os
from jina import Flow, Executor, requests


class ConcatenateTextExecutor(Executor):
   @requests
   def foo(self, docs, **kwargs):
       for doc in docs:
          doc.text += 'add text '

os.environ['JINA_LOG_LEVEL'] = 'DEBUG'


f = Flow.load_config('flow.yml')

with f:
    f.block()
```

We can see that the Flow is running and serving:

```python
from jina import Client, DocumentArray

c = Client(port=12345)

print(c.post(on='/', inputs=DocumentArray.empty(1))[0].text)
```

```text
add text
```

We can edit the Flow YAML file and save the changes:

```yaml
jtype: Flow
with:
  port: 12345
  restart: True
executors:
- name: exec1
  uses: ConcatenateTextExecutor
- name: exec2
  uses: ConcatenateTextExecutor
```

You should see in the logs of the Flow

```text
INFO   Flow@28301 change in Flow YAML XXX/flow.yml observed, restarting Flow                                                   
```

And after this, the Flow will have 2 Executors with the new topology

```python
from jina import Client, DocumentArray

c = Client(port=12345)

print(c.post(on='/', inputs=DocumentArray.empty(1))[0].text)
```

```text
add text add text
```


## Visualize

A {class}`~jina.Flow` has a built-in `.plot()` function which can be used to visualize the `Flow`:
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

You can also do it in the terminal:

```bash
jina export flowchart flow.yml flow.svg 
```

You can also visualize a remote Flow by passing the URL to `jina export flowchart`.

## Export

A {class}`~jina.Flow` YAML can be exported as a Docker Compose YAML or a Kubernetes YAML bundle. 

### Docker Compose
```python
from jina import Flow

f = Flow().add()
f.to_docker_compose_yaml()
```

You can also do it in the terminal:

```shell
jina export docker-compose flow.yml docker-compose.yml 
```

This will generate a single `docker-compose.yml` file containing all the Executors of the Flow.

For advanced utilization of Docker Compose with Jina, refer to {ref}`How to <docker-compose>` 

(kubernetes-export)=
### Kubernetes

```python
from jina import Flow

f = Flow().add()
f.to_kubernetes_yaml('flow_k8s_configuration')
```

You can also do it in the terminal:

```shell
jina export kubernetes flow.yml ./my-k8s 
```

This generates the Kubernetes configuration files for all the {class}`~jina.Executor`s in the Flow.
The generated folder can be used directly with `kubectl` to deploy the Flow to an existing Kubernetes cluster.

For advanced utilisation of Kubernetes with Jina please refer to {ref}`How to <kubernetes>` 


```{tip}
Based on your local Jina version, Executor Hub may rebuild the Docker image during the YAML generation process.
If you do not wish to rebuild the image, set the environment variable `JINA_HUB_NO_IMAGE_REBUILD`.
```

```{tip}
If an Executor requires volumes to be mapped for them to persist data, Jina will create a StatefulSet for that Executor instead of a Deployment.
You can control the access mode, storage class name and capacity of the attached Persistent Volume Claim by using {ref}`Jina environment variables <jina-env-vars>`  
`JINA_K8S_ACCESS_MODES`, `JINA_K8S_STORAGE_CLASS_NAME` and `JINA_K8S_STORAGE_CAPACITY`. Only the first volume will be considered to be mounted.
```

```{admonition} See also
:class: seealso
For more in-depth guides on Flow deployment, check our how-tos for {ref}`Docker compose <docker-compose>` and
{ref}`Kubernetes <kubernetes>`.
```

