(executor-dynamic-batching)=
# Dynamic Batching
Dynamic batching is a feature of Jina that allows requests to be accumulated and batched together before being sent to 
an {class}`~jina.Executor`. The batch is created dynamically depending on the per-endpoint dynamic batching configuration.

This feature is relevant especially for inference tasks where model inference is more optimized when done in batches in 
order to efficiently use GPU resources.

## Overview
Enabling dynamic batching on Executor endpoints that perform inference typically results in increased throughput. 

When Dynamic Batching is enabled requests incoming to an Executor endpoints with the same {ref}`request parameters<client-executor-parameters>`
will be queued together. The Executor endpoint will be executed on the queue requests when the number of documents 
accumulated exceeds the {ref}`preferred_batch_size<executor-dynamic-batching-parameters>` parameter or when the {ref}`timeout<executor-dynamic-batching-parameters` parameter is exceeded.

Although this feature can work on {ref}`parametrized requests<client-executor-parameters>`, it is best used for endpoints
that do not receive different parameters often.
Creating a batch of requests typically results in increased throughput.

Dynamic batching is enabled and configured on each Executor endpoint using several methods:
* {class}`~jina.dynamic_batching` decorator
* `uses_dynamic_batching` Executor parameter
* `dynamic_batching` section in Executor YAML

## Example:
The following examples shows how to enable dynamic batching on an Executor Endpoint:

````{tab} Using dynamic_batching Decorator
This decorator is applied per Executor endpoint.
Only Executor endpoints (methods decorated with `@requests`) decorated with `@dynamic_batching` will have dynamic 
batching enabled.

```{code-block} python
---
emphasize-lines: 12
---
from jina import requests, dynamic_batching, Executor, DocumentArray, Flow

class MyExecutor(Executor):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # initialize model
        import torch
        self.model = torch.nn.Linear(in_features=128, out_features=128)
    
    @requests(on='/bar')
    @dynamic_batching(preferred_batch_size=10, timeout=200)
    def embed(self, docs: DocumentArray):
        docs.embeddings = self.model(docs.tensors)

flow = Flow().add(uses=MyExecutor)
```
````

````{tab} Using uses_dynamic_batching argument
This argument is a dictionnary mapping each endpoint to it's corresponding configuration:
```{code-block} python
---
emphasize-lines: 12
---
from jina import requests, dynamic_batching, Executor, DocumentArray

class MyExecutor(Executor):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # initialize model
        import torch
        self.model = torch.nn.Linear(in_features=128, out_features=128)
    
    @requests(on='/bar')
    def embed(self, docs: DocumentArray):
        docs.embeddings = self.model(docs.tensors)
        
flow = Flow().add(uses=MyExecutor, uses_dynamic_batching={'/bar': {'preferred_batch_size': 10, 'timeout': 200}})
```
````

````{tab} Using YAML configuration
If you want to use YAML to enable dynamic batching on an Executor, you can use the `dynamic_batching` section in the 
Executor section. Suppose the Executor is implemented like this:
`my_executor.py`:
```{code-block} python
---
emphasize-lines: 12
---
from jina import requests, dynamic_batching, Executor, DocumentArray

class MyExecutor(Executor):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # initialize model
        import torch
        self.model = torch.nn.Linear(in_features=128, out_features=128)
    
    @requests(on='/bar')
    def embed(self, docs: DocumentArray):
        docs.embeddings = self.model(docs.tensors)
```

Then, in your `config.yaml` file, you can enable dynamic batching on the `/bar` endpoint like so:
``` yaml
!MyExecutor
py_modules:
    - my_executor.yaml
dynamic_batching:
  /bar:
    preferred_batch_size: 10
    timeout: 200
```
````

(executor-dynamic-batching-parameters)=
## Dynamic Batching Parameters
The following parameters allow you to configure the dynamic batching behavior on each Executor endpoint:
* `preferred_batch_size`: Target number of Documents in a batch. The batcher will collect requests until 
`preferred_batch_size` is reached, or until `timeout` is reached. Therefore, the actual batch size can be smaller or 
larger than `preferred_batch_size`.
* `timeout`:  maximum time in milliseconds to wait for a request to be assigned to a batch.
If the oldest request in the queue reaches a waiting time of `timeout`, the batch will be passed to the Executor, even 
if it contains fewer than `preferred_batch_size` Documents. Default is 10_000ms (10 seconds).
