## Document API

### `Document` attributes

A `Document` object has the following attributes, which can be put into the following categories:

| Category | Attributes |
|---|---|
| Content attributes | `.buffer`, `.blob`, `.text`, `.uri`, `.content`, `.embedding` |
| Meta attributes | `.id`, `.parent_id`, `.weight`, `.mime_type`, `.content_type`, `.tags`, `.modality` |
| Recursive attributes | `.chunks`, `.matches`, `.granularity`, `.adjacency` |
| Relevance attributes | `.score`, `.evaluations` |

#### Set & Unset attributes

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

#### Access nested attributes from tags

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

### Construct `Document`

##### Content attributes

| Attribute | Description |
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
<jina.types.document.Document id=2ca74f1c-aed9-11eb-b791-1e008a366d48 buffer=DDE= at 6247702160>
<jina.types.document.Document id=2caab594-aed9-11eb-b791-1e008a366d48 blob={'dense': {'buffer': 'AQAAAAAAAAACAAAAAAAAAAMAAAAAAAAA', 'shape': [3], 'dtype': '<i8'}} at 6247702416>
<jina.types.document.Document id=4c008c40-af9f-11eb-bb84-1e008a366d49 uri=https://static.jina.ai/logo/core/notext/light/logo.png mimeType=image/png at 6252395600>
```

The content will be automatically assigned to either the `text`, `buffer`, `blob`, or `uri` fields. `id` and `mime_type`
are auto-generated when not given.

You can get a visualization of a `Document` object in Jupyter Notebook or by calling `.plot()`.

<img src="https://mermaid.ink/svg/JSV7aW5pdDogeyd0aGVtZSc6ICdiYXNlJywgJ3RoZW1lVmFyaWFibGVzJzogeyAncHJpbWFyeUNvbG9yJzogJyNGRkM2NjYnfX19JSUKICAgICAgICAgICAgICAgICAgICBjbGFzc0RpYWdyYW0KICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgY2xhc3MgZDY5fkRvY3VtZW50fnsKK2lkIGU4MDY0MjdlLWEKK21pbWVfdHlwZSB0ZXh0L3BsYWluCit0ZXh0IGhlbGxvCn0="/><img src="https://mermaid.ink/svg/JSV7aW5pdDogeyd0aGVtZSc6ICdiYXNlJywgJ3RoZW1lVmFyaWFibGVzJzogeyAncHJpbWFyeUNvbG9yJzogJyNGRkM2NjYnfX19JSUKICAgICAgICAgICAgICAgICAgICBjbGFzc0RpYWdyYW0KICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgY2xhc3MgZDczfkRvY3VtZW50fnsKK2lkIGZmZTQzMmFjLWEKK2J1ZmZlciBEREU9CittaW1lX3R5cGUgdGV4dC9wbGFpbgp9"/><img src="https://mermaid.ink/svg/JSV7aW5pdDogeyd0aGVtZSc6ICdiYXNlJywgJ3RoZW1lVmFyaWFibGVzJzogeyAncHJpbWFyeUNvbG9yJzogJyNGRkM2NjYnfX19JSUKICAgICAgICAgICAgICAgICAgICBjbGFzc0RpYWdyYW0KICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgY2xhc3MgZDJmfkRvY3VtZW50fnsKK2lkIDAzOWVmMzE0LWEKK2Jsb2IoPGNsYXNzICdudW1weS5uZGFycmF5Jz4pCn0="/><img src="https://mermaid.ink/svg/JSV7aW5pdDogeyd0aGVtZSc6ICdiYXNlJywgJ3RoZW1lVmFyaWFibGVzJzogeyAncHJpbWFyeUNvbG9yJzogJyNGRkM2NjYnfX19JSUKICAgICAgICAgICAgICAgICAgICBjbGFzc0RpYWdyYW0KICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgY2xhc3MgMjRmfkRvY3VtZW50fnsKK2lkIDA2YTE2OGY4LWEKK3VyaSBodHRwczovL3N0CittaW1lX3R5cGUgaW1hZ2UvcG5nCn0="/>

#### Exclusivity of `doc.content`

```{image} ../../../.github/2.0/doc.content.svg
:align: center
```

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

You can use `convert_content_to_uri` to convert the content to URI. This will determine the used `content_type` and use
the appropriate conversion method.

You can convert a URI to a data URI (a data in-line URI scheme) using `doc.convert_uri_to_datauri()`. This will fetch
the resource and make it inline.

In particular, when you work with an image `Document`, there are some extra helpers that enable more conversion:

```python
doc.convert_image_buffer_to_blob()
doc.convert_image_blob_to_uri()
doc.convert_image_uri_to_blob()
doc.convert_image_datauri_to_blob()
```

#### Set embedding

An embedding is a high-dimensional representation of a `Document`. You can assign any Numpy `ndarray` as a `Document`'s
embedding.

```python
import numpy as np
from jina import Document

