Document, Executor, and Flow are the three fundamental concepts in Jina.

- [**Document**](Document.md) is the basic data type in Jina;
- [**Executor**](Executor.md) is how Jina processes Documents;
- [**Flow**](Flow.md) is how Jina streamlines and scales Executors.

*Learn them all, nothing more, you are good to go.*

---

# Cookbook on `Document`/`DocumentArray` 2.0 API

`Document` is the basic data type that Jina operates with. Text, picture, video, audio, image or 3D mesh: They are
all `Document`s in Jina.

`DocumentArray` is a sequence container of `Document`s. It is the first-class citizen of `Executor`, serving as the Executor's input
and output.

You could say `Document` is to Jina is what `np.float` is to Numpy, and `DocumentArray` is similar to `np.ndarray`.

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
Table of Contents

- [Minimum working example](#minimum-working-example)
- [`Document` API](#document-api)
  - [`Document` Attributes](#document-attributes)
    - [Set & Unset Attributes](#set--unset-attributes)
  - [Construct `Document`](#construct-document)
    - [Exclusivity of `doc.content`](#exclusivity-of-doccontent)
    - [Conversion between `doc.content`](#conversion-between-doccontent)
    - [Support for Sparse arrays](#support-for-sparse-arrays)
    - [Construct with Multiple Attributes](#construct-with-multiple-attributes)
    - [Construct from Dict or JSON String](#construct-from-dict-or-json-string)
    - [Construct from Another `Document`](#construct-from-another-document)
    - [Construct from JSON, CSV, `ndarray` and Files](#construct-from-json-csv-ndarray-and-files)
  - [Serialize `Document`](#serialize-document)
  - [Add Recursion to `Document`](#add-recursion-to-document)
    - [Recursive Attributes](#recursive-attributes)
  - [Represent `Document` as Dictionary or JSON](#represent-document-as-dictionary-or-json)
  - [Visualize `Document`](#visualize-document)
  - [Add Relevancy to `Document`s](#add-relevancy-to-documents)
    - [Relevance Attributes](#relevance-attributes)
- [`DocumentArray` API](#documentarray-api)
  - [Construct `DocumentArray`](#construct-documentarray)
  - [Persistence via `save()`/`load()`](#persistence-via-saveload)
  - [Access Element](#access-element)
  - [Traverse Elements](#traverse-elements)
  - [Sort Elements](#sort-elements)
  - [Filter Elements](#filter-elements)
  - [Use `itertools` on `DocumentArray`](#use-itertools-on-documentarray)
  - [Get Attributes in Bulk](#get-attributes-in-bulk)
  - [Access nested attributes from tags](#access-nested-attributes-from-tags)
- [`DocumentArrayMemmap` API](#documentarraymemmap-api)
  - [Create `DocumentArrayMemmap` object](#create-documentarraymemmap-object)
  - [Add Documents to `DocumentArrayMemmap` object](#add-documents-to-documentarraymemmap-object)
  - [Clear a `DocumentArrayMemmap` object](#clear-a-documentarraymemmap-object)
    - [Pruning](#pruning)
  - [Mutable sequence with "read-only" elements](#mutable-sequence-with-read-only-elements)
  - [Side-by-side vs. `DocumentArray`](#side-by-side-vs-documentarray)
  - [Convert between `DocumentArray` and `DocumentArrayMemmap`](#convert-between-documentarray-and-documentarraymemmap)
  - [Maintaining Consistency via `.reload()`](#maintaining-consistency-via-reload)

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
| Meta attributes | `.id`, `.weight`, `.mime_type`, `.location`, `.tags`, `.offset`, `.modality`, `siblings` |
| Recursive attributes | `.chunks`, `.matches`, `.granularity`, `.adjacency` |
| Relevance attributes | `.score`, `.evaluations` |

#### Set & Unset Attributes

Set a attribute:

```python
from jina import Document

d = Document()
d.text = 'hello world'
```

```text
<jina.types.document.Document id=9badabb6-b9e9-11eb-993c-1e008a366d49 mime_type=text/plain text=hello world at 4444621648>
```

Unset a attribute:

```python
d.pop('text')
```

```text
<jina.types.document.Document id=cdf1dea8-b9e9-11eb-8fd8-1e008a366d49 mime_type=text/plain at 4490447504>
```

Unset multiple attributes:

```python
d.pop('text', 'id', 'mime_type')
```

```text
<jina.types.document.Document at 5668344144>
```

### Construct `Document`

##### Content Attributes

|     |     |
| --- | --- |
| `doc.buffer` | The raw binary content of this Document |
| `doc.blob` | The `ndarray` of the image/audio/video Document |
| `doc.text` | The text info of the Document |
| `doc.uri` | A uri of the Document could be: a local file path, a remote url starts with http or https or data URI scheme |
| `doc.content` | One of the above non-empty field |
| `doc.embedding` | The embedding `ndarray` of this Document |

You can assign `str`, `ndarray`, `buffer` or `uri` to a `Document`.

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

The content will be automatically assigned to either the `text`, `buffer`, `blob`, or `uri` fields. `id` and `mime_type` are
auto-generated when not given.

You can get a visualization of a `Document` object in Jupyter Notebook or by calling `.plot()`.

<img src="https://mermaid.ink/svg/JSV7aW5pdDogeyd0aGVtZSc6ICdiYXNlJywgJ3RoZW1lVmFyaWFibGVzJzogeyAncHJpbWFyeUNvbG9yJzogJyNGRkM2NjYnfX19JSUKICAgICAgICAgICAgICAgICAgICBjbGFzc0RpYWdyYW0KICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgY2xhc3MgZDY5fkRvY3VtZW50fnsKK2lkIGU4MDY0MjdlLWEKK21pbWVfdHlwZSB0ZXh0L3BsYWluCit0ZXh0IGhlbGxvCn0="/><img src="https://mermaid.ink/svg/JSV7aW5pdDogeyd0aGVtZSc6ICdiYXNlJywgJ3RoZW1lVmFyaWFibGVzJzogeyAncHJpbWFyeUNvbG9yJzogJyNGRkM2NjYnfX19JSUKICAgICAgICAgICAgICAgICAgICBjbGFzc0RpYWdyYW0KICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgY2xhc3MgZDczfkRvY3VtZW50fnsKK2lkIGZmZTQzMmFjLWEKK2J1ZmZlciBEREU9CittaW1lX3R5cGUgdGV4dC9wbGFpbgp9"/><img src="https://mermaid.ink/svg/JSV7aW5pdDogeyd0aGVtZSc6ICdiYXNlJywgJ3RoZW1lVmFyaWFibGVzJzogeyAncHJpbWFyeUNvbG9yJzogJyNGRkM2NjYnfX19JSUKICAgICAgICAgICAgICAgICAgICBjbGFzc0RpYWdyYW0KICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgY2xhc3MgZDJmfkRvY3VtZW50fnsKK2lkIDAzOWVmMzE0LWEKK2Jsb2IoPGNsYXNzICdudW1weS5uZGFycmF5Jz4pCn0="/><img src="https://mermaid.ink/svg/JSV7aW5pdDogeyd0aGVtZSc6ICdiYXNlJywgJ3RoZW1lVmFyaWFibGVzJzogeyAncHJpbWFyeUNvbG9yJzogJyNGRkM2NjYnfX19JSUKICAgICAgICAgICAgICAgICAgICBjbGFzc0RpYWdyYW0KICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgY2xhc3MgMjRmfkRvY3VtZW50fnsKK2lkIDA2YTE2OGY4LWEKK3VyaSBodHRwczovL3N0CittaW1lX3R5cGUgaW1hZ2UvcG5nCn0="/>

#### Exclusivity of `doc.content`

![](../doc.content.svg?raw=true)

Note that one `Document` can only contain one type of `content`: it is either `text`, `buffer`, `blob` or `uri`.
Setting `text` first and then setting `uri` will clear the `text` field.

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

You can use the following methods to convert between `.uri`, `.text`, `.buffer` and `.blob`:

```python
doc.convert_buffer_to_blob()
doc.convert_blob_to_buffer()
doc.convert_uri_to_buffer()
doc.convert_buffer_to_uri()
doc.convert_text_to_uri()
doc.convert_uri_to_text()
```

You can convert a URI to a data URI (a data in-line URI scheme) using `doc.convert_uri_to_datauri()`. This will fetch the
resource and make it inline.

In particular, when you work with an image `Document`, there are some extra helpers that enable more conversion:

```python
doc.convert_image_buffer_to_blob()
doc.convert_image_blob_to_uri()
doc.convert_image_uri_to_blob()
doc.convert_image_datauri_to_blob()
```

##### Set Embedding

An embedding is a high-dimensional representation of a `Document`. You can assign any Numpy `ndarray` as a `Document`'s embedding.

```python
import numpy as np
from jina import Document

d1 = Document(embedding=np.array([1, 2, 3]))
d2 = Document(embedding=np.array([[1, 2, 3], [4, 5, 6]]))
```

#### Support for Sparse arrays

 Scipy sparse array (`coo_matrix, bsr_matrix, csr_matrix, csc_matrix`)  are supported as both `embedding` or `blob` :

```python
import scipy.sparse as sp 

d1 = Document(embedding=sp.coo_matrix([0,0,0,1,0]))
d2 = Document(embedding=sp.csr_matrix([0,0,0,1,0]))
d3 = Document(embedding=sp.bsr_matrix([0,0,0,1,0]))
d4 = Document(embedding=sp.csc_matrix([0,0,0,1,0]))

d5 = Document(blob=sp.coo_matrix([0,0,0,1,0]))
d6 = Document(blob=sp.csr_matrix([0,0,0,1,0]))
d7 = Document(blob=sp.bsr_matrix([0,0,0,1,0]))
d8 = Document(blob=sp.csc_matrix([0,0,0,1,0]))
```

Tensorflow and Pytorch sparse arrays are also supported

```python
import torch
import tensorflow as tf

indices = [[0, 0], [1, 2]]
values = [1, 2]
dense_shape = [3, 4]

d1 = Document(embedding=torch.sparse_coo_tensor(indices, values, dense_shape))
d2 = Document(embedding=tf.SparseTensor(indices, values, dense_shape))
d3 = Document(blob=torch.sparse_coo_tensor(indices, values, dense_shape))
d4 = Document(blob=tf.SparseTensor(indices, values, dense_shape))
```

#### Construct with Multiple Attributes

##### Meta Attributes

|     |     |
| --- | --- |
| `doc.tags` | A structured data value, consisting of fields which map to dynamically typed values |
| `doc.id` | A hexdigest that represents a unique Document ID |
| `doc.weight` | The weight of the Document |
| `doc.mime_type` | The mime type of the Document |
| `doc.location` | The position of the Document. This could be start and end index of a string; x,y (top, left) coordinates of an image crop; timestamp of an audio clip, etc |
| `doc.offset` | The offset of the Document in the previous granularity Document|
| `doc.modality` | An identifier of the modality the Document belongs to|

You can assign multiple attributes in the constructor via:

```python
from jina import Document

d = Document(uri='https://jina.ai',
             mime_type='text/plain',
             granularity=1,
             adjacency=3,
             tags={'foo': 'bar'})
```

```text
<jina.types.document.Document id=e01a53bc-aedb-11eb-88e6-1e008a366d48 uri=https://jina.ai mimeType=text/plain tags={'foo': 'bar'} granularity=1 adjacency=3 at 6317309200>
```

#### Construct from Dict or JSON String

You can build a `Document` from a `dict` or JSON string:

```python
from jina import Document
import json

d = {'id': 'hello123', 'content': 'world'}
d1 = Document(d)

d = json.dumps({'id': 'hello123', 'content': 'world'})
d2 = Document(d)
```

##### Parsing Unrecognized Fields

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

#### Construct from Another `Document`

Assigning a `Document` object to another `Document` object will make a shallow copy:

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

You can partially update a `Document` according to another source `Document`:

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
d.update(s, fields=['id'])

# update all fields. `tags` field as `dict` will be merged.
d.update(s)
```

#### Construct from JSON, CSV, `ndarray` and Files

The `jina.types.document.generators` module let you construct `Document` from common file types such as JSON, CSV, `ndarray` and text files. The following
functions will give a generator of `Document`, where each `Document` object corresponds to a line/row in the original
format:

|     |     |
| --- | --- |
| `from_ndjson()` | Yield `Document` from a line-based JSON file. Each line is a `Document` object |
| `from_csv()` | Yield `Document` from a CSV file. Each line is a `Document` object |
| `from_files()` | Yield `Document` from a glob files. Each file is a `Document` object |
| `from_ndarray()` | Yield `Document` from a `ndarray`. Each row (depending on `axis`) is a `Document` object |

Using a generator is sometimes less memory-demanding, as it does not load/build all Document objects in one shot.

To convert the generator to `DocumentArray` use:

```python
from jina import DocumentArray
from jina.types.document.generators import from_files

DocumentArray(from_files('/*.png'))
```

### Serialize `Document`

You can serialize a `Document` into JSON string or Python dict or binary string:

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

`Document` can be recursed both horizontally and vertically:

|     |     |
| --- | --- |
| `doc.chunks` | The list of sub-Documents of this Document. They have `granularity + 1` but same `adjacency` |
| `doc.matches` | The list of matched Documents of this Document. They have `adjacency + 1` but same `granularity` |
|  `doc.granularity` | The recursion "depth" of the recursive chunks structure |
|  `doc.adjacency` | The recursion "width" of the recursive match structure |

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

Note that both `doc.chunks` and `doc.matches` return `DocumentArray`, which we will introduce later.

### Represent `Document` as Dictionary or JSON

Any `Document` can be converted into a `Python dictionary` or into `Json string` by calling their `.dict()` or `.json()` methods. 

```python
import pprint
import numpy as np

from jina import Document

d0 = Document(id='🐲identifier', text='I am a Jina Document', tags={'cool': True}, embedding=np.array([0, 0]))
pprint.pprint(d0.dict())
pprint.pprint(d0.json())
```

```text
{'embedding': {'dense': {'buffer': 'AAAAAAAAAAAAAAAAAAAAAA==',
                         'dtype': '<i8',
                         'shape': [2]}},
 'id': '🐲identifier',
 'mime_type': 'text/plain',
 'tags': {'cool': True},
 'text': 'I am a Jina Document'}
('{\n'
 '  "embedding": {\n'
 '    "dense": {\n'
 '      "buffer": "AAAAAAAAAAAAAAAAAAAAAA==",\n'
 '      "dtype": "<i8",\n'
 '      "shape": [\n'
 '        2\n'
 '      ]\n'
 '    }\n'
 '  },\n'
 '  "id": "identifier",\n'
 '  "mime_type": "text/plain",\n'
 '  "tags": {\n'
 '    "cool": true\n'
 '  },\n'
 '  "text": "I am a Jina Document"\n'
 '}')
```

As it can be observed, the output seems quite noisy when representing the `embedding`. This is because Jina `Document` stores `embeddings` in an `inner` structure
supported by `protobuf`. In order to have a nicer representation of the `embeddings` and any `ndarray` field, you can call `dict` and `json` with the option `prettify_ndarrays=True`.

```python
import pprint
import numpy as np

from jina import Document

d0 = Document(id='🐲identifier', text='I am a Jina Document', tags={'cool': True}, embedding=np.array([0, 0]))
pprint.pprint(d0.dict(prettify_ndarrays=True))
pprint.pprint(d0.json(prettify_ndarrays=True))
```

```text
{'embedding': [0, 0],
 'id': '🐲identifier',
 'mime_type': 'text/plain',
 'tags': {'cool': True},
 'text': 'I am a Jina Document'}

('{"embedding": [0, 0], "id": "identifier", "mime_type": '
 '"text/plain", "tags": {"cool": true}, "text": "I am a Jina Document"}')
```

This can be useful to understand the contents of the `Document` and to send to backends that can process vectors as `lists` of values.

### Visualize `Document`

To better see the Document's recursive structure, you can use `.plot()` function. If you are using JupyterLab/Notebook,
all `Document` objects will be auto-rendered:

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

### Add Relevancy to `Document`s

#### Relevance Attributes

|     |     |
| --- | --- |
| `doc.scores` | The relevance information of this Document. A dict-like structure supporting storing different metrics |
| `doc.evaluations` | The evaluation information of this Document. A dict-like structure supporting storing different metrics |

You can add a relevance score to a `Document` object via:

```python
from jina import Document

d = Document()
d.scores['cosine similarity'] = 0.96
d.scores['cosine similarity'].description = 'cosine similarity'
d.scores['cosine similarity'].op_name = 'cosine()'
d.evaluations['recall'] = 0.56
d.evaluations['recall'].description = 'recall at 10'
d.evaluations['recall'].op_name = 'recall()'
d
```

```text
<jina.types.document.Document id=6c4db2c8-cdf1-11eb-be5d-e86a64801cb1 scores={'values': {'cosine similarity': {'value': 0.96, 'op_name': 'cosine()', 'description': 'cosine similarity'}}} evaluations={'values': {'recall': {'value': 0.56, 'op_name': 'recall()', 'description': 'recall at 10'}}} at 140003211429776>```
```

Score information is often used jointly with `matches`. For example, you often see the indexer adding `matches` as
follows:

```python
from jina import Document

# some query Document
q = Document()
# get match Document `m`
m = Document()
m.scores['metric'] = 0.96
q.matches.append(m)
```

```text
<jina.types.document.Document id=1aaba345-cdf1-11eb-be5d-e86a64801cb1 adjacency=1 scores={'values': {'metric': {'value': 0.96, 'ref_id': '1aaba344-cdf1-11eb-be5d-e86a64801cb1'}}} at 140001502011856>
```

These attributes (`scores` and `evaluations`) provide a dict-like interface that lets access all its elements:
```python
from jina import Document

d = Document()
d.evaluations['precision'] = 1.0
d.evaluations['precision'].description = 'precision at 10'
d.evaluations['precision'].op_name = 'precision()'
d.evaluations['recall'] = 0.5
d.evaluations['recall'].description = 'recall at 10'
d.evaluations['recall'].op_name = 'recall()'
for evaluation_key, evaluation_score in d.evaluations.items():
    print(f' {evaluation_key} => {evaluation_score.description}: {evaluation_score.value}') 
```

```text
 precision => precision at 10: 1.0
 recall => recall at 10: 0.5
```

## `DocumentArray` API

A `DocumentArray` is a list of `Document` objects. You can construct, delete, insert, sort and traverse a `DocumentArray`
like a Python `list`.

Methods supported by `DocumentArray`:

| | |
|--- |--- |
| Python `list`-like interface | `__getitem__`, `__setitem__`, `__delitem__`, `__len__`, `insert`, `append`, `reverse`, `extend`, `__iadd__`, `__add__`, `__iter__`, `clear`, `sort` |
| Persistence | `save`, `load` |
| Advanced getters | `get_attributes`, `get_attributes_with_docs`, `traverse_flat`, `traverse` |

### Construct `DocumentArray`

You can construct a `DocumentArray` from an iterable of `Document`s:

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

To save all elements in a `DocumentArray` in a JSON line format:

```python
from jina import DocumentArray, Document

da = DocumentArray([Document(), Document()])

da.save('data.json')
da1 = DocumentArray.load('data.json')
```

`DocumentArray` can be also stored in binary format, which is much faster and yields smaller file:

```python
from jina import DocumentArray, Document

da = DocumentArray([Document(), Document()])

da.save('data.bin', file_format='binary')
da1 = DocumentArray.load('data.bin', file_format='binary')
```

### Access Element

You can access a `Document` in the `DocumentArray` via integer index, string `id` or `slice` indices:

```python
from jina import DocumentArray, Document

da = DocumentArray([Document(id='hello'), Document(id='world'), Document(id='goodbye')])

da[0]
# <jina.types.document.Document id=hello at 5699749904>

da['world']
# <jina.types.document.Document id=world at 5736614992>

da[1:2]
# <jina.types.arrays.document.DocumentArray length=1 at 5705863632>
```

### Traverse Elements
The following graphic illustrates the recursive `Document` structure. 
Every `Document` can have multiple `Chunks` and `Matches`.
`Chunks` and `Matches` are `Documents` as well.

<img src="https://hanxiao.io/2020/08/28/What-s-New-in-Jina-v0-5/blog-post-v050-protobuf-documents.jpg">

In most of the cases, you want to iterate through a certain level of documents. 
`DocumentArray.traverse` can be used for that by providing custom paths.
As return value you get a generator which generates `DocumentArrays` matching the provided traversal paths.
Let's assume you have the following `Document` structure:
```python
from jina import DocumentArray, Document

da = DocumentArray([
    Document(id='r1', chunks=[
        Document(id='c1', matches=[
                Document(id='c1c1m1'),
        ]),
        Document(id='c2', chunks=[
            Document(id='c2c1', matches=[
                Document(id='c2c1m1'),
                Document(id='c2c1m2')
            ]),
            Document(id='c2c2'),
        ]),
        Document(id='c3')
    ]),
    Document(id='r2')
])
```
When calling `da.traverse(['cm', 'ccm'])` you get a generator over two `DocumentArrays`. 
The first `DocumentArray` contains the `Matches` of the `Chunks` and the second `DocumentArray` contains the `Matches` of the `Chunks` of the `Chunks`.
The following `DocumentArrays` are emitted from the generator:
```python
from jina import Document
from jina.types.arrays import MatchArray

MatchArray([Document(id='c1c1m1', adjacency=1)], reference_doc=da['r1'].chunks['c1'])
MatchArray([], reference_doc=da['r1'].chunks['c2'])
MatchArray([], reference_doc=da['r1'].chunks['c3'])
MatchArray([Document(id='c2c1m1', adjacency=1),Document(id='c2c1m2', adjacency=1)], reference_doc=da['r1'].chunks['c2'].chunks['c2c1'])
MatchArray([], reference_doc=da['r1'].chunks['c2'].chunks['c2c2'])
```

`DocumentArray.traverse_flat` is doing the same but flattens all `DocumentArrays` in the generator. 
When calling `da.traverse_flat(['cm', 'ccm'])` the result in our example will be the following:

```python
from jina import Document, DocumentArray
assert da.traverse_flat(['cm', 'ccm']) == DocumentArray([
    Document(id='c1c1m1', adjacency=1),
    Document(id='c2c1m1', adjacency=1),
    Document(id='c2c1m2', adjacency=1)
])
```

`DocumentArray.traverse_flat_per_path` is a further method for `Document` traversal.
It works like `DocumentArray.traverse_flat` but groups the `Documents` into `DocumentArrays` based on the traversal path.
When calling `da.traverse_flat_per_path(['cm', 'ccm'])`, the resulting generator emits the following `DocumentArrays`:
```python
from jina import Document, DocumentArray
DocumentArray([
    Document(id='c1c1m1', adjacency=1),
])
DocumentArray([
    Document(id='c2c1m1', adjacency=1),
    Document(id='c2c1m2', adjacency=1)
])
```


### Sort Elements

`DocumentArray` is a subclass of `MutableSequence`, therefore you can use built-in Python `sort` to sort elements in
a `DocumentArray` object, e.g.

```python
from jina import DocumentArray, Document

da = DocumentArray(
    [
        Document(tags={'id': 1}),
        Document(tags={'id': 2}),
        Document(tags={'id': 3})
    ]
)

da.sort(key=lambda d: d.tags['id'], reverse=True)
print(da)
```

To sort elements in `da` in-place, using `tags[id]` value in a descending manner: 

```text
<jina.types.arrays.document.DocumentArray length=3 at 5701440528>

{'id': '6a79982a-b6b0-11eb-8a66-1e008a366d49', 'tags': {'id': 3.0}},
{'id': '6a799744-b6b0-11eb-8a66-1e008a366d49', 'tags': {'id': 2.0}},
{'id': '6a799190-b6b0-11eb-8a66-1e008a366d49', 'tags': {'id': 1.0}}
```

### Filter Elements

You can use Python's [built-in `filter()`](https://docs.python.org/3/library/functions.html#filter) to filter elements in a `DocumentArray` object:

```python
from jina import DocumentArray, Document

da = DocumentArray([Document() for _ in range(6)])

for j in range(6):
    da[j].scores['metric'] = j

for d in filter(lambda d: d.scores['metric'].value > 2, da):
    print(d)
```

```text
{'id': 'b5fa4871-cdf1-11eb-be5d-e86a64801cb1', 'scores': {'values': {'metric': {'value': 3.0}}}}
{'id': 'b5fa4872-cdf1-11eb-be5d-e86a64801cb1', 'scores': {'values': {'metric': {'value': 4.0}}}}
{'id': 'b5fa4873-cdf1-11eb-be5d-e86a64801cb1', 'scores': {'values': {'metric': {'value': 5.0}}}}
```

You can build a `DocumentArray` object from the filtered results:

```python
from jina import DocumentArray, Document

da = DocumentArray([Document(weight=j) for j in range(6)])
da2 = DocumentArray(d for d in da if d.weight > 2)

print(da2)
```

```text
DocumentArray has 3 items:
{'id': '3bd0d298-b6da-11eb-b431-1e008a366d49', 'weight': 3.0},
{'id': '3bd0d324-b6da-11eb-b431-1e008a366d49', 'weight': 4.0},
{'id': '3bd0d392-b6da-11eb-b431-1e008a366d49', 'weight': 5.0}
```

### Use `itertools` on `DocumentArray`

As `DocumentArray` is an `Iterable`, you can also
use [Python's built-in `itertools` module](https://docs.python.org/3/library/itertools.html) on it. This enables
advanced "iterator algebra" on the `DocumentArray`.

For instance, you can group a `DocumentArray` by `parent_id`:

```python
from jina import DocumentArray, Document
from itertools import groupby

da = DocumentArray([Document(parent_id=f'{i % 2}') for i in range(6)])
groups = groupby(sorted(da, key=lambda d: d.parent_id), lambda d: d.parent_id)
for key, group in groups:
    key, len(list(group))
```

```text
('0', 3)
('1', 3)
```

### Get Attributes in Bulk

`DocumentArray` implements powerful getters that lets you fetch multiple attributes from the Documents it contains
in one-shot:

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

This can be very useful when extracting a batch of embeddings:

```python
import numpy as np

np.stack(da.get_attributes('embedding'))
```

```text
[[1 2 3]
 [4 5 6]
 [7 8 9]]
```

### Access nested attributes from tags

`Document` contains the `tags` field that can hold a map-like structure that can map arbitrary values.

```python
from jina import Document

doc = Document(tags={'dimensions': {'height': 5.0, 'weight': 10.0}})

doc.tags['dimensions']
```

```text
{'weight': 10.0, 'height': 5.0}
```

In order to provide easy access to nested fields, the `Document` allows to access attributes by composing the attribute 
qualified name with interlaced `__` symbols:

```python
from jina import Document

doc = Document(tags={'dimensions': {'height': 5.0, 'weight': 10.0}})

doc.tags__dimensions__weight
```

```text
10.0
```

This also allows to access nested metadata attributes in `bulk` from a `DocumentArray`.

```python
from jina import Document, DocumentArray

da = DocumentArray([Document(tags={'dimensions': {'height': 5.0, 'weight': 10.0}}) for _ in range(10)]) 

da.get_attributes('tags__dimensions__height', 'tags__dimensions__weight')
```

```text
[[5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0], [10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0]]
```

## `DocumentArrayMemmap` API

When your `DocumentArray` object contains a large number of `Document`, holding it in memory can be very demanding. You may want to use `DocumentArrayMemmap` to alleviate this issue. A `DocumentArrayMemmap` stores all Documents directly on the disk, while only keeps a small lookup table in memory. This lookup table contains the offset and length of each `Document`, hence it is much smaller than the full `DocumentArray`. Elements are loaded on-demand to memory during the access.

The next table show the speed and memory consumption when writing and reading 50,000 `Documents`.

|| `DocumentArrayMemmap` | `DocumentArray` |
|---|---|---|
|Write to disk | 0.62s | 0.71s |
|Read from disk | 0.11s | 0.20s |
|Memory usage | 20MB | 342MB |
|Disk storage | 14.3MB | 12.6MB |

### Create `DocumentArrayMemmap` object

```python
from jina.types.arrays.memmap import DocumentArrayMemmap

dam = DocumentArrayMemmap('./my-memmap')
```

### Add Documents to `DocumentArrayMemmap` object

```python
from jina.types.arrays.memmap import DocumentArrayMemmap
from jina import Document

d1 = Document(text='hello')
d2 = Document(text='world')

dam = DocumentArrayMemmap('./my-memmap')
dam.extend([d1, d2])
```

The `dam` object stores all future Documents into `./my-memmap`, there is no need to manually call `save`/`load`. In fact, `save`/`load` methods are not available in `DocumentArrayMemmap`.

### Clear a `DocumentArrayMemmap` object

To clear all contents in a `DocumentArrayMemmap` object, simply call `.clear()`. It will clean all content on disk.

#### Pruning

One may notice another method `.prune()` that shares similar semantics. `.prune()` method is designed for "post-optimizing" the on-disk data structure of `DocumentArrayMemmap` object. It can reduce the on-disk usage.

### Mutable sequence with "read-only" elements

The biggest caveat in `DocumentArrayMemmap` is that you can **not** modify element's attribute inplace. Though the `DocumentArrayMemmap` is mutable, each of its element is not. For example:

```python
from jina.types.arrays.memmap import DocumentArrayMemmap
from jina import Document

d1 = Document(text='hello')
d2 = Document(text='world')

dam = DocumentArrayMemmap('./my-memmap')
dam.extend([d1, d2])

dam[0].text = 'goodbye'

print(dam[0].text)
```

```text
hello
```

One can see the `text` field has not changed!

To update an existing `Document` in a `DocumentArrayMemmap`, you need to assign it to a new `Document` object.

```python
from jina.types.arrays.memmap import DocumentArrayMemmap
from jina import Document

d1 = Document(text='hello')
d2 = Document(text='world')

dam = DocumentArrayMemmap('./my-memmap')
dam.extend([d1, d2])

dam[0] = Document(text='goodbye')

for d in dam:
    print(d)
```

```text
{'id': '44a74b56-c821-11eb-8522-1e008a366d48', 'mime_type': 'text/plain', 'text': 'goodbye'}
{'id': '44a73562-c821-11eb-8522-1e008a366d48', 'mime_type': 'text/plain', 'text': 'world'}
```

### Side-by-side vs. `DocumentArray`

Accessing elements in `DocumentArrayMemmap` is _almost_ the same as `DocumentArray`, you can use integer/string index to access element; you can loop over a `DocumentArrayMemmap` to get all `Document`; you can use `get_attributes` or `traverse_flat` to achieve advanced traversal or getter.

This table summarizes the interfaces of `DocumentArrayMemmap` and `DocumentArray`:

|| `DocumentArrayMemmap` | `DocumentArray` |
|---|---|---|
| `__getitem__`, `__setitem__`, `__delitem__` (int) | ✅|✅|
| `__getitem__`, `__setitem__`, `__delitem__` (string) | ✅|✅|
| `__getitem__`, `__setitem__`, `__delitem__` (slice)  |❌ |✅|
| `__iter__` |✅|✅|
| `__contains__` |✅|✅|
| `__len__` | ✅|✅|
| `append` | ✅|✅|
| `extend` | ✅|✅|
| `traverse_flat`, `traverse` | ✅|✅|
| `get_attributes`, `get_attributes_with_docs` | ✅|✅|
| `insert` |❌ |✅|
| `reverse` (inplace) |❌ |✅|
| `sort` (inplace) | ❌|✅|
| `__add__`, `__iadd__` | ❌|✅|
| `__bool__` |✅|✅|
| `__eq__` |✅|✅|
| `save`, `load` |❌ unnecessary |✅|

### Convert between `DocumentArray` and `DocumentArrayMemmap`

```python
from jina import Document, DocumentArray
from jina.types.arrays.memmap import DocumentArrayMemmap

da = DocumentArray([Document(text='hello'), Document(text='world')])

# convert DocumentArray to DocumentArrayMemmap
dam = DocumentArrayMemmap('./my-memmap')
dam.extend(da)

# convert DocumentArrayMemmap to DocumentArray
da = DocumentArray(dam)
```


### Maintaining Consistency via `.reload()`

Considering two `DocumentArrayMemmap` objects that share the same on-disk storage `./memmap` but sit in different processes/threads. After some writing ops, the consistency of the lookup table may be corrupted, as each `DocumentArrayMemmap` object has its own version of lookup table in memory. `.reload()` method is for solving this issue:

```python
from jina.types.arrays.memmap import DocumentArrayMemmap
from jina import Document

d1 = Document(text='hello')
d2 = Document(text='world')

dam = DocumentArrayMemmap('./my-memmap')
dam2 = DocumentArrayMemmap('./my-memmap')

dam.extend([d1, d2])
assert len(dam) == 2
assert len(dam2) == 0

dam2.reload()
assert len(dam2) == 2

dam.clear()
assert len(dam) == 0
assert len(dam2) == 2

dam2.reload()
assert len(dam2) == 0
```