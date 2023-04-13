(flow-cookbook)=
# Flow

```{important}
A Flow is a set of {ref}`Deployments <deployment>`. Be sure to read up on those before diving more deeply into Flows!
```

A {class}`~jina.Flow` orchestrates {class}`~jina.Executor`s into a processing pipeline to accomplish a task. Documents "flow" through the pipeline and are processed by Executors.

You can think of Flow as an interface to configure and launch your {ref}`microservice architecture <architecture-overview>`, while the heavy lifting is done by the {ref}`services <executor-cookbook>` themselves. In particular, each Flow also launches a {ref}`Gateway <gateway>` service, which can expose all other services through an API that you define.

## Why use a Flow?

Once you've learned DocumentArray and Executor, you can split a big task into small independent modules and services.
But you need to chain them together to bring real value and build and serve an application. Flows enable you to do exactly this.

- Flows connect microservices (Executors) to build a service with proper client/server style interface over HTTP, gRPC, or WebSockets.
- Flows let you scale these Executors independently to match your requirements.
- Flows let you easily use other cloud-native orchestrators, such as Kubernetes, to manage your service.

(create-flow)=
## Create

The most trivial {class}`~jina.Flow` is an empty one. It can be defined in Python or from a YAML file:

````{tab} Python
```python
from jina import Flow

f = Flow()
```
````
````{tab} YAML
```yaml
jtype: Flow
```
````

```{important}
All arguments received by {class}`~jina.Flow()` API will be propagated to other entities (Gateway, Executor) with the following exceptions:

- `uses` and `uses_with` won't be passed to Gateway
- `port`, `port_monitoring`, `uses` and `uses_with` won't be passed to Executor
```

```{tip}
An empty Flow contains only {ref}`the Gateway<gateway>`.
```

```{figure} images/zero-flow.svg
:scale: 70%
```

For production, you should define your Flows with YAML. This is because YAML files are independent of the Python logic code and easier to maintain.

## Minimum working example

````{tab} Pythonic style


```python
from jina import Flow, Executor, requests, Document


class MyExecutor(Executor):
    @requests(on='/bar')
    def foo(self, docs, **kwargs):
        print(docs)


f = Flow().add(name='myexec1', uses=MyExecutor)

with f:
    f.post(on='/bar', inputs=Document(), on_done=print)
```


````

````{tab} Flow-as-a-Service style

Server:

```python
from jina import Flow, Executor, requests


class MyExecutor(Executor):
    @requests(on='/bar')
    def foo(self, docs, **kwargs):
        print(docs)


f = Flow(port=12345).add(name='myexec1', uses=MyExecutor)

with f:
    f.block()
```

Client:

```python
from jina import Client, Document

c = Client(port=12345)
c.post(on='/bar', inputs=Document(), on_done=print)
```

````

````{tab} Load from YAML

`my.yml`:
```yaml
jtype: Flow
executors:
  - name: myexec1
    uses: FooExecutor
    py_modules: exec.py
```

`exec.py`:
```python
from jina import Executor, requests, Document, DocumentArray


class FooExecutor(Executor):
    @requests
    def foo(self, docs: DocumentArray, **kwargs):
        docs.append(Document(text='foo was here'))
```

```python
from jina import Flow, Document

f = Flow.load_config('my.yml')

with f:
    try:
        f.post(on='/bar', inputs=Document(), on_done=print)
    except Exception as ex:
        # handle exception
        pass
```

````

```{caution}
The statement `with f:` starts the Flow, and exiting the indented with block stops the Flow, including all Executors defined in it.
Exceptions raised inside the `with f:` block will close the Flow context manager. If you don't want this, use a `try...except` block to surround the statements that could potentially raise an exception.
```

## Start and stop

When a {class}`~jina.Flow` starts, all included Executors (single for a Deployment, multiple for a Flow) will start as well, making it possible to {ref}`reach the service through its API <third-party-client>`.

There are three ways to start an Flow: In Python, from a YAML file, or from the terminal.

- Generally in Python: use Deployment or Flow as a context manager in Python.
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

