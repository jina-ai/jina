# Temporary Cookbook on Document 2.0 API

Document, Executor, Flow are the three fundamental concepts in Jina.

- **Document** is the basic data type in Jina;
- **Executor** is how Jina processes Documents;
- **Flow** is how Jina streamlines and scales Executors.

## `Document`: the primitive data type in Jina

Text, picture, video, audio, image, 3D mesh, they are all `Document` in Jina.

`Document` to Jina is like `np.float` to Numpy. It is the basic data type that Jina operates with.

`DocumentArray` to Jina is like `np.ndarray` to Numpy. It is a sequence container of `Document`.

The input & output of Jina `Executor` is `DocumentArray`, e.g.

```python
from jina import Executor, requests, DocumentArray


class MyExec(Executor):

    @requests
    def foo(self, docs: DocumentArray, **kwargs) -> Optional[DocumentArray]:
        ...
```

## Extracting Multiple Attributes

One can extract multiple attributes from a `Document` via