d1 = Document(embedding=np.array([1, 2, 3]))
d2 = Document(embedding=np.array([[1, 2, 3], [4, 5, 6]]))
```

##### Support for sparse arrays

Scipy sparse array (`coo_matrix, bsr_matrix, csr_matrix, csc_matrix`)  are supported as both `embedding` or `blob` :

```python
import scipy.sparse as sp

d1 = Document(embedding=sp.coo_matrix([0, 0, 0, 1, 0]))
d2 = Document(embedding=sp.csr_matrix([0, 0, 0, 1, 0]))
d3 = Document(embedding=sp.bsr_matrix([0, 0, 0, 1, 0]))
d4 = Document(embedding=sp.csc_matrix([0, 0, 0, 1, 0]))

d5 = Document(blob=sp.coo_matrix([0, 0, 0, 1, 0]))
d6 = Document(blob=sp.csr_matrix([0, 0, 0, 1, 0]))
d7 = Document(blob=sp.bsr_matrix([0, 0, 0, 1, 0]))
d8 = Document(blob=sp.csc_matrix([0, 0, 0, 1, 0]))
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

#### Construct with multiple attributes

##### Meta attributes

| Attribute | Description |
| --- | --- |
| `doc.tags` | A structured data value, consisting of fields which map to dynamically typed values |
| `doc.id` | A hexdigest that represents a unique Document ID |
| `doc.parent_id` | A hexdigest that represents the document's parent id |
| `doc.weight` | The weight of the Document |
| `doc.mime_type` | The mime type of the Document |
| `doc.content_type` | The content type of the Document |
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

#### Construct from dict or JSON string

You can build a `Document` from a `dict` or JSON string:

```python
from jina import Document
import json

d = {'id': 'hello123', 'content': 'world'}
d1 = Document(d)

d = json.dumps({'id': 'hello123', 'content': 'world'})
d2 = Document(d)
```

##### Parsing unrecognized fields

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

#### Construct from another `Document`

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

#### Construct from JSON, CSV, `ndarray` and files

The `jina.types.document.generators` module let you construct `Document` from common file types such as JSON,
CSV, `ndarray` and text files. The following functions will give a generator of `Document`, where each `Document` object
corresponds to a line/row in the original format:

|     |     |
| --- | --- |
| `from_ndjson()` | Yield `Document` from a line-based JSON file. Each line is a `Document` object |
| `from_csv()` | Yield `Document` from a CSV file. Each line is a `Document` object |
| `from_files()` | Yield `Document` from a glob files. Each file is a `Document` object |
| `from_ndarray()` | Yield `Document` from a `ndarray`. Each row (depending on `axis`) is a `Document` object |
| `from_lines()` | Yield `Document` from lines, json and csv |

Using a generator is sometimes less memory-demanding, as it does not load/build all Document objects in one shot.

To convert the generator to `DocumentArray` use:

```python
from jina import DocumentArray
from jina.types.document.generators import from_files

DocumentArray(from_files('/*.png'))
```

### Construct Recursive `Document`

#### Recursive attributes

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