The statement `with f:` starts the Flow, and exiting the indented `with` block stops the Flow, including all its Executors.

A successful start of a Flow looks like this:

```{figure} images/success-flow.png
:scale: 70%
```

Your addresses and entrypoints can be found in the output. When you enable more features such as monitoring, HTTP gateway, TLS encryption, this display expands to contain more information.

```{admonition} Multiprocessing spawn
:class: warning

Some corner cases require forcing a `spawn` start method for multiprocessing, for example if you encounter "Cannot re-initialize CUDA in forked subprocess". Read {ref}`more in the docs <multiprocessing-spawn>`
```

## Serve

### Serve forever

In most scenarios, a Flow should remain reachable for prolonged periods of time. This can be achieved from Python or the terminal:

````{tab} Python
```python
from jina import Flow

f = Flow()

with f:
    f.block()
```
The `.block()` method blocks the execution of the current thread or process, enabling external clients to access the Flow.
````
````{tab} Terminal
```shell
jina flow --uses flow.yml
```
````

In this case, the Flow can be stopped by interrupting the thread or process. 

### Serve until an event

Alternatively, a `multiprocessing` or `threading` `Event` object can be passed to `.block()`, which stops the Flow once set.

```python
from jina import Flow
import threading


def start_flow(stop_event):
    """start a blocking Flow."""
    f = Flow()

    with f:
        f.block(stop_event=stop_event)


e = threading.Event()  # create new Event

t = threading.Thread(name='Blocked-Flow', target=start_flow, args=(e,))
t.start()  # start Flow in new Thread

# do some stuff

e.set()  # set event and stop (unblock) the Flow
```

### Serve on Google Colab

