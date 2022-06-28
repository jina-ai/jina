(external-executor)=
# Use external Executors

Normally, we have seen how {class}`~jina.Flow` ties up {class}`~jina.Executor`s together, and how an Executor lives in the context of a Flow.

However, this is not always the case, and sometimes you may want to launch an Executor on its own, and perhaps have the same
Executor be used by different Flows.


````{admonition} Where can external Executors run?
:class: hint
External Executors can run anywhere from the same environment as the Flow, to a Docker container, or even a remote
machine.
````

As the first step in this tutorial, you will learn how to add already running external Executors to your Flow.
After that, you will see how to create and use an external Executor yourself.

## Adding external Executors

If you want to add an external Executor to your Flow, all you really need to know is how to find it.
You need:

- `host`, the host address of the Executor
- `port`, the port on which the Executor receives information

Then, adding the Executor is a simple call to {meth}`~jina.Flow.add`  with the `external` argument set to True. This tells the Flow that
it does not need to start the Executor itself.:

```python
from jina import Flow

exec_host, exec_port = 'localhost', 12345
f = Flow().add(host=exec_host, port=exec_port, external=True)
```

After that, the external Executor will behave just like an internal one. And you can even add the same Executor to multiple
Flows!

````{admonition} Note
:class: hint
If an external Executor needs multiple predecessors, reducing needs to be enabled. So setting disable_reduce=True is not allowed for these cases. 
````

## Starting standalone Executors

The example above assumes that there already is an Executor running, and you just want to access
it from your Flow.


You can, however, also start your own standalone Executors, which can then be accessed from anywhere.
In the following sections we will describe how to run standalone Executors via the Jina command line interface (CLI). For more options to run your Executor, including in Kubernetes and Docker Compose, please read the {ref}`Executor API section <serve-executor-standalone>`.


````{admonition} Advanced deployment options
:class: seealso
This tutorial walks through the basics of spawing a standalone (external) Executor. For more advanced options, refer to the
[CLI](../cli/index.rst) and {ref}`Executor API section <serve-executor-standalone>`
````

## Using Jina Hub

The Jina CLI allows you to spawn executors straight from the Hub.
In this example, we will use `CLIPTextEncoder` to create embeddings for our Documents.

First, we start the Executor from the terminal. All we need to decide is the `port` that will be used by the Executor.
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

And just like that, our Executor is up and running.

Next, let's access it from a Flow and encode some Documents. You can do this from a different machine, as long you know
the first machine's host address, or simply from the same machine in a different process using `localhost`.

So, if you are still working on the same machine, hop over to a new terminal or your code editor of choice, and define
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

```console
"Embed me please!" has been embedded to shape (512,)
```

We obtain embeddings for our Documents, just like we would with a local Executor.

## Using a custom Executor

You can achieve the same while using your own, locally defined Executor. Let's walk through it.

First, we create a file `exec.py`, and in it we define our custom Executor:

```python
from jina import Executor, requests


class MyExecutor(Executor):
    @requests
    def foo(self, docs, **kwargs):
        for doc in docs:
            print(f'Received: "{doc.text}"')
```

Since we can't rely on the Hub this time around, we need to tell Jina how to find the Executor that we just defined.
We do this using a YAML file.

In a new file called `my-exec.yml` we type:

```yaml
!MyExecutor
metas:
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

```console
Received: "Greetings from Flow1"
Received: "Greetings from Flow2"
```