Note that both `doc.chunks` and `doc.matches` return `ChunkArray` and `MatchArray`, which are sub-classes
of [`DocumentArray`](#documentarray-api). We will introduce `DocumentArray later.


### Construct `GraphDocument`

`GraphDocument` is a subclass of `Document`. It's a special type of `Document` that adds functionality to let you work
with a `Document` as a `directed graph`. Chunks of the document represent the nodes of the graph. `GraphDocument` adds
graph-specific attributes (`nodes`, `adjacency` list, `edge_features`,...) and operations (`add_node`, `remove_node`
, `add_edge`, `remove_edge`,...)

#### `GraphDocument` constructor

`GraphDocument`'s constructor supports the same parameters as `Document`. It mainly adds one
parameter `force_undirected`. It's a boolean flag that, when set to `True`, forces the graph document to be undirected.

#### `GraphDocument` additional attributes

`GraphDocument` adds the following attributes to `Document`:

| Attribute | Description |
|---|---|
| `edge_features` | The dictionary of edge features, indexed by `edge_id` |
| `adjacency` | Adjacency list |
| `undirected` | Type of the graph: undirected or directed |
| `num_nodes` | Number of nodes in the graph |
| `num_edges` | Number of edges in the graph |
| `nodes` | The list of nodes. Equivalent to `chunks` |

#### `GraphDocument` methods

`GraphDocument` adds the following methods to `Document`:

* `add_node`: adds a document to the graoh:

```python
from jina.types.document.graph import GraphDocument
from jina import Document

graph = GraphDocument()
graph.add_node(Document(text='hello world'))
graph.nodes[0]
```

```text
<jina.types.document.Document id=8f9a60ce-f5d7-11eb-8383-c7034ef3edd4 mime_type=text/plain text=hello world granularity=1 parent_id=7ec9087c-f5d7-11eb-8383-c7034ef3edd4 at 140287929173088>
```

* `add_edge`: Adds an edge between 2 documents. If a document does not exist in the graph, it is added. You can also add
  dict features to the edge with parameter `features`

```python
from jina import Document
from jina.types.document.graph import GraphDocument

graph = GraphDocument()
d1 = Document(id='1', text='hello world')
d2 = Document(id='2', text='goodbye world')
graph.add_edge(d1, d2, features={"text": "both documents are linked"})
graph.nodes
```

```text
<jina.types.arrays.chunk.ChunkArray length=2 at 140039698424448>
```

You access the edge features using id1-id2 as key:

```python
graph.edge_features['1-2']
```

```text
<jina.types.struct.StructView text=both documents are linked at 140132368471280>
```

* `remove_edge` and `remove_node` allows removing an edge (between 2 nodes) and removing a node respectively.

* `GraphDocument` exposes methods that return node-specific information:

| method | Description |
|---|---|
| `get_out_degree` | node outdegree  |
| `get_in_degree` | node indegree |
| `get_outgoing_nodes` | Array of outgoing nodes for a given node |
| `get_incoming_nodes` | Array of incoming nodes for a given node |

```python
from jina import Document
from jina.types.document.graph import GraphDocument

graph = GraphDocument()
d1 = Document(id='1', text='hello world')
d2 = Document(id='2', text='goodbye world')
d3 = Document(id='3')
graph.add_edge(d1, d2)
graph.add_edge(d1, d3)

assert graph.get_out_degree(d1) == 2

graph.get_outgoing_nodes(d1)
```

```text
<jina.types.arrays.chunk.ChunkArray length=2 at 140689776342112>
```

* `to_dgl_graph`: returns a `dgl.DGLGraph` from the graph document.
* `load_from_dgl_graph`: returns a `GraphDocument` from a `dgl.DGLGraph`.


### Add relevancy to `Document`

#### Relevance attributes

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
<jina.types.document.Document id=6c4db2c8-cdf1-11eb-be5d-e86a64801cb1 scores={'values': {'cosine similarity': {'value': 0.96, 'op_name': 'cosine()', 'description': 'cosine similarity'}}} evaluations={'recall': {'value': 0.56, 'op_name': 'recall()', 'description': 'recall at 10'}} at 140003211429776>```
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
<jina.types.document.Document id=1aaba345-cdf1-11eb-be5d-e86a64801cb1 adjacency=1 scores={'values': {'metric': {'value': 0.96}}} at 140001502011856>
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


### Serialize `Document` to binary/`Dict`/JSON

You can serialize a `Document` into JSON string or Python dict or binary string:

```python
from jina import Document

d = Document(content='hello, world')
```

```python
d.binary_str()
```

```
b'\n$6a1c7f34-aef7-11eb-b075-1e008a366d48R\ntext/plainj\x0bhello world'
```

```python
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


In order to have a nicer representation of
the `embeddings` and any `ndarray` field, you can call `dict` and `json` with the option `prettify_ndarrays=True`.

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

This can be useful to understand the contents of the `Document` and to send to backends that can process vectors
as `lists` of values.


### Visualize `Document`

To better see the Document's recursive structure, you can use `.plot()` function. If you are using JupyterLab/Notebook,
all `Document` objects will be auto-rendered:


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


```{figure} ../../../.github/images/four-symbol-docs.svg
:align: center
```
