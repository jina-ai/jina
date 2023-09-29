(executor-dynamic-batching)=
# Dynamic Batching
Dynamic batching allows requests to be accumulated and batched together before being sent to 
an {class}`~jina.Executor`. The batch is created dynamically depending on the configuration for each endpoint.

This feature is especially relevant for inference tasks where model inference is more optimized when batched to efficiently use GPU resources.

## Overview
Enabling dynamic batching on Executor endpoints that perform inference typically results in better hardware usage and thus, in increased throughput. 

When you enable dynamic batching, incoming requests to Executor endpoints with the same {ref}`request parameters<client-executor-parameters>`
are queued together. The Executor endpoint is executed on the queue requests when either:

- the number of accumulated Documents exceeds the {ref}`preferred_batch_size<executor-dynamic-batching-parameters>` parameter
- or the {ref}`timeout<executor-dynamic-batching-parameters>` parameter is exceeded.

Although this feature _can_ work on {ref}`parametrized requests<client-executor-parameters>`, it's best used for endpoints that don't often receive different parameters.
Creating a batch of requests typically results in better usage of hardware resources and potentially increased throughput.

You can enable and configure dynamic batching on an Executor endpoint using several methods:
* {class}`~jina.dynamic_batching` decorator
* `uses_dynamic_batching` Executor parameter
* `dynamic_batching` section in Executor YAML

## Example
The following examples show how to enable dynamic batching on an Executor Endpoint:

````{tab} Using dynamic_batching Decorator
This decorator is applied per Executor endpoint.
Only Executor endpoints (methods decorated with `@requests`) decorated with `@dynamic_batching` have dynamic 
batching enabled.

```{code-block} python
---
emphasize-lines: 22
---
from jina import Executor, requests, dynamic_batching, Deployment
from docarray import DocList, BaseDoc
from docarray.typing import AnyTensor, AnyEmbedding
from typing import Optional

import numpy as np
import torch

class MyDoc(BaseDoc):
    tensor: Optional[AnyTensor[128]] = None
    embedding: Optional[AnyEmbedding[128]] = None


class MyExecutor(Executor):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # initialize model
        self.model = torch.nn.Linear(in_features=128, out_features=128)
    
    @requests(on='/bar')
    @dynamic_batching(preferred_batch_size=10, timeout=200)
    def embed(self, docs: DocList[MyDoc], **kwargs) -> DocList[MyDoc]:
        docs.embedding = self.model(torch.Tensor(docs.tensor))

dep = Deployment(uses=MyExecutor)
```
````

````{tab} Using uses_dynamic_batching argument
This argument is a dictionary mapping each endpoint to its corresponding configuration:
```{code-block} python
---
emphasize-lines: 28
---
from jina import Executor, requests, dynamic_batching, Deployment
from docarray import DocList, BaseDoc
from docarray.typing import AnyTensor, AnyEmbedding
from typing import Optional

import numpy as np
import torch

class MyDoc(BaseDoc):
    tensor: Optional[AnyTensor[128]] = None
    embedding: Optional[AnyEmbedding[128]] = None


class MyExecutor(Executor):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # initialize model
        self.model = torch.nn.Linear(in_features=128, out_features=128)
    
    @requests(on='/bar')
    def embed(self, docs: DocList[MyDoc], **kwargs) -> DocList[MyDoc]:
        docs.embedding = self.model(torch.Tensor(docs.tensor))


dep = Deployment(
    uses=MyExecutor,
    uses_dynamic_batching={'/bar': {'preferred_batch_size': 10, 'timeout': 200}},
)
```
````

````{tab} Using YAML configuration
If you use YAML to enable dynamic batching on an Executor, you can use the `dynamic_batching` section in the 
Executor section. Suppose the Executor is implemented like this:
`my_executor.py`:
```python
from jina import Executor, requests, dynamic_batching, Deployment
from docarray import DocList, BaseDoc
from docarray.typing import AnyTensor, AnyEmbedding
from typing import Optional

import numpy as np
import torch

class MyDoc(BaseDoc):
    tensor: Optional[AnyTensor[128]] = None
    embedding: Optional[AnyEmbedding[128]] = None


class MyExecutor(Executor):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # initialize model
        self.model = torch.nn.Linear(in_features=128, out_features=128)
    
    @requests(on='/bar')
    def embed(self, docs: DocList[MyDoc], **kwargs) -> DocList[MyDoc]:
        docs.embedding = self.model(torch.Tensor(docs.tensor))
```

Then, in your `config.yaml` file, you can enable dynamic batching on the `/bar` endpoint like so:
``` yaml
jtype: MyExecutor
py_modules:
    - my_executor.py
uses_dynamic_batching:
  /bar:
    preferred_batch_size: 10
    timeout: 200
```

We then deploy with:

```python
from jina import Deployment

with Deployment(uses='config.yml') as dep:
    dep.block()
```
````


(executor-dynamic-batching-parameters)=
## Parameters
The following parameters allow you to configure the dynamic batching behavior on each Executor endpoint:
* `preferred_batch_size`: Target number of Documents in a batch. The batcher collects requests until 
`preferred_batch_size` is reached, or until `timeout` is reached. Therefore, the actual batch size could be smaller or 
larger than `preferred_batch_size`.
* `timeout`:  Maximum time in milliseconds to wait for a request to be assigned to a batch.
If the oldest request in the queue reaches a waiting time of `timeout`, the batch is passed to the Executor, even 
if it contains fewer than `preferred_batch_size` Documents. Default is 10,000ms (10 seconds).
