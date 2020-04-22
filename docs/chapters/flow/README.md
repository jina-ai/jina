# Using Flow API to Compose Your Jina Workflow

In a search system, task such as indexing is a workflow often involves multiple steps: preprocessing, encoding, storing etc. In Jina's architecture, each step is implemented by an Executor and wrapped by a Pod. This microservice design makes the whole pipeline flexible and scalable. Accomplishing a task is then orchestrating all these Pods work together, either sequentially or in parallel; locally or remotely. 

Flow API is a context manager for Pods. Each `Flow` object corresponds to a real-world task, it helps user to manage the states and contexts of all Pods required in that task. Flow API translates a workflow defined in Python code, YAML spec and interactive graph to a runtime backed by multi-thread/process, Kubernetes, Docker Swarm, etc. Users don't need to worry about where the Pod is running and how the Pods are connected.


<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->


<!-- END doctoc generated TOC please keep comment here to allow auto update -->



## Using Flow API in Python

### Create a Flow 

To create a new Flow:

```python
from jina.flow import Flow

f = Flow()
```

`Flow()` accepts some arguments, see `jina flow --help` or [our documentations](https://docs.jina.ai) for details. For example, `Flow(log_server=True)` will enable the logs emission to the [dashboard](https://github.com/jina-ai/dashboard). 

When the arguments given to `Flow()` can not be parsed, they will be propagated to all its `Pod` for parsing (if they accept, see `jina pod --help` for the list of arguments). For example, 

```python
f = Flow(read_only=True)
```

will override `read_only` attribute of all Pods in `f` to `True`.

### Add Pod into the Flow

To add a Pod to Flow, simply call `.add()`. For example,

```python
f = (Flow().add(name='p1', yaml_path='mypod1.yml')
           .add(name='p2', yaml_path='mypod2.yml', timeout_ready=50000)
           .add(name='p3', yaml_path='mypod3.yml', read_only=True))
``` 

This will create a sequential workflow 
```

gateway -> p1 -> p2 -> p3 -> gateway

``` 

The input of a Pod is the output of the last Pod in sequential order. The gateway is the entrypoint of the whole Jina network. The `gateway` Pod will be automatically added to every `Flow`, of which the output is the first Pod and the input is the last Pod defined in the Flow.

All accepted arguments follow the command line interface of `Pod`, which can be found in `jina pod --help`. Just remember replace the dash `-` to underscore `_` in the name of the argument when referring it in Python.

#### Add a Containerized Pod into the Flow

To run a Pod in a Docker container, simply specify the `image` argument.

```python
f = (Flow().add(name='p1')
           .add(name='p2', image='jinaai/hub.executors.encoders.bidaf:latest')
           .add(name='p3'))
``` 

This will run `p2` in a Docker container equipped with image `jinaai/hub.executors.encoders.bidaf:latest`. More information on using container Pod can be found in [our documentations](https://docs.jina.ai). 

#### Add a Remote Pod into the Flow

To run a Pod remotely, simply specify the `host` and `port_grpc` arguments. For example,

```python
f = (Flow().add(name='p1')
           .add(name='p2', host='192.168.0.100', port_grpc=53100)
           .add(name='p3'))
```

This will start `p2` remotely on `192.168.0.100`, whereas `p1` and `p3` run locally.

To use remote Pod feature, you need to start a `gateway` on `192.168.0.100` in advance. More information on using remote Pod can be found in [our documentations](https://docs.jina.ai).  


### Parallelize the Steps

By default, if you keep `.add()` to a `Flow`, it will create a long chain of sequential workflow. You can parallelize some of the steps by using `needs` argument. For example,

```python
f = (Flow().add(name='p1')
           .add(name='p2')
           .add(name='p3', needs='p1'))
```

This creates a workflow, where `p2` and `p3` work in parallel with the output of `p1`. 
```
gateway -> p1 -> p2
            |
              -> p3 -> gateway 
```

### Wait Parallel Steps to Finish


In the last example, the message is returned to the gateway regardless the status `p2`. To wait multiple parallel steps to finish before continue, you can do:

```python
f = (Flow().add(name='p1')
           .add(name='p2')
           .add(name='p3', needs='p1')
           .join(['p2', 'p3']))
```
  
which gives

```
gateway -> p1 -> p2 ->
            |          | -> wait until both done -> gateway
              -> p3 -> 
```



### Run a Flow

To run a Flow, simply use `with` keyword:

```python
f = (Flow().add(...)
           .add(...))

with f:
    # the flow is now running

```

Though one can manually call `start()` method to run the flow, but then you also need to call `close()` method correspondingly to release the resource. Using `with` saves you the trouble, the resource is automatically released when running out of the scope. 

#### Test the Connectivity with Dry Run

You can test the whole workflow with `dry_run()`. For example,

```python

with f:
    f.dry_run()

```

This will send `ControRequest` to all pods following the topology you defined. You can use it to test the connectivity of all pods. 

### Feed Data to the Flow

You can use `.index()`, `.search()` to feed index data and search query to a flow:

```python
with f:
    f.index(raw_bytes)
```

```python
with f:
    f.search(raw_bytes, top_k=50, callback=print)
```

- `raw_bytes` is `Iterator[bytes]`, each of which corresponds to a bytes representation of a Document.
- `callback` is the callback function after each request, take `Request` protobuf as the only input.

A simple `raw_bytes` can be `input_fn` defined as follows:

```python
def input_fn():
    for _ in range(10):
        yield b's'


# or ...
input_fn = (b's' for _ in range(10))
```

> Please note that the current Flow API does not support using `index()` `search()` in mix under one `with` scope. This is because the workflow of index and search are usually different, you can not use one workflow for both tasks.

#### Feed Data to the Flow using Other Client

If you don't use Python as client, or your client and flow are on different instances. You can hold a flow in running state and use client in other languages to connect to it. Simply:

```python
with f:
    while True:
        pass
```

## Use Flow API in YAML

You can also write a Flow in YAML. For example,

```yaml
!Flow
with:
  logserver: true
pods:
  chunk_seg:
    yaml_path: craft/index-craft.yml
    replicas: $REPLICAS
    read_only: true
  doc_idx:
    yaml_path: index/doc.yml
  tf_encode:
    yaml_path: encode/encode.yml
    needs: chunk_seg
    replicas: $REPLICAS
    read_only: true
  chunk_idx:
    yaml_path: index/chunk.yml
    replicas: $SHARDS
    separated_workspace: true
  join_all:
    yaml_path: _merge
    needs: [doc_idx, chunk_idx]
    read_only: true
```

You can use enviroment variables via `$` in YAML. More information on the Flow YAML Schema can be found in [our documentations](https://docs.jina.ai). 

### Load a Flow from YAML

```python
from jina.flow import Flow
f = Flow.load_config('myflow.yml')
```

### Start a Flow Directly from the CLI

The following command will start a flow from the console and hold it for client to connect.

```bash
jina flow --yaml-path myflow.yml
``` 


## Design a Flow with Dashboard

With Jina Dashboard, you can interactively drag-n-drop Pod, set its attribute and export to a Flow YAML file.  

![Dashboard](flow-demo.gif)


More information on the dashboard can be found in [here](https://github.com/jina-ai/dashboard).