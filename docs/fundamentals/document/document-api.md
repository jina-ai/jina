# Document

```{toctree}
:hidden:

fluent-interface
```

{class}`~jina.types.document.Document` is the basic data type in Jina. Whether you're working with text, image, video, audio, or 3D meshes, they are
all `Document`s in Jina.


## Construct

````{tab} Empty document

```python
from jina import Document

d = Document()
```

````

````{tab} From attributes 

```python
from jina import Document
import numpy

d1 = Document(text='hello')
d2 = Document(buffer=b'\f1')
d3 = Document(blob=numpy.array([1, 2, 3]))
d4 = Document(uri='https://jina.ai',
             mime_type='text/plain',
             granularity=1,
             adjacency=3,
             tags={'foo': 'bar'})
```


```console
<jina.types.document.Document ('id', 'mime_type', 'text') at 4483297360>
<jina.types.document.Document ('id', 'buffer') at 5710817424>
<jina.types.document.Document ('id', 'blob') at 4483299536>
<jina.types.document.Document id=e01a53bc-aedb-11eb-88e6-1e008a366d48 uri=https://jina.ai mimeType=text/plain tags={'foo': 'bar'} granularity=1 adjacency=3 at 6317309200>
```

````


````{tab} From another Document

```python
from jina import Document

d = Document(content='hello, world!')
d1 = d

assert id(d) == id(d1)  # True
```

To make a deep copy, use `copy=True`:

```python
d1 = Document(d, copy=True)

assert id(d) == id(d1)  # False
```

````

`````{tab} From dict or JSON string

```python
from jina import Document
import json

d = {'id': 'hello123', 'content': 'world'}
d1 = Document(d)

d = json.dumps({'id': 'hello123', 'content': 'world'})
d2 = Document(d)
```

````{admonition} Parsing unrecognized fields
:class: tip

Unrecognized fields in a `dict`/JSON string are automatically put into the Document's `.tags` field:

```python
from jina import Document

d1 = Document({'id': 'hello123', 'foo': 'bar'})
```

```text
<jina.types.document.Document id=hello123 tags={'foo': 'bar'} at 6320791056>
```

You can use `field_resolver` to map external field names to `Document` attributes:

```python
from jina import Document

d1 = Document({'id': 'hello123', 'foo': 'bar'}, field_resolver={'foo': 'content'})
```

```text
<jina.types.document.Document id=hello123 mimeType=text/plain text=bar at 6246985488>
```

````


`````

## Set/unset attributes

````{tab} Set
Set an attribute as you would with any Python object: 

```python
from jina import Document

d = Document()
d.text = 'hello world'
```

```text
<jina.types.document.Document id=9badabb6-b9e9-11eb-993c-1e008a366d49 mime_type=text/plain text=hello world at 4444621648>
```
````

````{tab} Unset

```python
d.text = None
```

or 

```python
d.pop('text')
```

```text
<jina.types.document.Document id=cdf1dea8-b9e9-11eb-8fd8-1e008a366d49 mime_type=text/plain at 4490447504>
```
````

````{tab} Unset multiple attributes

```python
d.pop('text', 'id', 'mime_type')
```

```text
<jina.types.document.Document at 5668344144>
```
````



## Content 

{attr}`~jina.Document.text`, {attr}`~jina.Document.blob`, and {attr}`~jina.Document.buffer` are the three content attributes of a Document. They correspond to string-like data (e.g. for natural language), `ndarray`-like data (e.g. for image/audio/video data), and binary data for general purpose, respectively. Each Document can contain only one type of content.

| Attribute | Accept type | Use case |
| --- | --- | --- |
| `doc.text` | Python string | Contain text |
| `doc.blob` | Numpy `ndarray`, SciPy sparse matrix (`spmatrix`), TensorFlow dense & sparse tensor, PyTorch dense & sparse tensor, PaddlePaddle dense tensor | Contain image/video/audio |
| `doc.buffer` | 	Binary string | Contain intermediate IO buffer |

````{admonition} Exclusivity of the content
:class: important

Note that one `Document` can only contain one type of `content`: either `text`, `buffer`, or `blob`. If you set one, the others will be cleared. 

