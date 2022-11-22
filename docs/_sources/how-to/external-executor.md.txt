(external-executor)=
# Include external Executors in a Flow

We've seen how {class}`~jina.Flow` ties {class}`~jina.Executor`s together, and how an Executor lives in the context of a Flow. Sometimes you may want to launch an Executor on its own, and then share it to different Flows. We call this an *external* Executor as its lifecycle is not tied to the Flow.

External Executors can run anywhere, from the same environment as the Flow, to a Docker container, or even a remote
environment, such as {ref}`JCloud <jcloud>`.

```{tip}
To deploy external Executors on JCloud, please follow {ref}`this documentation <external-executors>`.
```

In this tutorial, we'll add already running external Executors to a Flow,
and then create and use an external Executor for ourselves.

## Adding external Executors

To add an external Executor to your Flow, all you need to know is how to find it, namely:

- `host`, the host address of the Executor
- `port`, the port on which the Executor receives information

Adding the Executor is a simple call to {meth}`~jina.Flow.add` with the `external` argument set to True. This tells the Flow 
not to start the Executor itself:

```python
from jina import Flow

exec_host, exec_port = 'localhost', 12345
f = Flow().add(host=exec_host, port=exec_port, external=True)
```

Alternatively, you can pass the entire network address as the `host` parameter:

```python
from jina import Flow

f = Flow().add(host='localhost:12345', external=True)
```

After that, the external Executor behaves just like an internal one. You can even add the same Executor to multiple
Flows.

````{admonition} Distributed replicas
:class: hint

Similarly, you can add multiple replicas of the same Executor
by specifying all the respective hosts and ports:

```python
from jina import Flow

replica_hosts, replica_ports = 'localhost,91.198.174.192', '12345,12346'
f = Flow().add(host=replica_hosts, port=replica_ports, external=True)

# alternative syntax
# f = Flow().add(host='localhost:12345,91.198.174.192:12346', external=True)
```

This connects to `grpc://localhost:12345` and `grpc://91.198.174.192:12346` as two replicas of the same Executor.

````

````{admonition} Reducing
:class: hint
If an external Executor needs multiple predecessors, reducing needs to be enabled. So setting disable_reduce=True is not allowed for these cases. 
````


## Starting shared Executors

The example above assumes there's already an Executor running, and you just want to access
it from your Flow.

You can, however, start your own standalone Executors, which can then be accessed from anywhere.
In the following sections we describe how to run shared Executors via the Jina CLI.
For more options to run your Executor, including in Kubernetes and Docker Compose, please read the {ref}`Executor API section <serve-executor-standalone>`.

Though not part of this how-to, you can also use {ref}`served Executors <serve-executor-standalone>` as external Executors.


````{admonition} Advanced deployment options
:class: seealso
This tutorial walks through the basics of spawing a standalone (external) Executor. For more advanced options, refer to the
[CLI](../cli/index.rst) and {ref}`Executor API section <serve-executor-standalone>`
````

## Using Executor Hub

The Jina CLI lets you spawn Executors straight from Executor Hub.
In this example, we use `CLIPTextEncoder` to create embeddings for our Documents.

First, start the Executor from the terminal. All we need to decide is the `port` that will be used by the Executor.
Here we pick `12345`.

````{tab} Using Docker

```bash
jina executor --uses jinahub+docker://CLIPTextEncoder --port 12345
```

````

````{tab} Without Docker

```bash
jina executor --uses jinahub://CLIPTextEncoder --port 12345
```

````

This might take a few seconds, but in the end you should be greeted with the
following message:

```bash
WorkerRuntime@ 1[L]: Executor CLIPTextEncoder started
```

Just like that, our Executor is up and running.

Next, let's access it from a Flow and encode some Documents. You can do this from a different machine, as long you know
the first machine's host address, or simply from the same machine in a different process using `localhost`.

If you're still working on the same machine, open a new terminal or code editor of choice, and define
the following Flow in a Python file:

```python
from jina import Flow

f = Flow().add(host='localhost', port=12345, external=True)
```

Now we can encode our Documents:

```python
from docarray import Document, DocumentArray

docs = DocumentArray([Document(text='Embed me please!') for _ in range(5)])


def print_embedding(resp):
    doc = resp.docs[0]
    print(f'"{doc.text}" has been embedded to shape {doc.embedding.shape}')


with f:
    f.index(inputs=docs, on_done=print_embedding)
```

```shell
"Embed me please!" has been embedded to shape (512,)
```

We have obtained embeddings for our Documents, just like we would with a local Executor.

## Using a custom Executor

You can achieve the same while using your own, locally defined Executor:

First, create a file `exec.py`, and define a custom Executor:

```python
from jina import Executor, requests


class MyExecutor(Executor):
    @requests
    def foo(self, docs, **kwargs):
        for doc in docs:
            print(f'Received: "{doc.text}"')
```

Since we don't use Executor Hub this time around, we need to tell Jina how to find the Executor that we just defined.
We do this using a YAML file.

Create a new file called `my-exec.yml`:

```yaml
jtype: MyExecutor
py_modules:
  - exec.py
```

This simply points Jina to our file and Executor class.

Now we can run the CLI command again, this time using our custom Executor:

```bash
jina executor --uses my-exec.yml --port 12345
```

Now that your Executor is up and running, we can tap into it just like before, and even use it from two different Flows.

```python
from jina import Flow, Document, DocumentArray

f1 = Flow().add(host='localhost', port=12345, external=True)
f2 = Flow().add(host='localhost', port=12345, external=True)
with f1:
    f1.index(
        inputs=DocumentArray([Document(text='Greetings from Flow1') for _ in range(1)])
    )
    f2.index(
        inputs=DocumentArray([Document(text='Greetings from Flow2') for _ in range(1)])
    )
```

```shell
Received: "Greetings from Flow1"
Received: "Greetings from Flow2"
```
