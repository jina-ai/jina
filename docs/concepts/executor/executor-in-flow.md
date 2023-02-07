(executor-in-flow)=
# Executors in Flows

You can chain Executors together into a {ref}`Flow <flow-cookbook>`, which orchestrates Executors into a processing pipeline to accomplish a task. Documents “flow” through the pipeline and are processed by each Executor in turn.

When developing an Executor to put into a Flow, there are several practices you should follow:

(merge-upstream-documentarrays)=
## Merging upstream DocumentArrays

Often when you're building a Flow, you want an Executor to receive DocumentArrays from multiple upstream Executors. 

```{figure} flow-merge-executor.svg
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
### Reducing multiple DocumentArrays to one DocumentArray

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

## Serve

Both served and shared Executors can be used as part of a Flow, by adding them as an {ref}`external Executor <external-executors>`. If the Executor is only used inside other Flows, you should define a shared Executor to save the costs of running the Gateway in Kubernetes.