```python
import numpy as np

d = Document(text='hello')
d.blob = np.array([1])

d.text  # <- now it's empty
```

````

````{admonition} Why a Document contains only data type
:class: question

What if you want to represent more than one kind of information? Say, to fully represent a PDF page you need to store both image and text. In this case, you can use {ref}`nested Document<recursive-nested-document>`s by putting image into one sub-Document, and text into another.

```python
d = Document(chunks=[Document(blob=...), Document(text=...)])
```


The principle is each Document contains only one modality. This makes the whole logic clearer.
````

```{tip}
There is also a `doc.content` sugar getter/setter of the above non-empty field. The content will be automatically grabbed or assigned to either `text`, `buffer`, or `blob` field based on the given type.
```



### Load content from URI

Often, you need to load data from a URI instead of assigning them directly in your code, {attr}`~jina.Document.uri` is the attribute you must learn. 

After setting `.uri`, you can load data into `.text`/`.buffer`/`.blob` as follows.

The value of `.uri` can point to either local URI, remote URI or [data URI](https://en.wikipedia.org/wiki/Data_URI_scheme).

````{tab} Local image URI


```python
from jina import Document

d1 = Document(uri='apple.png').load_uri_to_image_blob()
print(d1.content_type, d1.content)
```

```console
blob [[[255 255 255]
  [255 255 255]
  [255 255 255]
  ...
```
````


````{tab} Remote text URI

```python
from jina import Document

d1 = Document(uri='https://www.gutenberg.org/files/1342/1342-0.txt').load_uri_to_text()

print(d1.content_type, d1.content)
```


```console
text ﻿The Project Gutenberg eBook of Pride and Prejudice, by Jane Austen

This eBook is for the use of anyone anywhere in the United States and
most other parts of the wor
```
````

````{tab} Inline data URI

```python
from jina import Document

d1 = Document(uri='''data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA
AAAFCAYAAACNbyblAAAAHElEQVQI12P4//8/w38GIAXDIBKE0DHxgljNBAAO
9TXL0Y4OHwAAAABJRU5ErkJggg==
''').load_uri_to_image_blob()

print(d1.content_type, d1.content)
```
```console
blob [[[255 255 255]
  [255   0   0]
  [255   0   0]
  [255   0   0]
  [255 255 255]]
  ...
```

````

There are more `.load_uri_to_*` functions that allow you to read {ref}`text<text-type>`, {ref}`image<image-type>`, {ref}`video<video-type>`, {ref}`3D mesh<mesh-type>`, {ref}`audio<audio-type>` and {ref}`tabular<table-type>` data into Jina.

```{admonition} Write to data URI
:class: tip
Inline data URI is helpful when you need a quick visualization in HTML, as it embeds all resources directly into that HTML. 

You can convert a URI to a data URI using `doc.load_uri_to_datauri()`. This will fetch the resource and make it inline.
```


## Embedding

Embedding is a multi-dimensional representation of a `Document` (often a `[1, D]` vector). It serves as a very important piece in the neural search. 

Document has an attribute {attr}`~jina.Document.embedding` to contain the embedding information.

Like `.blob`, you can assign it with Numpy `ndarray`, SciPy sparse matrix (`spmatrix`), TensorFlow dense and sparse tensor, PyTorch dense and sparse tensor, or PaddlePaddle dense tensor.

```python
import numpy as np
import scipy.sparse as sp
import torch
import tensorflow as tf
from jina import Document

d1 = Document(embedding=np.array([1, 2, 3]))
d2 = Document(embedding=np.array([[1, 2, 3], [4, 5, 6]]))
d3 = Document(embedding=sp.coo_matrix([0, 0, 0, 1, 0]))
d4 = Document(embedding=torch.tensor([1, 2, 3]))
d5 = Document(embedding=tf.sparse.from_dense(np.array([[1, 2, 3], [4, 5, 6]])))
```

### Fill embedding from DNN model

```{admonition} On multiple Documents
:class: tip

This is a syntax sugar on single Document, which leverages {meth}`~jina.types.arrays.mixins.embed.EmbedMixin.embed` underneath. To embed multiple Documents, do not use this feature in a for-loop. Instead, read more details in {ref}`embed-via-model`.    
```

Once a `Document` has `.blob` set, you can use a deep neural network to {meth}`~jina.types.arrays.mixins.embed.EmbedMixin.embed` it, which means filling `Document.embedding`. For example, our `Document` looks like the following:

```python
q = (Document(uri='/Users/hanxiao/Downloads/left/00003.jpg')
     .load_uri_to_image_blob()
     .set_image_blob_normalization()
     .set_image_blob_channel_axis(-1, 0))
```

Let's embed it into vector via ResNet:

```python
import torchvision
model = torchvision.models.resnet50(pretrained=True)
q.embed(model)
```

### Find nearest-neighbours

```{admonition} On multiple Documents
:class: tip

This is a syntax sugar on single Document, which leverages  {meth}`~jina.types.arrays.mixins.match.MatchMixin.match` underneath. To match multiple Documents, do not use this feature in a for-loop. Instead, find out more in {ref}`match-documentarray`.  
```

Once a Document has `.embedding` filled, it can be "matched". In this example, we build ten Documents and put them into a {ref}`DocumentArray<da-intro>`, and then use another Document to search against them.

```python
from jina import DocumentArray, Document
import numpy as np

da = DocumentArray.empty(10)
da.embeddings = np.random.random([10, 256])

q = Document(embedding=np.random.random([256]))
q.match(da)

print(q.matches[0])
```

```console
<jina.types.document.Document ('id', 'embedding', 'adjacency', 'scores') at 8256118608>
```



(recursive-nested-document)=
## Nested Documents

`Document` can be nested both horizontally and vertically. The following graphic illustrates the recursive `Document` structure. Each `Document` can have multiple "chunks"
and "matches", which are `Document` as well.

<img src="https://hanxiao.io/2020/08/28/What-s-New-in-Jina-v0-5/blog-post-v050-protobuf-documents.jpg">

|  Attribute   |   Description  |
| --- | --- |
| `doc.chunks` | The list of sub-Documents of this Document. They have `granularity + 1` but same `adjacency` |
| `doc.matches` | The list of matched Documents of this Document. They have `adjacency + 1` but same `granularity` |
| `doc.granularity` | The recursion "depth" of the recursive chunks structure |
| `doc.adjacency` | The recursion "width" of the recursive match structure |

You can add **chunks** (sub-Document) and **matches** (neighbour-Document) to a `Document`:

- Add in constructor:

  ```python
  d = Document(chunks=[Document(), Document()], matches=[Document(), Document()])
  ```

- Add to existing `Document`:

  ```python
  d = Document()
  d.chunks = [Document(), Document()]
  d.matches = [Document(), Document()]
  ```

- Add to existing `doc.chunks` or `doc.matches`:

  ```python
  d = Document()
  d.chunks.append(Document())
  d.matches.append(Document())
  ```

````{admonition} Note
:class: note
Both `doc.chunks` and `doc.matches` return `ChunkArray` and `MatchArray`, which are sub-classes
of {ref}`DocumentArray<documentarray>`. We will introduce `DocumentArray` later.
````

`````{admonition} Caveat: order matters
:class: alert


When adding sub-Documents to `Document.chunks`, avoid creating them in one line, otherwise the recursive Document structure will not be correct. This is because `chunks` use `ref_doc` to control their `granularity`. At `chunk` creation time the `chunk` doesn't know anything about its parent, and will get a wrong `granularity` value.

````{tab} ✅ Do
```python
from jina import Document

root_document = Document(text='i am root')
# add one chunk to root
root_document.chunks.append(Document(text='i am chunk 1'))
root_document.chunks.extend([
   Document(text='i am chunk 2'),
   Document(text='i am chunk 3'),
])  # add multiple chunks to root
```
````

````{tab} 😔 Don't
```python
from jina import Document

root_document = Document(
   text='i am root',
   chunks=[
      Document(text='i am chunk 2'),
      Document(text='i am chunk 3'),
   ]
)
```
````


`````


## Tags

`Document` contains the {attr}`~jina.Document.tags` attribute that can hold a map-like structure that can map arbitrary values. 
In practice, you can store meta information in `tags`.

```python
from jina import Document

doc = Document(tags={'dimensions': {'height': 5.0, 'weight': 10.0, 'last_modified': 'Monday'}})

doc.tags['dimensions']
```

```text
{'weight': 10.0, 'height': 5.0, 'last_modified': 'Monday'}
```

To provide easy access to nested fields, the `Document` allows you to access attributes by composing the attribute
qualified name with interlaced `__` symbols:

```python
from jina import Document

doc = Document(tags={'dimensions': {'height': 5.0, 'weight': 10.0}})

doc.tags__dimensions__weight
```

```text
10.0
```

This also allows the access of nested metadata attributes in `bulk` from a `DocumentArray`.

```python
from jina import Document, DocumentArray

da = DocumentArray([Document(tags={'dimensions': {'height': 5.0, 'weight': 10.0}}) for _ in range(10)])

da.get_attributes('tags__dimensions__height', 'tags__dimensions__weight')
```

```text
[[5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0], [10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0]]
```


`````{admonition} Note
:class: caution

As `tags` does not have a fixed schema, it is declared with type `google.protobuf.Struct` in the `DocumentProto`
protobuf declaration. However, `google.protobuf.Struct` follows the JSON specification and does not 
differentiate `int` from `float`. So, data of type `int` in `tags` will be **always** casted to `float` when a request is
sent to an Executor.

As a result, users need be explicit and cast the data to the expected type as follows:

````{tab} ✅ Do
```{code-block} python
---
emphasize-lines: 7, 8
---

class MyIndexer(Executor):
    animals = ['cat', 'dog', 'turtle']
    @request
    def foo(self, docs, parameters: dict, **kwargs):
        for doc in docs:
            # need to cast to int since list indices must be integers not float
            index = int(doc.tags['index'])
            assert self.animals[index] == 'dog'

with Flow().add(uses=MyExecutor) as f:
    f.post(on='/endpoint',
    inputs=DocumentArray([]), parameters={'index': 1})
```
````

````{tab} 😔 Don't
```{code-block} python
---
emphasize-lines: 7, 8
---

class MyIndexer(Executor):
    animals = ['cat', 'dog', 'turtle']
    @request
    def foo(self, docs, parameters: dict, **kwargs):
        for doc in docs:
            # ERROR: list indices must be integer not float
            index = doc.tags['index']
            assert self.animals[index] == 'dog'

with Flow().add(uses=MyExecutor) as f:
    f.post(on='/endpoint',
    inputs=DocumentArray([]), parameters={'index': 1})
```
````

`````




## Serialization

You can serialize a `Document` into JSON string or Python dict or binary string:
````{tab} JSON
```python
from jina import Document

d = Document(content='hello, world')
d.json()
```

```json
{
  "id": "6a1c7f34-aef7-11eb-b075-1e008a366d48",
  "mimeType": "text/plain",
  "text": "hello world"
}
```
````

````{tab} Binary
```python
from jina import Document

d = Document(content='hello, world')
d.binary_str()
```

```
b'\n$6a1c7f34-aef7-11eb-b075-1e008a366d48R\ntext/plainj\x0bhello world'
```
````

````{tab} Dict
```python
from jina import Document

d = Document(content='hello, world')
d.dict()
```

```
{'id': '6a1c7f34-aef7-11eb-b075-1e008a366d48', 'mimeType': 'text/plain', 'text': 'hello world'}
```
````

## Visualization

To better see the Document's recursive structure, you can use {meth}`~jina.types.document.mixins.plot.PlotMixin.plot` function. If you are using JupyterLab/Notebook,
all `Document` objects will be auto-rendered:


```{code-block} python
---
emphasize-lines: 13
---
import numpy as np
from jina import Document

d0 = Document(id='🐲', embedding=np.array([0, 0]))
d1 = Document(id='🐦', embedding=np.array([1, 0]))
d2 = Document(id='🐢', embedding=np.array([0, 1]))
d3 = Document(id='🐯', embedding=np.array([1, 1]))

d0.chunks.append(d1)
d0.chunks[0].chunks.append(d2)
d0.matches.append(d3)

d0.plot()  # simply `d0` on JupyterLab
```


```{figure} ../../../.github/images/four-symbol-docs.svg
:align: center
```