[Google Colab](https://colab.research.google.com/) provides an easy-to-use Jupyter notebook environment with GPU/TPU support. Flows are fully compatible with Google Colab and you can use it in the following ways:

```{figure} images/jina-on-colab.svg
:align: center
:width: 70%
```

```{button-link} https://colab.research.google.com/github/jina-ai/jina/blob/master/docs/Using_Jina_on_Colab.ipynb
:color: primary
:align: center

{octicon}`link-external` Open the notebook on Google Colab 
```

Please follow the walkthrough and enjoy the free GPU/TPU!


```{tip}
Hosing services on Google Colab is not recommended if your server aims to be long-lived or permanent. It is often used for quick experiments, demonstrations or leveraging its free GPU/TPU. For stable, secure and free hosting of your Flow, check out [JCloud](https://docs.jina.ai/concepts/jcloud/).
```

## Export

A Flow YAML can be exported as a Docker Compose YAML or Kubernetes YAML bundle. 

(docker-compose-export)=
### Docker Compose

````{tab} Python
```python
from jina import Flow

f = Flow().add()
f.to_docker_compose_yaml()
```
````
````{tab} Terminal
```shell
jina export docker-compose flow.yml docker-compose.yml 
```
````

This will generate a single `docker-compose.yml` file.

For advanced utilization of Docker Compose with Jina, refer to {ref}`How to <docker-compose>` 

(kubernetes-export)=
### Kubernetes

````{tab} Python
```python
from jina import Flow

f = Flow().add()
f.to_kubernetes_yaml('flow_k8s_configuration')
```
````
````{tab} Terminal
```shell
jina export kubernetes flow.yml ./my-k8s 
```
````

The generated folder can be used directly with `kubectl` to deploy the Flow to an existing Kubernetes cluster.

For advanced utilisation of Kubernetes with Jina please refer to {ref}`How to <kubernetes>` 

```{tip}
Based on your local Jina version, Executor Hub may rebuild the Docker image during the YAML generation process.
If you do not wish to rebuild the image, set the environment variable `JINA_HUB_NO_IMAGE_REBUILD`.
```

```{tip}
If an Executor requires volumes to be mapped to persist data, Jina will create a StatefulSet for that Executor instead of a Deployment.
You can control the access mode, storage class name and capacity of the attached Persistent Volume Claim by using {ref}`Jina environment variables <jina-env-vars>`  
`JINA_K8S_ACCESS_MODES`, `JINA_K8S_STORAGE_CLASS_NAME` and `JINA_K8S_STORAGE_CAPACITY`. Only the first volume will be considered to be mounted.
```

```{admonition} See also
:class: seealso
For more in-depth guides on Flow deployment, check our how-tos for {ref}`Docker compose <docker-compose>` and {ref}`Kubernetes <kubernetes>`.
```


## Add Executors

```{important}
This section is for Flow-specific considerations when working with Executors. Check more information on {ref}`working with Executors <add-executors>`.
```

A {class}`~jina.Flow` orchestrates its {class}`~jina.Executor`s as a graph and sends requests to all Executors in the order specified by {meth}`~jina.Flow.add` or listed in {ref}`a YAML file<flow-yaml-spec>`. 

When you start a Flow, Executors always run in **separate processes**. Multiple Executors run in **different processes**. Multiprocessing is the lowest level of separation when you run a Flow locally. When running a Flow on Kubernetes, Docker Swarm, {ref}`jcloud`, different Executors run in different containers, pods or instances.   

Executors can be added into a Flow with {meth}`~jina.Flow.add`.  

```python
from jina import Flow

f = Flow().add()
```

This adds an "empty" Executor called {class}`~jina.serve.executors.BaseExecutor` to the Flow. This Executor (without any parameters) performs no actions.

```{figure} images/no-op-flow.svg
:scale: 70%
```

To more easily identify an Executor, you can change its name by passing the `name` parameter:

```python
from jina import Flow

f = Flow().add(name='myVeryFirstExecutor').add(name='secondIsBest')
```


```{figure} images/named-flow.svg
:scale: 70%
```

You can also define the above Flow in YAML:

```yaml
jtype: Flow
executors:
  - name: myVeryFirstExecutor
  - name: secondIsBest
```

Save it as `flow.yml` and run it: 

```bash
jina flow --uses flow.yml
```

More Flow YAML specifications can be found in {ref}`Flow YAML Specification<flow-yaml-spec>`.

### How Executors process DocumentArrays in a Flow

Let's understand how Executors process DocumentArray's inside a Flow, and how changes are chained and applied, affecting downstream Executors in the Flow.

```python 
from jina import Executor, requests, Flow, DocumentArray, Document


class PrintDocuments(Executor):
    @requests
    def foo(self, docs, **kwargs):
        for doc in docs:
            print(f' PrintExecutor: received document with text: "{doc.text}"')


class ProcessDocuments(Executor):
    @requests(on='/change_in_place')
    def in_place(self, docs, **kwargs):
        # This Executor only works on `docs` and doesn't consider any other arguments
        for doc in docs:
            print(f' ProcessDocuments: received document with text "{doc.text}"')
            doc.text = 'I changed the executor in place'

    @requests(on='/return_different_docarray')
    def ret_docs(self, docs, **kwargs):
        # This executor only works on `docs` and doesn't consider any other arguments
        ret = DocumentArray()
        for doc in docs:
            print(f' ProcessDocuments: received document with text: "{doc.text}"')
            ret.append(Document(text='I returned a different Document'))
        return ret


f = Flow().add(uses=ProcessDocuments).add(uses=PrintDocuments)

with f:
    f.post(on='/change_in_place', inputs=DocumentArray(Document(text='request1')))
    f.post(
        on='/return_different_docarray', inputs=DocumentArray(Document(text='request2'))
    )
```


```shell
────────────────────────── 🎉 Flow is ready to serve! ──────────────────────────
╭────────────── 🔗 Endpoint ───────────────╮
│  ⛓     Protocol                    GRPC  │
│  🏠       Local           0.0.0.0:58746  │
│  🔒     Private     192.168.1.187:58746  │
│  🌍      Public    212.231.186.65:58746  │
╰──────────────────────────────────────────╯

 ProcessDocuments: received document with text "request1"
 PrintExecutor: received document with text: "I changed the executor in place"
 ProcessDocuments: received document with text: "request2"
 PrintExecutor: received document with text: "I returned a different Document"
```

### Define topologies over Executors

{class}`~jina.Flow`s are not restricted to sequential execution. Internally they are modeled as graphs, so they can represent any complex, non-cyclic topology.

A typical use case for such a Flow is a topology with a common pre-processing part, but different indexers separating embeddings and data.

To define a custom topology you can use the `needs` keyword when adding an {class}`~jina.Executor`. By default, a Flow assumes that every Executor needs the previously added Executor.

```python
from jina import Executor, Flow, requests, Document, DocumentArray


class FooExecutor(Executor):
    @requests
    async def foo(self, docs: DocumentArray, **kwargs):
        docs.append(Document(text=f'foo was here and got {len(docs)} document'))


class BarExecutor(Executor):
    @requests
    async def bar(self, docs: DocumentArray, **kwargs):
        docs.append(Document(text=f'bar was here and got {len(docs)} document'))


class BazExecutor(Executor):
    @requests
    async def baz(self, docs: DocumentArray, **kwargs):
        docs.append(Document(text=f'baz was here and got {len(docs)} document'))


f = (
    Flow()
    .add(uses=FooExecutor, name='fooExecutor')
    .add(uses=BarExecutor, name='barExecutor', needs='fooExecutor')
    .add(uses=BazExecutor, name='bazExecutor', needs='fooExecutor')
    .add(needs=['barExecutor', 'bazExecutor'])
)
```

```{figure} images/needs-flow.svg
:width: 70%
:align: center
Complex Flow where one Executor requires two Executors to process Documents beforehand
```

When sending message to this Flow,

```python
with f:
    print(f.post('/').texts)
```

This gives the output:

```text
['foo was here and got 0 document', 'bar was here and got 1 document', 'baz was here and got 1 document']
```

Both `BarExecutor` and `BazExecutor` only received a single `Document` from `FooExecutor` because they are run in parallel. The last Executor `executor3` receives both DocumentArrays and merges them automatically.
This automated merging can be disabled with `no_reduce=True`. This is useful for providing custom merge logic in a separate Executor. In this case the last `.add()` call would look like `.add(needs=['barExecutor', 'bazExecutor'], uses=CustomMergeExecutor, no_reduce=True)`. This feature requires Jina >= 3.0.2.

(floating-executors)=
### Floating Executors

Some Executors in your Flow can be used for asynchronous background tasks that take time and don't generate a required output. For instance,
logging specific information in external services, storing partial results, etc.

You can unblock your Flow from such tasks by using *floating Executors*.

Normally, all Executors form a pipeline that handles and transforms a given request until it is finally returned to the Client.

However, floating Executors do not feed their outputs back into the pipeline. Therefore, the Executor's output does not affect the response for the Client, and the response can be returned without waiting for the floating Executor to complete its task.
 
Those Executors are marked with the `floating` keyword when added to a `Flow`:

```python
import time
from jina import Flow, Executor, requests, DocumentArray


class FastChangingExecutor(Executor):
    @requests()
    def foo(self, docs, **kwargs):
        for doc in docs:
            doc.text = 'Hello World'


class SlowChangingExecutor(Executor):
    @requests()
    def foo(self, docs, **kwargs):
        time.sleep(2)
        print(f' Received {docs.texts}')
        for doc in docs:
            doc.text = 'Change the document but will not affect response'


f = (
    Flow()
    .add(name='executor0', uses=FastChangingExecutor)
    .add(
        name='floating_executor',
        uses=SlowChangingExecutor,
        needs=['gateway'],
        floating=True,
    )
)
with f:
    f.post(on='/endpoint', inputs=DocumentArray.empty(1))  # we need to send a first
    start_time = time.time()
    response = f.post(on='/endpoint', inputs=DocumentArray.empty(2))
    end_time = time.time()
    print(f' Response time took {end_time - start_time}s')
    print(f' {response.texts}')
```

```text
 Response time took 0.011997222900390625s
 ['Hello World', 'Hello World']
 Received ['Hello World', 'Hello World']
```

In this example the response is returned without waiting for the floating Executor to complete. However, the Flow is not closed until
the floating Executor has handled the request.

You can plot the Flow and see the Executor is floating disconnected from the **Gateway**.

```{figure} images/flow_floating.svg
:width: 70%

```
A floating Executor can *never* come before a non-floating Executor in your Flow's {ref}`topology <flow-complex-topologies>`.

This leads to the following behaviors:

- **Implicit reordering**: When you add a non-floating Executor after a floating Executor without specifying its `needs` parameter, the non-floating Executor is chained after the previous non-floating one.
```python
from jina import Flow

f = Flow().add().add(name='middle', floating=True).add()
f.plot()
```

```{figure} images/flow_middle_1.svg
:width: 70%

```

- **Chaining floating Executors**: To chain more than one floating Executor, you need to add all of them with the `floating` flag, and explicitly specify the `needs` argument.

```python
from jina import Flow

f = Flow().add().add(name='middle', floating=True).add(needs=['middle'], floating=True)
f.plot()
```

```{figure} images/flow_chain_floating.svg
:width: 70%

```

- **Overriding the `floating` flag**: If you add a floating Executor as part of `needs` parameter of a non-floating Executor, then the floating Executor is no longer considered floating.

```python
from jina import Flow

f = Flow().add().add(name='middle', floating=True).add(needs=['middle'])
f.plot()
```

```{figure} images/flow_cancel_floating.svg
:width: 70%
```

(conditioning)=
### Add Conditioning

Sometimes you may not want all Documents to be processed by all Executors. For example when you process text and image Documents you want to forward them to different Executors depending on their data type. 

You can set conditioning for every {class}`~jina.Executor` in the Flow. Documents that don't meet the condition will be removed before reaching that Executor. This allows you to build a selection control in the Flow.

#### Define conditions

To add a condition to an Executor, pass it to the `when` parameter of {meth}`~jina.Flow.add` method of the Flow. This then defines *when* a Document is processed by the Executor:

You can use the [DocArray query language](https://docarray.jina.ai/fundamentals/documentarray/find/#query-by-conditions) to specify a filter condition for each Executor.

```python
from jina import Flow

f = Flow().add(when={'tags__key': {'$eq': 5}})
```

Then only Documents that satisfy the `when` condition will reach the associated Executor. Any Documents that don't satisfy that condition won't reach the Executor.

If you are trying to separate Documents according to the data modality they hold, you need to choose a condition accordingly.

````{admonition} See Also
:class: seealso

In addition to `$exists` you can use a number of other operators to define your filter: `$eq`, `$gte`, `$lte`, `$size`, `$and`, `$or` and many more. For details, consult this [DocArray documentation page](https://docarray.jina.ai/fundamentals/documentarray/find/#query-by-conditions).
````

```python
# define filter conditions
text_condition = {'text': {'$exists': True}}
tensor_condition = {'tensor': {'$exists': True}}
```

These conditions specify that only Documents that hold data of a specific modality can pass the filter.

````{tab} Python
```{code-block} python
---
emphasize-lines: 3, 8
---
from jina import Flow, DocumentArray, Document

f = Flow().add().add(when={'tags__key': {'$eq': 5}})  # Create the empty Flow, add condition

with f:  # Using it as a Context Manager starts the Flow
    ret = f.post(
        on='/search',
        inputs=DocumentArray([Document(tags={'key': 5}), Document(tags={'key': 4})]),
    )

print(
    ret[:, 'tags']
)  # only the Document fulfilling the condition is processed and therefore returned.
```

```shell
[{'key': 5.0}]
```

````

````{tab} YAML

```yaml
jtype: Flow
executors:
  - name: executor
    when:
        tags__key:
            $eq: 5
```

```{code-block} python
---
emphasize-lines: 9
---
from docarray import DocumentArray, Document
from jina import Flow

f = Flow.load_config('flow.yml')  # Load the Flow definition from Yaml file

with f:  # Using it as a Context Manager starts the Flow
    ret = f.post(
        on='/search',
        inputs=DocumentArray([Document(tags={'key': 5}), Document(tags={'key': 4})]),
    )

print(
    ret[:, 'tags']
)  # only the Document fulfilling the condition is processed and therefore returned.
```

```shell
[{'key': 5.0}]
```
````

Note that if a Document does not satisfy the `when` condition of a filter, the filter removes the Document *for that entire branch of the Flow*.
This means that every Executor located behind a filter is affected by this, not just the specific Executor that defines the condition.
As with a real-life filter, once something fails to pass through it, it no longer continues down the pipeline.

Naturally, parallel branches in a Flow do not affect each other. So if a Document gets filtered out in only one branch, it can
still be used in the other branch, and also after the branches are re-joined:

````{tab} Parallel Executors

```{code-block} python
---
emphasize-lines: 7, 8
---

from jina import Flow, DocumentArray, Document

f = (
    Flow()
    .add(name='first')
    .add(when={'tags__key': {'$eq': 5}}, needs='first', name='exec1')
    .add(when={'tags__key': {'$eq': 4}}, needs='first', name='exec2')
    .needs_all(name='join')
)
```

```{figure} images/conditional-flow.svg
:width: 70%
:align: center
```

```python
with f:
    ret = f.post(
        on='/search',
        inputs=DocumentArray([Document(tags={'key': 5}), Document(tags={'key': 4})]),
    )

print(ret[:, 'tags'])  # Each Document satisfies one parallel branch/filter
```

```shell
[{'key': 5.0}, {'key': 4.0}]
```

````

````{tab} Sequential Executors
```{code-block} python
---
emphasize-lines: 7, 8
---

from jina import Flow, DocumentArray, Document

f = (
    Flow()
    .add(name='first')
    .add(when={'tags__key': {'$eq': 5}}, name='exec1', needs='first')
    .add(when={'tags__key': {'$eq': 4}}, needs='exec1', name='exec2')
)
```

```{figure} images/sequential-flow.svg
:width: 70%

```


```python
with f:
    ret = f.post(
        on='/search',
        inputs=DocumentArray([Document(tags={'key': 5}), Document(tags={'key': 4})]),
    )

print(ret[:, 'tags'])  # No Document satisfies both sequential filters
```

```shell
[]
```
````

This feature is useful to prevent some specialized Executors from processing certain Documents.
It can also be used to build *switch-like nodes*, where some Documents pass through one branch of the Flow,
while other Documents pass through a different parallel branch.

Note that whenever a Document does not satisfy the condition of an Executor, it is not even sent to that Executor.
Instead, only a tailored Request without any payload is transferred.
This means that you can not only use this feature to build complex logic, but also to minimize your networking overhead.

#### Filtering outside the Flow

You can use conditions directly on the data, outside the Flow:

```python
da = ...  # type: docarray.DocumentArray
filtered_text_data = da.find(text_condition)
filtered_image_data = da.find(tensor_condition)

print(filtered_text_data.texts)  # print text
print('---')
print(filtered_image_data.tensors)
```
```shell
['hey there!', 'hey there!']
---
[[[0.50535537 0.50538128]
  [0.40446746 0.34972967]]

 [[0.04222604 0.70102327]
  [0.12079661 0.65313938]]]
```

Each filter selects Documents that contain the desired data fields.
That's exactly what you want for your filter!

````{admonition} See Also
:class: seealso

For a hands-on example of leveraging filter conditions, see {ref}`this how-to <flow-filter>`.
````

To define a filter condition, use [DocArray's rich query language](https://docarray.jina.ai/fundamentals/documentarray/find/#query-by-conditions).

### Merging upstream DocumentArrays

Often when you're building a Flow, you want an Executor to receive DocumentArrays from multiple upstream Executors. 

```{figure} images/flow-merge-executor.svg
:width: 70%
:align: center
```

For this you can use the `docs_matrix` or `docs_map` parameters (part of Executor endpoints signature). These Flow-specific arguments that can be used alongside an Executor's {ref}`default arguments <endpoint-arguments>`:

```{code-block} python
---
emphasize-lines: 11, 12
---
from typing import Dict, Union, List, Optional
from jina import Executor, requests, DocumentArray


class MergeExec(Executor):
    @requests
    async def foo(
        self,
        docs: DocumentArray,
        parameters: Dict,
        docs_matrix: Optional[List[DocumentArray]],
        docs_map: Optional[Dict[str, DocumentArray]],
    ) -> Union[DocumentArray, Dict, None]:
        pass
```

- Use `docs_matrix` to receive a List of all incoming DocumentArrays from upstream Executors:

```python
[
    DocumentArray(...),  # from Executor1
    DocumentArray(...),  # from Executor2
    DocumentArray(...),  # from Executor3
]
```

- Use `docs_map` to receive a Dict, where each item's key is the name of an upstream Executor and the value is the DocumentArray coming from that Executor:

```python
{
    'Executor1': DocumentArray(...),
    'Executor2': DocumentArray(...),
    'Executor3': DocumentArray(...),
}
```

(no-reduce)=
#### Reducing multiple DocumentArrays to one DocumentArray

The `no_reduce` argument determines whether DocumentArrays are reduced into one when being received:

- To reduce all incoming DocumentArrays into **one single DocumentArray**, do not set `no_reduce` or set it to `False`. The `docs_map` and `docs_matrix` will be `None`.
- To receive **a list all incoming DocumentArrays** set `no_reduce` to `True`. The Executor will receive the DocumentArrays independently under `docs_matrix` and `docs_map`.

```python
from jina import Flow, Executor, requests, Document, DocumentArray


class Exec1(Executor):
    @requests
    def foo(self, docs, **kwargs):
        for doc in docs:
            doc.text = 'Exec1'


class Exec2(Executor):
    @requests
    def foo(self, docs, **kwargs):
        for doc in docs:
            doc.text = 'Exec2'


class MergeExec(Executor):
    @requests
    def foo(self, docs_matrix, **kwargs):
        documents_to_return = DocumentArray()
        for doc1, doc2 in zip(*docs_matrix):
            print(
                f'MergeExec processing pairs of Documents "{doc1.text}" and "{doc2.text}"'
            )
            documents_to_return.append(
                Document(text=f'Document merging from "{doc1.text}" and "{doc2.text}"')
            )
        return documents_to_return


f = (
    Flow()
    .add(uses=Exec1, name='exec1')
    .add(uses=Exec2, name='exec2')
    .add(uses=MergeExec, needs=['exec1', 'exec2'], no_reduce=True)
)

with f:
    returned_docs = f.post(on='/', inputs=Document())

print(f'Resulting documents {returned_docs[0].text}')
```


```shell
────────────────────────── 🎉 Flow is ready to serve! ──────────────────────────
╭────────────── 🔗 Endpoint ───────────────╮
│  ⛓     Protocol                    GRPC │
│  🏠       Local           0.0.0.0:55761  │
│  🔒     Private     192.168.1.187:55761  │
│  🌍      Public    212.231.186.65:55761  │
╰──────────────────────────────────────────╯

MergeExec processing pairs of Documents "Exec1" and "Exec2"
Resulting documents Document merging from "Exec1" and "Exec2"
```

## Visualize

A {class}`~jina.Flow` has a built-in `.plot()` function which can be used to visualize the `Flow`:
```python
from jina import Flow

f = Flow().add().add()
f.plot('flow.svg')
```

```{figure} images/flow.svg
:width: 70%

```

```python
from jina import Flow

f = Flow().add(name='e1').add(needs='e1').add(needs='e1')
f.plot('flow-2.svg')
```

```{figure} images/flow-2.svg
:width: 70%
```

You can also do it in the terminal:

```bash
jina export flowchart flow.yml flow.svg 
```

You can also visualize a remote Flow by passing the URL to `jina export flowchart`.

(logging-configuration)=
## Logging

The default {class}`jina.logging.logger.JinaLogger` uses rich console logging that writes to the system console. The `log_config` argument can be used to pass in a string of the pre-configured logging configuration names in Jina or the absolute YAML file path of the custom logging configuration. For most cases, the default logging configuration sufficiently covers local, Docker and Kubernetes environments.

Custom logging handlers can be configured by following the Python official [Logging Cookbook](https://docs.python.org/3/howto/logging-cookbook.html#logging-cookbook) examples. An example custom logging configuration file defined in a YAML file `logging.json.yml` is:

```yaml
handlers:
  - StreamHandler
level: INFO
configs:
  StreamHandler:
    format: '%(asctime)s:{name:>15}@%(process)2d[%(levelname).1s]:%(message)s'
    formatter: JsonFormatter
```

The logging configuration can be used as follows:

````{tab} Python
```python
from jina import Flow

f = Flow(log_config='./logging.json.yml')
```
````
````{tab} YAML
```yaml
jtype: Flow
with:
    log_config: './logging.json.yml'
```
````

(logging-override)=
### Custom logging configuration

The default {ref}`logging <logging-configuration>` or custom logging configuration at the Flow level will be propagated to the `Gateway` and `Executor` entities. If that is not desired, every `Gateway` or `Executor` entity can be provided with its own custom logging configuration. 

You can configure two different `Executors` as in the below example:

```python
from jina import Flow

f = (
    Flow().add(log_config='./logging.json.yml').add(log_config='./logging.file.yml')
)  # Create a Flow with two Executors
```

`logging.file.yml` is another YAML file with a custom `FileHandler` configuration.

````{hint}
Refer to {ref}`Gateway logging configuration <gateway-logging-configuration>` section for configuring the `Gateway` logging.
````

````{caution}
When exporting the Flow to Kubernetes, the log_config file path must refer to the absolute local path of each container. The custom logging
file must be included during the containerization process. If the availability of the file is unknown then its best to rely on the default
configuration. This restriction also applies to dockerized `Executors`. When running a dockerized Executor locally, the logging configuration
file can be mounted using {ref}`volumes <mount-local-volumes>`.
````

## Methods

The most important methods of the `Flow` object are the following:

| Method                                                       | Description                                                                                                                                                                                                                                                                          |
|--------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| {meth}`~jina.Flow.add`                                       | Adds an Executor to the Flow                                                                                                                                                                                                                                                         |
| {meth}`~jina.Flow.start()`                                   | Starts the Flow. This will start all its Executors and check if they are ready to be used.                                                                                                                                                                                           |
| {meth}`~jina.Flow.close()`                                   | Stops and closes the Flow. This will stop and shutdown all its Executors.                                                                                                                                                                                                            |
| `with` context manager                                       | Uses the Flow as a context manager. It will automatically start and stop your Flow.                                                                                                                                                                                                   |                                                                |
| {meth}`~jina.Flow.plot()`                                    | Visualizes the Flow. Helpful for building complex pipelines.                                                                                                                                                                                                                         |
| {meth}`~jina.clients.mixin.PostMixin.post()`                 | Sends requests to the Flow API.                                                                                                                                                                                                                                                      |
| {meth}`~jina.Flow.block()`                                   | Blocks execution until the program is terminated. This is useful to keep the Flow alive so it can be used from other places (clients, etc).                                                                                                                                          |
| {meth}`~jina.Flow.to_docker_compose_yaml()`                  | Generates a Docker-Compose file listing all Executors as services.                                                                                                                                                                                                                                                |
| {meth}`~jina.Flow.to_kubernetes_yaml()`                      | Generates Kubernetes configuration files in `<output_directory>`. Based on your local Jina version, Executor Hub may rebuild the Docker image during the YAML generation process. If you do not wish to rebuild the image, set the environment variable `JINA_HUB_NO_IMAGE_REBUILD`.                                                                                                                                   |
| {meth}`~jina.clients.mixin.HealthCheckMixin.is_flow_ready()` | Check if the Flow is ready to process requests. Returns a boolean indicating the readiness.                                                                                                                                                                                                                                                                                                                                 |

