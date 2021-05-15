Document, Executor, Flow are three fundamental concepts in Jina.

- [**Document**](COOKBOOK-Document.md) is the basic data type in Jina;
- [**Executor**](COOKBOOK-Executor.md) is how Jina processes Documents;
- **Flow** is how Jina streamlines and scales Executors.

*Learn them all, nothing more, you are good to go.*

---

# Temporary Cookbook on `Document`/`DocumentArray` 2.0 API

`Document` is the basic data type that Jina operates with. Text, picture, video, audio, image, 3D mesh, they are
all `Document` in Jina.

`DocumentArray` is a sequence container of `Document`. It is the first-class citizen of `Executor`, serving as the input
& output.

One can say `Document` to Jina is like `np.float` to Numpy, then `DocumentArray` is like `np.ndarray`.

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
Table of Contents

- [Minimum working example](#minimum-working-example)
- [`Document` API](#document-api)
  - [`Document` Attributes](#document-attributes)
  - [Construct `Document`](#construct-document)
    - [Exclusivity of `doc.content`](#exclusivity-of-doccontent)
    - [Conversion between `doc.content`](#conversion-between-doccontent)
    - [Construct with Multiple Attributes](#construct-with-multiple-attributes)
    - [Construct from Dict or JSON String](#construct-from-dict-or-json-string)
    - [Construct from Another `Document`](#construct-from-another-document)
    - [Construct from Generator](#construct-from-generator)
  - [Serialize `Document`](#serialize-document)
  - [Add Recursion to `Document`](#add-recursion-to-document)
    - [Recursive Attributes](#recursive-attributes)
  - [Visualize `Document`](#visualize-document)
  - [Add Relevancy to `Document`](#add-relevancy-to-document)
    - [Relevance Attributes](#relevance-attributes)
- [`DocumentArray` API](#documentarray-api)
  - [Construct `DocumentArray`](#construct-documentarray)
  - [Persistence via `save()`/`load()`](#persistence-via-saveload)
  - [Get Attributes in Bulk](#get-attributes-in-bulk)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Minimum working example

```python
from jina import Document

d = Document() 
```

## `Document` API

### `Document` Attributes

A `Document` object has the following attributes, which can be put into the following categories:

| | | 
|---|---|
| Content attributes | `.buffer`, `.blob`, `.text`, `.uri`, `.content`, `.embedding` |
| Meta attributes | `.id`, `.weight`, `.mime_type`, `.location`, `.tags`, `.offset`, `.modality` |
| Recursive attributes | `.chunks`, `.matches`, `.granularity`, `.adjacency` |
| Relevance attributes | `.score`, `.evaluations` |

### Construct `Document`

##### Content Attributes

|     |     |
| --- | --- |
| `doc.buffer` | The raw binary content of this document |
| `doc.blob` | The `ndarray` of the image/audio/video document |
| `doc.text` | The text info of the document |
| `doc.uri` | A uri of the document could be: a local file path, a remote url starts with http or https or data URI scheme |
| `doc.content` | One of the above non-empty field |
| `doc.embedding` | The embedding `ndarray` of this Document |

You can assign `str`, `ndarray`, `buffer`, `uri` to a `Document`.

```python
from jina import Document
import numpy as np

d1 = Document(content='hello')
d2 = Document(content=b'\f1')
d3 = Document(content=np.array([1, 2, 3]))
d4 = Document(content='https://static.jina.ai/logo/core/notext/light/logo.png')
```

```text
<jina.types.document.Document id=2ca74b98-aed9-11eb-b791-1e008a366d48 mimeType=text/plain text=hello at 6247702096>
<jina.types.document.Document id=2ca74f1c-aed9-11eb-b791-1e008a366d48 buffer=DDE= mimeType=text/plain at 6247702160>
<jina.types.document.Document id=2caab594-aed9-11eb-b791-1e008a366d48 blob={'dense': {'buffer': 'AQAAAAAAAAACAAAAAAAAAAMAAAAAAAAA', 'shape': [3], 'dtype': '<i8'}} at 6247702416>
<jina.types.document.Document id=4c008c40-af9f-11eb-bb84-1e008a366d49 uri=https://static.jina.ai/logo/core/notext/light/logo.png mimeType=image/png at 6252395600>
```

The content will be automatically assigned to one of `text`, `buffer`, `blob`, `uri` fields, `id` and `mime_type` are
auto-generated when not given.

In Jupyter notebook or use `.plot()`, you can get the visualization of a `Document` object.

<img src="https://mermaid.ink/svg/JSV7aW5pdDogeyd0aGVtZSc6ICdiYXNlJywgJ3RoZW1lVmFyaWFibGVzJzogeyAncHJpbWFyeUNvbG9yJzogJyNGRkM2NjYnfX19JSUKICAgICAgICAgICAgICAgICAgICBjbGFzc0RpYWdyYW0KICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgY2xhc3MgZDY5fkRvY3VtZW50fnsKK2lkIGU4MDY0MjdlLWEKK21pbWVfdHlwZSB0ZXh0L3BsYWluCit0ZXh0IGhlbGxvCn0="/><img src="https://mermaid.ink/svg/JSV7aW5pdDogeyd0aGVtZSc6ICdiYXNlJywgJ3RoZW1lVmFyaWFibGVzJzogeyAncHJpbWFyeUNvbG9yJzogJyNGRkM2NjYnfX19JSUKICAgICAgICAgICAgICAgICAgICBjbGFzc0RpYWdyYW0KICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgY2xhc3MgZDczfkRvY3VtZW50fnsKK2lkIGZmZTQzMmFjLWEKK2J1ZmZlciBEREU9CittaW1lX3R5cGUgdGV4dC9wbGFpbgp9"/><img src="https://mermaid.ink/svg/JSV7aW5pdDogeyd0aGVtZSc6ICdiYXNlJywgJ3RoZW1lVmFyaWFibGVzJzogeyAncHJpbWFyeUNvbG9yJzogJyNGRkM2NjYnfX19JSUKICAgICAgICAgICAgICAgICAgICBjbGFzc0RpYWdyYW0KICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgY2xhc3MgZDJmfkRvY3VtZW50fnsKK2lkIDAzOWVmMzE0LWEKK2Jsb2IoPGNsYXNzICdudW1weS5uZGFycmF5Jz4pCn0="/><img src="https://mermaid.ink/svg/JSV7aW5pdDogeyd0aGVtZSc6ICdiYXNlJywgJ3RoZW1lVmFyaWFibGVzJzogeyAncHJpbWFyeUNvbG9yJzogJyNGRkM2NjYnfX19JSUKICAgICAgICAgICAgICAgICAgICBjbGFzc0RpYWdyYW0KICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgY2xhc3MgMjRmfkRvY3VtZW50fnsKK2lkIDA2YTE2OGY4LWEKK3VyaSBodHRwczovL3N0CittaW1lX3R5cGUgaW1hZ2UvcG5nCn0="/>

#### Exclusivity of `doc.content`

![](doc.content.svg?raw=true)

Note that one `Document` can only contain one type of `content`: it is one of `text`, `buffer`, `blob`, `uri`.
Setting `text` first and then set `uri` will clear the `text field.

```python
d = Document(text='hello world')
d.uri = 'https://jina.ai/'
assert not d.text  # True

d = Document(content='https://jina.ai')
assert d.uri == 'https://jina.ai'  # True
assert not d.text  # True
d.text = 'hello world'

assert d.content == 'hello world'  # True
assert not d.uri  # True
```

#### Conversion between `doc.content`

You can use the following methods to convert between `.uri`, `.text`, `.buffer`, `.blob`:

```python
doc.convert_buffer_to_blob()
doc.convert_blob_to_buffer()
doc.convert_uri_to_buffer()
doc.convert_buffer_to_uri()
doc.convert_text_to_uri()
doc.convert_uri_to_text()
```

You can convert a URI to data URI (a data in-line URI scheme) using `doc.convert_uri_to_datauri()`. This will fetch the
resource and make it inline.

In particular, when you work with the image `Document`, there are some extra helpers that enables more conversion.

```python
doc.convert_image_buffer_to_blob()
doc.convert_image_blob_to_uri()
doc.convert_image_uri_to_blob()
doc.convert_image_datauri_to_blob()
```

##### Set Embedding

Embedding is the high-dimensional representation of a `Document`. You can assign any Numpy `ndarray` as its embedding.

```python
import numpy as np
from jina import Document

d1 = Document(embedding=np.array([1, 2, 3]))
d2 = Document(embedding=np.array([[1, 2, 3], [4, 5, 6]]))
```

#### Construct with Multiple Attributes

##### Meta Attributes

|     |     |
| --- | --- |
| `doc.tags` | A structured data value, consisting of field which map to dynamically typed values |
| `doc.id` | A hexdigest that represents a unique document ID |
| `doc.weight` | The weight of this document |
| `doc.mime_type` | The mime type of this document |
| `doc.location` | The position of the doc, could be start and end index of a string; could be x,y (top, left) coordinate of an image crop; could be timestamp of an audio clip |
| `doc.offset` | The offset of this doc in the previous granularity document|
| `doc.modality` | An identifier to the modality this document belongs to|

You can assign multiple attributes in the constructor via:

```python
from jina import Document

d = Document(content='hello',
             uri='https://jina.ai',
             mime_type='text/plain',
             granularity=1,
             adjacency=3,
             tags={'foo': 'bar'})
```

```text
<jina.types.document.Document id=e01a53bc-aedb-11eb-88e6-1e008a366d48 uri=https://jina.ai mimeType=text/plain tags={'foo': 'bar'} text=hello granularity=1 adjacency=3 at 6317309200>
```

#### Construct from Dict or JSON String

You can build a `Document` from `dict` or a JSON string.

```python
from jina import Document
import json

d = {'id': 'hello123', 'content': 'world'}
d1 = Document(d)

d = json.dumps({'id': 'hello123', 'content': 'world'})
d2 = Document(d)
```

##### Parsing Unrecognized Fields

Unrecognized fields in Dict/JSON string are automatically put into `.tags` field.

```python
from jina import Document

d1 = Document({'id': 'hello123', 'foo': 'bar'})
```

```text
<jina.types.document.Document id=hello123 tags={'foo': 'bar'} at 6320791056>
```

You can use `field_resolver` to map the external field name to `Document` attributes, e.g.

```python
from jina import Document

d1 = Document({'id': 'hello123', 'foo': 'bar'}, field_resolver={'foo': 'content'})
```

```text
<jina.types.document.Document id=hello123 mimeType=text/plain text=bar at 6246985488>
```

#### Construct from Another `Document`

Assigning a `Document` object to another `Document` object will make a shallow copy.

```python
from jina import Document

d = Document(content='hello, world!')
d1 = d

assert id(d) == id(d1)  # True
```

To make a deep copy, use `copy=True`,

```python
d1 = Document(d, copy=True)

assert id(d) == id(d1)  # False
```

You can update a `Document` partially according to another source `Document`,

```python
from jina import Document

s = Document(
  id='🐲',
  content='hello-world',
  tags={'a': 'b'},
  chunks=[Document(id='🐢')],
)
d = Document(
  id='🐦',
  content='goodbye-world',
  tags={'c': 'd'},
  chunks=[Document(id='🐯')],
)

# only update `id` field
d.update(s, include_fields=('id',))

# only preserve `id` field
d.update(s, exclude_fields=('id',))
```

#### Construct from Generator

You can also construct `Document` from some generator:

|     |     |
| --- | --- |
| `Document.from_ndjson()` | Yield `Document` from a line-based JSON file, each line is a `Document` object |
| `Document.from_csv()` | Yield `Document` from a CSV file, each line is a `Document` object |
| `Document.from_files()` | Yield `Document` from a glob files, each file is a `Document` object |
| `Document.from_ndarray()` | Yield `Document` from a `ndarray`, each row (depending on `axis`) is a `Document` object |

Using generator is sometimes less memory demanding, as it does not load build all Document objects in one shot.

### Serialize `Document`

You can serialize a `Document` into JSON string or Python dict or binary string via

```python
from jina import Document

d = Document(content='hello, world')
d.json()
```

```
{
  "id": "6a1c7f34-aef7-11eb-b075-1e008a366d48",
  "mimeType": "text/plain",
  "text": "hello world"
}
```

```python
d.dict()
```

```
{'id': '6a1c7f34-aef7-11eb-b075-1e008a366d48', 'mimeType': 'text/plain', 'text': 'hello world'}
```

```python
d.binary_str()
```

```
b'\n$6a1c7f34-aef7-11eb-b075-1e008a366d48R\ntext/plainj\x0bhello world'
```

### Add Recursion to `Document`

#### Recursive Attributes

`Document` can be recurred in both horizontal & vertical way.

|     |     |
| --- | --- |
| `doc.chunks` | The list of sub-documents of this document. They have `granularity + 1` but same `adjacency` |
| `doc.matches` | The list of matched documents of this document. They have `adjacency + 1` but same `granularity` |
|  `doc.granularity` | The recursion "depth" of the recursive chunks structure |
|  `doc.adjacency` | The recursion "width" of the recursive match structure |

You can add **chunks** (sub-document) and **matches** (neighbour-document) to a `Document` via the following ways:

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

Note that both `doc.chunks` and `doc.matches` return `DocumentArray`, which we will introduce later.

### Visualize `Document`

To better see the Document's recursive structure, you can use `.plot()` function. If you are using JupyterLab/Notebook,
all `Document` objects will be auto-rendered.

<table>
  <tr>
    <td>

```python
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

</td>
<td>
<img src="https://github.com/jina-ai/jina/blob/master/.github/images/four-symbol-docs.svg?raw=true"/>
</td>
</tr>
</table>

### Add Relevancy to `Document`

#### Relevance Attributes

|     |     |
| --- | --- |
| `doc.score` | The relevance information of this document |
| `doc.evaluations` | The evaluation information of this document |

You can add relevance score to a `Document` object via:

```python
from jina import Document
d = Document()
d.score.value = 0.96
d.score.description = 'cosine similarity'
d.score.op_name = 'cosine()'
```

```text
<jina.types.document.Document id=0a986c50-aeff-11eb-84c1-1e008a366d48 score={'value': 0.96, 'opName': 'cosine()', 'description': 'cosine similarity'} at 6281686928>
```

Score information is often used jointly with `matches`. For example, you often see the indexer adding `matches` as
follows:

```python
from jina import Document

# some query document
q = Document()
# get match document `m`
m = Document()
m.score.value = 0.96
q.matches.append(m)
```

## `DocumentArray` API

`DocumentArray` is a list of `Document` objects. You can construct, delete, insert, sort, traverse a `DocumentArray`
like a Python `list`.

Methods supported by `DocumentArray`:

| | |
|--- |--- |
| Python `list`-like interface | `__getitem__`, `__setitem__`, `__delitem__`, `__len__`, `insert`, `append`, `reverse`, `extend`, `pop`, `remove`, `__iadd__`, `__add__`, `__iter__`, `__clear__`, `sort` |
| Persistence | `save`, `load` |
| Advanced getters | `get_attributes`, `get_attributes_with_docs` |

### Construct `DocumentArray`

One can construct a `DocumentArray` from iterable of `Document` via:

```python
from jina import DocumentArray, Document

# from list
da1 = DocumentArray([Document(), Document()])

# from generator
da2 = DocumentArray((Document() for _ in range(10)))

# from another `DocumentArray`
da3 = DocumentArray(da2)
```

### Persistence via `save()`/`load()`

To save all elements in a `DocumentArray` in a JSON lines format:

```python
from jina import DocumentArray, Document

da = DocumentArray([Document(), Document()])

da.save('data.json')
da1 = DocumentArray.load('data.json')
```

### Access Element

You can access a `Document` in the `DocumentArray` via integer index, string `id` and `slice` indices.

```python
from jina import DocumentArray, Document

da = DocumentArray([Document(id='hello'), Document(id='world'), Document(id='goodbye')])

da[0]
# <jina.types.document.Document id=hello content_hash= granularity=0 adjacency=0 parent_id= chunks=[] weight=0.0 siblings=0 matches=[] mime_type= location=[] offset=0 modality= evaluations=[] at 5732567632>

da['world']
# <jina.types.document.Document id=world content_hash= granularity=0 adjacency=0 parent_id= chunks=[] weight=0.0 siblings=0 matches=[] mime_type= location=[] offset=0 modality= evaluations=[] at 5732565712>

da[1:2]  
# <jina.types.arrays.document.DocumentArray length=1 at 5732566608>
```


### Get Attributes in Bulk

`DocumentArray` implements powerful getters that allows one to fetch multiple attributes from the documents it contains
in one-shot.

```python
import numpy as np

from jina import DocumentArray, Document

da = DocumentArray([Document(id=1, text='hello', embedding=np.array([1, 2, 3])),
                    Document(id=2, text='goodbye', embedding=np.array([4, 5, 6])),
                    Document(id=3, text='world', embedding=np.array([7, 8, 9]))])

da.get_attributes('id', 'text', 'embedding')
```

```text
[('1', '2', '3'), ('hello', 'goodbye', 'world'), (array([1, 2, 3]), array([4, 5, 6]), array([7, 8, 9]))]
```

This can be very useful when extracting a batch of embeddings,

```python
import numpy as np

np.stack(da.get_attributes('embedding'))
```

```text
[[1 2 3]
 [4 5 6]
 [7 8 9]]
```
