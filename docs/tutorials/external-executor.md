# External Executors in Flows

An `Executor` does not need to be tied to a `Flow` - or vice versa.
In fact, Executors can be launched on their own, and be added to a Flow after the fact, all while running in the same
environment, inside a Docker container, on a remote machine, or spawned from the Jina Hub.

As the first step in the tutorial, you will learn how to add already running external Executors to your Flow.
After that, you will see how to create and use an external Executor yourself.

## Adding external Executors

If you want to add an external Executor to your Flow, all you really need to know is how to find it.
You need:

- `host`, the host address of the Executor
- `port_in`, the port on which the executor receives information

Then, adding the Executor is a simple call to `Flow.add()`:

```python
from jina import Flow

exec_host, exec_port = 'localhost', 12345
f = Flow().add(host=exec_host, port_in=exec_port, external=True)
```

After that, the external Executor will behave just like an internal one. And you can even add the same Executor to multiple
Flows!

## Starting standalone Executors

The example above assumes that there already is an Executor running, and you just want to access
it from your flow.

You can, however, also start your own standalone Executors, which can then be accessed from anywhere. There are two
ways of doing this: Pulling an Executor from Jina Hub, and using a locally defined Executor. In either case, you will
launch the Executor using the Jina command line interface (CLI).

````{admonition} Hint
:class: hint
This tutorial walks through the basics of spawing a standalone (external) Executor. For more advanced options, refer to the
CLI documentation (**TODO: LINK TO CLI DOCS**)
````

## Using Jina Hub

The Jina CLI allows you to spawn executors straight from the Hub.
In this example, we will use the `CLIPTextEncoder` to create embeddings for our Documents.

First, we start the Executor from the terminal. All we need to decide is the `port` that will be used by the Executor.
Here we pick `12345`.

````{tab} Using Docker

```bash
jina executor --uses jinahub+docker://CLIPTextEncoder --port-in 12345
```

````

````{tab} Without Docker

```bash
jina executor --uses jinahub://CLIPTextEncoder --port-in 12345
```

````

And just like that, our Executor is up and running.

Next, let's access it from a Flow and encode some Documents. You can do this from a different machine, as long you know
the first machine's host address, or simply from the same machine in a different process using `localhost`.

So, if you are still working on the same machine, hop over to a new terminal or your code editor of choice, and define
the following flow in a Python file:

```python
from jina import Flow

f = Flow().add(host='localhost', port_in=12345, external=True)

```

Now we can encode our Documents:

```python
from docarray import Document, DocumentArray

docs = DocumentArray([Document(text='Embed me please!') for _ in range(5)])

def print_embedding(resp):
    doc = resp.docs[0]
    print(f'{doc.text} has been embedded to shape {doc.embedding.shape}')

with f:
    f.index(inputs=docs, on_done=print_embedding)

>>> **TODO run once Jina 3 Executors are available from the hub** 
```

We obtain embeddings for our documents, just like we would with a local Executor.

## Using a custom Executor

You can achieve the same while using your own, locally defined Executor. Let's walk through it.

First, we create a file `exec.py`, and in it we define our custom Executor:

```python
from jina import Executor, requests
from docarray import Document, DocumentArray

class MyExecutor(Executor):
    @requests
    def foo(self, docs, **kwargs):
        docs.texts = ['Hey you, have a wonderful day!' for _ in docs]
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

This simply points jina to our file and Executor class.

Now we can run the CLI command again, this time using our custom Executor:

```bash
jina executor --uses my-exec.yml --port-in 12345
```

Now that your executor is up and running, we can tap into it just like before:

```python
from jina import Flow
from docarray import Document, DocumentArray

def print_text(resp):
    print(resp.docs[0].text)

docs = DocumentArray[Document() for _ in range(5)]

f = Flow().add(host='localhost', port_in=12345, external=True)
with f:
    f.index(inputs=docs, on_done=print_text)

>>> Hey you, have a wonderful day!
```

Again, we obtain modified Documents, just like we would with an interal Executor.

