# Flow IO

`.post()` is the core method for sending data to a `Flow` object, it provides multiple callbacks for fetching results from the Flow.

```python
from jina import Flow

f = Flow().add(...)

with f:
    f.post(...)
```

```{caution}

`.post()` must be called *inside* the `with` context.
```

````{admonition} Hint
:class: hint
You can also use CRUD methods (`index`, `search`, `update`, `delete`) which are just sugary syntax of `post`
with `on='/index'`
, `on='/search'`, etc. Precisely, they are defined as:

```python
index = partialmethod(post, '/index')
search = partialmethod(post, '/search')
update = partialmethod(post, '/update')
delete = partialmethod(post, '/delete')
```
````

## Request data

Request data can be a single `Document` object, an iterator of `Document`, a generator of `Document`, a `DocumentArray`
object, and None.

For example:

```python
from jina import Flow, DocumentArray, Document, DocumentArrayMemmap

d1 = Document(content='hello')
d2 = Document(content='world')


def doc_gen():
    for j in range(10):
        yield Document(content=f'hello {j}')


with Flow() as f:
    f.post('/', d1)  # Single document

    f.post('/', [d1, d2])  # a list of Document

    f.post('/', doc_gen)  # Document generator

    f.post('/', DocumentArray([d1, d2]))  # DocumentArray

    f.post('/', DocumentArrayMemmap('./my-mmap'))  # DocumentArray

    f.post('/')  # empty
```

