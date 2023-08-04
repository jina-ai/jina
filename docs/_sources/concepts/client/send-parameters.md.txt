(client-executor-parameters)=
# Send Parameters

The {class}`~jina.Client` can send key-value pairs as parameters to {class}`~jina.Executor`s as shown below:

```{code-block} python
---
emphasize-lines: 15
---

from jina import Client, Executor, Deployment, requests
from docarray import BaseDoc

class MyExecutor(Executor):

    @requests
    def foo(self, parameters, **kwargs):
        print(parameters['hello'])

dep = Deployment(uses=MyExecutor)

with dep:
    client = Client(port=dep.port)
    client.post('/', BaseDoc(), parameters={'hello': 'world'})
```

````{hint} 
:class: note
You can send a parameters-only data request via:

```python
with dep:
    client = Client(port=dep.port)
    client.post('/', parameters={'hello': 'world'})
```

This might be useful to control `Executor` objects during their lifetime.
````

Since Executors {ref}`can use Pydantic models to have strongly typed parameters <executor-api-parameters>`, you can also send parameters as Pydantic models in the client API


(specific-params)=
## Send parameters to specific Executors

You can send parameters to specific Executor by using the `executor__parameter` syntax.
The Executor named `executorname` will receive the parameter `paramname` (without the `executorname__` in the key name) 
and none of the other Executors will receive it.

For instance in the following Flow:

```python
from jina import Flow, Client
from docarray import BaseDoc, DocList

with Flow().add(name='exec1').add(name='exec2') as f:

    client = Client(port=f.port)

    client.post(
        '/index',
        DocList[BaseDoc]([BaseDoc()]),
        parameters={'exec1__parameter_exec1': 'param_exec1', 'exec2__parameter_exec1': 'param_exec2'},
    )
```

The Executor `exec1` will receive `{'parameter_exec1':'param_exec1'}` as parameters, whereas `exec2` will receive `{'parameter_exec1':'param_exec2'}`.

This feature is intended for the case where there are multiple Executors that take the same parameter names, but you want to use different values for each Executor.
This is often the case for Executors from the Hub, since they tend to share a common interface for parameters.

```{admonition} Difference to target_executor

Why do we need this feature if we already have `target_executor`?

On the surface, both of them is about sending information to a partial Flow, i.e. a subset of Executors. However, they work differently under the hood. `target_executor` directly send info to those specified executors, ignoring the topology of the Flow; whereas `executor__parameter`'s request follows the topology of the Flow and only send parameters to the Executor that matches.

Think about roll call and passing notes in a classroom. `target_executor` is like calling a student directly, whereas `executor__parameter` is like asking him/her to pass the notes to the next student one by one while each picks out the note with its own name.
```


