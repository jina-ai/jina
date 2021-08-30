# Document/DocumentArray

`Document` is the basic data type that Jina operates with text, picture, video, audio, image or 3D mesh: They are
all `Document`s in Jina.

`DocumentArray` is a sequence container of `Document`s. It is the first-class citizen of `Executor`, serving as the
Executor's input and output.

You could say `Document` is to Jina is what `np.float` is to Numpy, and `DocumentArray` is similar to `np.ndarray`.

## Minimum working example

```python
from jina import Document

d = Document() 
```

````{admonition} See Also
:class: seealso
{ref}`Executor <executor>`
````

```{toctree}
:hidden:

document-api
documentarray-api
documentarraymemmap-api
```