`Document` module provides some methods that lets you build `Document` generator, e.g. [`from_csv`
, `from_files`, `from_ndarray`, `from_ndjson`](Document.md#construct-from-json-csv-ndarray-and-files). They can be used
in conjunction with `.post()`, e.g.

```{code-block} python
---
emphasize-lines: 7
---
from jina import Flow
from jina.types.document.generators import from_csv

f = Flow()

with f, open('my.csv') as fp:
    f.index(from_csv(fp, field_resolver={'question': 'text'}))
```

## Request parameters

To send parameters to the Executor, use

```{code-block} python
---
emphasize-lines: 14
---
from jina import Document, Executor, Flow, requests


class MyExecutor(Executor):

    @requests
    def foo(self, parameters, **kwargs):
        print(parameters['hello'])


f = Flow().add(uses=MyExecutor)

with f:
    f.post('/', Document(), parameters={'hello': 'world'})
```

````{admonition} Note
:class: note
You can send a parameters-only data request via:

```python
with f:
    f.post('/', parameters={'hello': 'world'})
```

This is useful to control `Executor` objects in the runtime.
````

If user wants different executors to have different values of the same parameters, one can specify specific parameters for the specific `executor` by adding a dictionary inside parameters
with the `executor` name as `key`. Jina will then take all these specific parameters and copy to the root of the
parameters dictionary before calling the executor `method`.

```{code-block} python
---
emphasize-lines: 24
---
from typing import Optional
from jina import Executor, requests, DocumentArray, Flow


class MyExecutor(Executor):
    def __init__(self, default_param: int = 1, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.default_param = default_param

    @requests
    def foo(self, docs: Optional[DocumentArray], parameters: dict, **kwargs):
        param = parameters.get('param', self.default_param)
        # param may be overriden for this specific request.
        # The first instance will receive 10, and the second one will receive 5
        if self.metas.name == 'my-executor-1':
            assert param == 10
        elif self.metas.name == 'my-executor-2':
            assert param == 5


with (Flow().
        add(uses={'jtype': 'MyExecutor', 'metas': {'name': 'my-executor-1'}}).
        add(uses={'jtype': 'MyExecutor', 'metas': {'name': 'my-executor-2'}})) as f:
    f.post(on='/endpoint', inputs=DocumentArray([]), parameters={'param': 5, 'my-executor-1': {'param': 10}})
```

Note, as `parameters` does not have a fixed schema, it is declared with type `google.protobuf.Struct` in the `RequestProto`
protobuf declaration. However, `google.protobuf.Struct` follows the JSON specification and does not
differentiate `int` from `float`. **So, data of type `int` in `parameters` will be casted to `float` when request is
sent to executor.**

As a result, users need be explicit and cast the data to the expected type as follows.

````{tab} ✅ Do
```{code-block} python
---
emphasize-lines: 6, 7
---

class MyExecutor(Executor):
    animals = ['cat', 'dog', 'turtle']
    @request
    def foo(self, docs, parameters: dict, **kwargs):
        # need to cast to int since list indices must be integers not float
        index = int(parameters.get('index', 0))
        assert self.animals[index] == 'dog'

with Flow().add(uses=MyExecutor) as f:
    f.post(on='/endpoint', inputs=DocumentArray([]), parameters={'index': 1})
```
````

````{tab} 😔 Don't
```{code-block} python
---
emphasize-lines: 6, 7
---

class MyIndexer(Executor):
    animals = ['cat', 'dog', 'turtle']
    @request
    def foo(self, docs, parameters: dict, **kwargs):
          # ERROR: list indices must be integer not float
          index = parameters.get('index', 0)
          assert self.animals[index] == 'dog'

with Flow().add(uses=MyExecutor) as f:
    f.post(on='/endpoint',
    inputs=DocumentArray([]), parameters={'index': 1})
```
````

## Size of request

You can control how many `Documents` in each request by `request_size`. Say your `inputs` has length of 100, whereas
you `request_size` is set to `10`. Then `f.post` will send ten requests and return 10 responses:

```python
from jina import Flow, Document

f = Flow()

with f:
    f.post('/', (Document() for _ in range(100)), request_size=10)
```

```console
        gateway@137489[L]:ready and listening
           Flow@137489[I]:🎉 Flow is ready to use!
	🔗 Protocol: 		GRPC
	🏠 Local access:	0.0.0.0:44249
	🔒 Private network:	192.168.1.100:44249
	🌐 Public address:	197.28.126.36:44249

```

To see that more clearly, you can turn on the progress-bar by `show_progress`.

```python
with f:
    f.post('/', (Document() for _ in range(100)), request_size=10, show_progress=True)
```

```console
        gateway@137489[L]:ready and listening
           Flow@137489[I]:🎉 Flow is ready to use!
	🔗 Protocol: 		GRPC
	🏠 Local access:	0.0.0.0:59109
	🔒 Private network:	192.168.1.100:59109
	🌐 Public address:	197.28.126.36:59109
⏳   |██████████          | ⏱️ 0.0s 🐎 429.0 RPS✅ 10 requests done in ⏱ 0 seconds 🐎 425.1 RPS

```

## Limiting outstanding requests

You can control the number of requests fetched at a time from the Client generator into the Executor using `prefetch` argument, e.g.- Setting `prefetch=2` would make sure only 2 requests reach the Executors at a time, hence controlling the overload. By default, prefetch is disabled (set to 0). In cases where an Executor is a slow worker, you can assign a higher value to prefetch.

```{code-block} python
---
emphasize-lines: 8, 10
---

def requests_generator():
    while True:
        yield Document(...)

class MyExecutor(Executor):
    @request
    def foo(self, **kwargs):
        slow_operation()

# Makes sure only 2 requests reach the Executor at a time.
with Flow(prefetch=2).add(uses=MyExecutor) as f:
    f.post(on='/', inputs=requests_generator)
```

```{danger}
When working with very slow executors and a big amount of data, you must set `prefetch` to some small number to prevent OOM. If you are unsure, always set `prefetch=1`.
```
 

## Response result

Once a request is returned, callback functions are fired. Jina Flow implements a Promise-like interface. You can add
callback functions `on_done`, `on_error`, `on_always` to hook different events.

In Jina, callback function's first argument is a `jina.types.request.Response` object. Hence, you can annotate the
callback function via:

```python
from jina.types.request import Response


def my_callback(rep: Response):
    ...
```

`Response` object has many attributes, probably the most popular one is `Response.docs`, where you can access
all `Document` as an `DocumentArray`.

In the example below, our Flow passes the message then prints the result when successful. If something goes wrong, it
beeps. Finally, the result is written to `output.txt`.

```python
from jina import Document, Flow


def beep(*args):
    # make a beep sound
    import sys
    sys.stdout.write('\a')


with Flow().add() as f, open('output.txt', 'w') as fp:
    f.post('/',
           Document(),
           on_done=print,
           on_error=beep,
           on_always=lambda x: x.docs.save(fp))
```

### Get all responses

In some scenarios (e.g. testing), you may want to get the all responses in bulk and then process them; instead of
processing responses on the fly. To do that, you can turn on `return_results`:

```python
from jina import Flow, Document

f = Flow()

with f:
    all_responses = f.post('/', (Document() for _ in range(100)), request_size=10, return_results=True)
    print(all_responses)
```

```console
        gateway@137489[L]:ready and listening
           Flow@137489[I]:🎉 Flow is ready to use!
	🔗 Protocol: 		GRPC
	🏠 Local access:	0.0.0.0:59275
	🔒 Private network:	192.168.1.100:59275
	🌐 Public address:	197.28.126.36:59275
[<jina.types.request.Response request_id=116880a6-acd7-474a-8ec6-71bab47041cd data={'docs': [{'id': 'e42c22dc-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c2552-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c26e2-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c2836-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c298a-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c2ad4-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c2c1e-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c2d5e-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c2ea8-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c2ff2-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}]} header={'exec_endpoint': '/'} routes=[{'pod': 'gateway', 'pod_id': 'c5a1293e-80b3-4b40-84d1-b9742611b92e', 'start_time': '2021-06-23T06:04:37.896226Z', 'end_time': '2021-06-23T06:04:37.897433Z'}, {'pod': 'gateway', 'pod_id': '6e3b1625-531d-4ec2-a8eb-43f2fb0fe7ee', 'start_time': '2021-06-23T06:04:37.897424Z'}] status={} at 5673238672>,
 <jina.types.request.Response request_id=37040d37-6835-443e-8741-b2f762ae95cc data={'docs': [{'id': 'e42c806a-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c8a10-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c8e70-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c9276-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c9668-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42ca748-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42ca996-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42caaf4-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42cb40e-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42cb594-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}]} header={'exec_endpoint': '/'} routes=[{'pod': 'gateway', 'pod_id': 'c5a1293e-80b3-4b40-84d1-b9742611b92e', 'start_time': '2021-06-23T06:04:37.898454Z', 'end_time': '2021-06-23T06:04:37.899392Z'}, {'pod': 'gateway', 'pod_id': '6e3b1625-531d-4ec2-a8eb-43f2fb0fe7ee', 'start_time': '2021-06-23T06:04:37.899384Z'}] status={} at 5678885008>,
 <jina.types.request.Response request_id=54eddb8b-8691-446f-98bc-1d492f5bedb0 data={'docs': [{'id': 'e42cfc16-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42cfdb0-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42cff04-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42d0044-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42d017a-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42d02ba-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42d03fa-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42d053a-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42d067a-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42d07b0-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}]} header={'exec_endpoint': '/'} routes=[{'pod': 'gateway', 'pod_id': 'c5a1293e-80b3-4b40-84d1-b9742611b92e', 'start_time': '2021-06-23T06:04:37.900145Z', 'end_time': '2021-06-23T06:04:37.901004Z'}, {'pod': 'gateway', 'pod_id': '6e3b1625-531d-4ec2-a8eb-43f2fb0fe7ee', 'start_time': '2021-06-23T06:04:37.900997Z'}] status={} at 5721399952>,
 <jina.types.request.Response request_id=653e1721-5371-42fb-98e8-714293a0b5bc data={'docs': [{'id': 'e42bc468-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42bd228-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42bd462-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42bd5fc-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42bd76e-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42bd8cc-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42bda20-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42bdb7e-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42bdcd2-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42bde1c-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}]} header={'exec_endpoint': '/'} routes=[{'pod': 'gateway', 'pod_id': 'c5a1293e-80b3-4b40-84d1-b9742611b92e', 'start_time': '2021-06-23T06:04:37.891429Z', 'end_time': '2021-06-23T06:04:37.895875Z'}, {'pod': 'gateway', 'pod_id': '6e3b1625-531d-4ec2-a8eb-43f2fb0fe7ee', 'start_time': '2021-06-23T06:04:37.895849Z'}] status={} at 5724839696>,
 <jina.types.request.Response request_id=5e8dddcc-0215-45cb-8d48-289c0e6f60ca data={'docs': [{'id': 'e42c086a-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c0be4-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c0d88-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c0f04-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c1062-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c11c0-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c133c-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c147c-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c15c6-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c1710-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}]} header={'exec_endpoint': '/'} routes=[{'pod': 'gateway', 'pod_id': 'c5a1293e-80b3-4b40-84d1-b9742611b92e', 'start_time': '2021-06-23T06:04:37.894530Z', 'end_time': '2021-06-23T06:04:37.896864Z'}, {'pod': 'gateway', 'pod_id': '6e3b1625-531d-4ec2-a8eb-43f2fb0fe7ee', 'start_time': '2021-06-23T06:04:37.896851Z'}] status={} at 5724838800>,
 <jina.types.request.Response request_id=d207de83-52c6-4287-8504-d6ab08816987 data={'docs': [{'id': 'e42c5306-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c55ea-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c57a2-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c5946-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c5ab8-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c5c20-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c5d7e-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c5edc-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c603a-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c618e-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}]} header={'exec_endpoint': '/'} routes=[{'pod': 'gateway', 'pod_id': 'c5a1293e-80b3-4b40-84d1-b9742611b92e', 'start_time': '2021-06-23T06:04:37.897747Z', 'end_time': '2021-06-23T06:04:37.898746Z'}, {'pod': 'gateway', 'pod_id': '6e3b1625-531d-4ec2-a8eb-43f2fb0fe7ee', 'start_time': '2021-06-23T06:04:37.898738Z'}] status={} at 5724838864>,
 <jina.types.request.Response request_id=590ae511-b5ad-4bd7-9ed1-baba2c63aadf data={'docs': [{'id': 'e42ce596-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42ce730-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42ce884-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42ce9d8-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42ceb18-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42cec76-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42cedf2-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42cef28-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42cf068-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42cf1a8-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}]} header={'exec_endpoint': '/'} routes=[{'pod': 'gateway', 'pod_id': 'c5a1293e-80b3-4b40-84d1-b9742611b92e', 'start_time': '2021-06-23T06:04:37.899588Z', 'end_time': '2021-06-23T06:04:37.900536Z'}, {'pod': 'gateway', 'pod_id': '6e3b1625-531d-4ec2-a8eb-43f2fb0fe7ee', 'start_time': '2021-06-23T06:04:37.900527Z'}] status={} at 4468253072>,
 <jina.types.request.Response request_id=4771806e-6c33-4a75-a519-85916a949ea2 data={'docs': [{'id': 'e42c3a06-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c3bf0-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c3d6c-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c3ede-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c4050-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c41ae-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c430c-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c446a-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c45c8-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42c473a-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}]} header={'exec_endpoint': '/'} routes=[{'pod': 'gateway', 'pod_id': 'c5a1293e-80b3-4b40-84d1-b9742611b92e', 'start_time': '2021-06-23T06:04:37.897122Z', 'end_time': '2021-06-23T06:04:37.898220Z'}, {'pod': 'gateway', 'pod_id': '6e3b1625-531d-4ec2-a8eb-43f2fb0fe7ee', 'start_time': '2021-06-23T06:04:37.898208Z'}] status={} at 5724837648>,
 <jina.types.request.Response request_id=76d92a47-7ce5-4a86-aab2-c3ced227d8e4 data={'docs': [{'id': 'e42cce62-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42cd074-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42cd1c8-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42cd312-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42cd452-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42cd592-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42cd6d2-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42cd81c-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42cd95c-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42cda9c-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}]} header={'exec_endpoint': '/'} routes=[{'pod': 'gateway', 'pod_id': 'c5a1293e-80b3-4b40-84d1-b9742611b92e', 'start_time': '2021-06-23T06:04:37.899022Z', 'end_time': '2021-06-23T06:04:37.899859Z'}, {'pod': 'gateway', 'pod_id': '6e3b1625-531d-4ec2-a8eb-43f2fb0fe7ee', 'start_time': '2021-06-23T06:04:37.899852Z'}] status={} at 5724837264>,
 <jina.types.request.Response request_id=c741e3dd-c57e-4deb-b074-99cd65037e05 data={'docs': [{'id': 'e42d123c-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42d143a-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42d15ac-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42d1700-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42d184a-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42d198a-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42d1ad4-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42d1c14-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42d1d54-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}, {'id': 'e42d1e9e-d3e8-11eb-aecd-1e008a366d48', 'content_hash': 'e4a6a0577479b2b4'}]} header={'exec_endpoint': '/'} routes=[{'pod': 'gateway', 'pod_id': 'c5a1293e-80b3-4b40-84d1-b9742611b92e', 'start_time': '2021-06-23T06:04:37.900727Z', 'end_time': '2021-06-23T06:04:37.902004Z'}, {'pod': 'gateway', 'pod_id': '6e3b1625-531d-4ec2-a8eb-43f2fb0fe7ee', 'start_time': '2021-06-23T06:04:37.901984Z'}] status={} at 5724837200>]

```

```{admonition} Caution
:class: caution
Turning on `return_results` breaks the streaming of the system. If you are sending 1000 requests,
then `return_results=True` means you will get nothing until the 1000th response returns. Moreover, if each response
takes 10MB memory, it means you will consume upto 10GB memory! On contrary, with callback and `return_results=False`,
your memory usage will stay constant at 10MB.
```

## Environment Variables

In some scenarios, you may want to set environment variables to the Flow and use it inside Executor.
To do that, you can use `env`:

```python
import os
from jina import Flow, Executor, requests


class MyExecutor(Executor):
    @requests
    def foo(self, **kwargs):
        print('MY_ENV', '->', os.environ.get('MY_ENV'))


f = Flow().add(uses=MyExecutor, env={'MY_ENV': 'MY_ENV_VALUE'})

with f:
    f.post('/foo')
```

```console
           Flow@23340[I]:🎉 Flow is ready to use!
	🔗 Protocol: 		GRPC
	🏠 Local access:	0.0.0.0:51587
	🔒 Private network:	172.18.0.253:51587
	🌐 Public address:	94.135.231.132:51587
MY_ENV -> MY_ENV_VALUE

Process finished with exit code 0
```
