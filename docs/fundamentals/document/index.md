(document-cookbook)=
# Document

{class}`~jina.types.document.Document` is the basic data type that Jina operates with text, picture, video, audio, image or 3D mesh: They are
all `Document`s in Jina.

{class}`~jina.types.arrays.document.DocumentArray` is a sequence container of `Document`s. It is the first-class citizen of `Executor`, serving as the
Executor's input and output.

{class}`~jina.types.arrays.memmap.DocumentArrayMemmap` is an on-disk sequence container of `Document`s. It shares almost the same interface as `DocumentArray` but with much smaller memory footprint. 


```{hint}
You could say `Document` is to Jina is what `np.float` is to Numpy, and `DocumentArray` is similar to `np.ndarray`.
```

````{admonition} See Also
:class: seealso

Document, Executor, and Flow are the three fundamental concepts in Jina.

- {doc}`Document <../document/index>` is the basic data type in Jina;
- {ref}`Executor <executor>` is how Jina processes Documents;
- {ref}`Flow <flow>` is how Jina streamlines and scales Executors.
````

```{toctree}
:hidden:

document-api
documentarray/index
```