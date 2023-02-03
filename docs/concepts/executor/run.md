# Run

### From a local Python class

```python
from jina import Executor, requests, DocumentArray, Document


class MyExec(Executor):
    @requests
    def foo(self, docs, **kwargs):
        for d in docs:
            d.text = 'hello world'


executor = MyExec()
docs = DocumentArray([Document(text='hello')])

executor.foo(da)
print(f'Text: {docs[0].text}')
```

```text
Text: hello world
```

### From Executor Hub

[Executor Hub](https://cloud.jina.ai/executors) is Jina AI's marketplace for Executors, letting you pull Executors to your local machine without getting your hands dirty implementing functionality from scratch. Check the {ref}`docs <jina-hub>` for more information.

```python
from docarray import Document, DocumentArray
from jina import Executor

executor = Executor.from_hub(
    uri='jinaai://jina-ai/CLIPTextEncoder', install_requirements=True
)

docs = DocumentArray(Document(text='hello'))
executor.encode(docs, {})

print(docs.embeddings.shape)
```
```text
(1, 512)
```
