# Using Flow API to Compose Your Jina Workflow

In a search system, a task such as indexing often involves multiple steps: preprocessing, encoding, storing, etc. In Jina's architecture, each step is implemented by an Executor and wrapped by a Pod. This microservice design makes the whole pipeline flexible and scalable. Accomplishing a task is then orchestrating all these Pods work together, either sequentially or in parallel; locally or remotely. 

Flow API is a context manager for Pods. Each `Flow` object corresponds to a real-world task. It helps the user to manage the states and contexts of all Pods required in that task. Flow API translates a workflow defined in Python code, YAML spec and interactive graph to a runtime backed by multi-thread/process, Kubernetes, Docker Swarm, etc. Users don't need to worry about where the Pod is running and how the Pods are connected.

![Flow is a context manager](flow-api-doc.png)

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->


- [Using Flow API in Python](#using-flow-api-in-python)
- [Use Flow API in YAML](#use-flow-api-in-yaml)
- [Design a Flow with Dashboard](#design-a-flow-with-dashboard)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->



## Using Flow API in Python

### Create a Flow 

To create a new Flow:

```python
from jina.flow import Flow

f = Flow()
```

`Flow()` accepts some arguments, see `jina flow --help` or [our documentation](https://docs.jina.ai) for details. For example, `Flow(log_server=True)` will enable the logs emission to the [dashboard](https://github.com/jina-ai/dashboard). 

When the arguments given to `Flow()` cannot be parsed, they are propagated to all their `Pods` for parsing (if they are accepted, see `jina pod --help` for the list of arguments). For example, 

```python
f = Flow(read_only=True)
```

will override `read_only` attribute of all Pods in `f` to `True`.

### Add Pod into the Flow

To add a Pod to Flow, simply call `.add()`. For example,

```python
f = (Flow().add(name='p1', uses='mypod1.yml')
           .add(name='p2', uses='mypod2.yml', timeout_ready=50000)
           .add(name='p3', uses='mypod3.yml', read_only=True))
``` 

This will create a sequential workflow 
```

gateway -> p1 -> p2 -> p3 -> gateway

``` 

The input of a Pod is the output of the last Pod in sequential order. The gateway is the entry point of the whole Jina network. The `gateway` Pod will be automatically added to every `Flow`, of which the output is the first Pod and the input is the last Pod defined in the Flow.

All accepted arguments follow the command line interface of `Pod`, which can be found in `jina pod --help`. Just remember to replace the dash `-` to underscore `_` in the name of the argument when referring to it in Python.

Besides the file path, in Flow API `uses` can accept other types:

| Type | Example | Remark |
| --- | --- | --- |
| YAML file path | `crafter/my.yml` | |
| Inline YAML | `'!DataURICrafter\nwith: {mimetype: png}'` | don't forget `!` in the beginning |
| The name of an executor [listed here](../all_exec.html) | `TransformerTorchEncoder` | only the executors that have full default values can be directly used |
| Built-in simple executors [listed here](../simple_exec.html) | `_clear` | it always starts with `_` |
 
#### Add a Containerized Pod into the Flow

To run a Pod in a Docker container, simply specify the `image` argument.

```python
f = (Flow().add(name='p1')
           .add(name='p2', image='jinaai/hub.executors.encoders.bidaf:latest')
           .add(name='p3'))
``` 

This will run `p2` in a Docker container equipped with image `jinaai/hub.executors.encoders.bidaf:latest`. More information on using container Pod can be found in [our documentation](https://docs.jina.ai). 

#### Add a Remote Pod into the Flow

To run a Pod remotely, simply specify the `host` and `port_expose` arguments. For example,

```python
f = (Flow().add(name='p1')
           .add(name='p2', host='192.168.0.100', port_expose=53100)
           .add(name='p3'))
```

This will start `p2` remotely on `192.168.0.100`, whereas `p1` and `p3` run locally.

To use remote Pod feature, you need to start a `gateway` on `192.168.0.100` in advance. More information on using remote Pod can be found in [our documentation](https://docs.jina.ai).  


#### Add a Remote Containerized Pod into the Flow

A very useful pattern is to combine the above two features together:

```python

f = (Flow().add(name='p1')
           .add(name='p2', host='192.168.0.100', port_expose=53100,
                image='jinaai/hub.executors.encoders.bidaf:latest')
           .add(name='p3'))
```

This will start `p2` remotely on `192.168.0.100` running a Docker container equipped with image `jinaai/hub.executors.encoders.bidaf:latest`. Of course Docker is required on `192.168.0.100`. More information on using remote Pod can be found in [our documentation](https://docs.jina.ai). 



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


In the last example, the message is returned to the gateway regardless the status `p2`. To wait for multiple parallel steps to finish before continue, you can do:

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

To run a Flow, simply use the `with` keyword:

```python
f = (Flow().add(...)
           .add(...))

with f:
    # the flow is now running

```

Though you can manually call the `start()` method to run the flow, you also need to call the corresponding `close()` method to release the resource. Using `with` saves you the trouble, as the resource is automatically released when running out of the scope. 

#### Test the Connectivity with Dry Run

You can test the whole workflow with `dry_run()`. For example,

```python

with f:
    f.dry_run()

```

This will send a `ControRequest` to all pods following the topology you defined. You can use it to test the connectivity of all pods. 

### Iterate over the Pods in the Flow

You can iterate the pods in a Flow like in a list.

```python
f = (Flow().add(...)
           .add(...))

for p in f.build():
    print(f'{p.name} in: {str(p.head_args.socket_in)} out: {str(p.head_args.socket_out)}')
```

Note `f.build()` will build the underlying network context but not running the pods. It is very useful for debugging.

### Feed Data to the Flow

You can use `.index()`, `.search()` to feed index data and search query to a flow:

```python
with f:
    f.index(input_fn)
```

```python
with f:
    f.search(input_fn, top_k=50, output_fn=print)
```

- `input_fn` is an `Iterator[bytes]`, each of which corresponds to the representation of a Document with bytes.
- `output_fn` is the callback function after each request, take a `Request` protobuf as the only input.

A simple `input_fn` is defined as follows:

```python
def input_fn():
    for _ in range(10):
        yield b's'


# or ...
input_fn = (b's' for _ in range(10))
```

> Please note that the current Flow API does not support using `index()` and `search()` together in the same `with` scope. This is because the workflow of `index()` and `search()` are usually different and you cannot use one workflow for both tasks.

#### Feed Data to the Flow using Other Client

If you don't use Python as a client, or your client and flow are in different instances. You can hold a flow in running state and use a client in another language to connect to it. Simply:

```python
import threading

with f:
    f.block()
```

Please checkout our [hello world in client-server architecture](https://github.com/jina-ai/examples/tree/master/helloworld-in-cs) for a complete example.

**WARNING**: don't use a while loop to do the waiting, it is extremely inefficient:

```python
with f:
    while True: # <- dont do that
        pass # <- dont do that
```

## Use Flow API in YAML

You can also write a Flow in YAML. For example,

```yaml
!Flow
with:
  logserver: true
pods:
  chunk_seg:
    uses: craft/index-craft.yml
    replicas: $REPLICAS
    read_only: true
  doc_idx:
    uses: index/doc.yml
  tf_encode:
    uses: encode/encode.yml
    needs: chunk_seg
    replicas: $REPLICAS
    read_only: true
  chunk_idx:
    uses: index/chunk.yml
    replicas: $SHARDS
    separated_workspace: true
  join_all:
    uses: _merge
    needs: [doc_idx, chunk_idx]
    read_only: true
```

You can use enviroment variables via `$` in YAML. More information on the Flow YAML Schema can be found in [our documentation](https://docs.jina.ai). 

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


More information on the dashboard can be found [here](https://github.com/jina-ai/dashboard).

# Common design patterns

jina is a really flexible AI-powered neural search framework. It is designed to enable any pattern that can be framed as  
a neural search problem.
However, there are basic common patterns that show up when developing search solutions with jina and here is a recopilation of some of them.

- CompoundIndexer (Vector + KV Indexers):

To develop neural search applications, it is useful to use a `CompoundIndexer` in the same `Pod` for both `index` and `query` Flows.
The following `yaml` file shows an example of this pattern.

```yaml
!CompoundIndexer
components:
  - !NumpyIndexer
    with:
      index_filename: vectors.gz
      metric: cosine
    metas:
      name: vecIndexer
  - !BinaryPbIndexer
    with:
      index_filename: values.gz
    metas:
      name: kvIndexer  # a customized name
metas:
  name: complete indexer
```

This type of construction will act as a single `indexer` and will allow to seamlessly `query` this index with the `embedding` vector coming
from any upstream `encoder` and obtain in the response message of the pod the corresponding `binary` information stored in
the key-value index. This lets the `VectorIndexer` be responsible to obtain the most relevant documents by finding similarities
in the `embedding` space while targeting the `key-value` database to extract the meaningful data and fields from those relevant documents.

- Indexers at different depth levels:

- NLP Document chunks (Segment + encode):

- Reference Indexer
