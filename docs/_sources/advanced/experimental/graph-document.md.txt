# Graph Document

`GraphDocument` is a subclass of `Document`. It's a special type of `Document` that adds functionality to let you work
with a `Document` as a `directed graph`. Chunks of the document represent the nodes of the graph. `GraphDocument` adds
graph-specific attributes (`nodes`, `adjacency` list, `edge_features`,...) and operations (`add_node`, `remove_node`
, `add_edge`, `remove_edge`,...)

## `GraphDocument` constructor

`GraphDocument`'s constructor supports the same parameters as `Document`. It mainly adds one
parameter `force_undirected`. It's a boolean flag that, when set to `True`, forces the graph document to be undirected.

## `GraphDocument` additional attributes

`GraphDocument` adds the following attributes to `Document`:

| Attribute | Description |
|---|---|
| `edge_features` | The dictionary of edge features, indexed by `edge_id` |
| `adjacency` | Adjacency list |
| `undirected` | Type of the graph: undirected or directed |
| `num_nodes` | Number of nodes in the graph |
| `num_edges` | Number of edges in the graph |
| `nodes` | The list of nodes. Equivalent to `chunks` |

## `GraphDocument` methods

`GraphDocument` adds the following methods to `Document`:

* `add_node`: adds a document to the graph:

```{code-block} python
---
emphasize-lines: 5
---
from jina.types.document.graph import GraphDocument
from jina import Document

gd = GraphDocument()
gd.add_node(Document(text='hello world'))
gd.nodes[0]
```

```text
<jina.types.document.Document id=8f9a60ce-f5d7-11eb-8383-c7034ef3edd4 mime_type=text/plain text=hello world granularity=1 parent_id=7ec9087c-f5d7-11eb-8383-c7034ef3edd4 at 140287929173088>
```

* `add_edge`: Adds an edge between 2 documents. If a document does not exist in the graph, it is added. You can also add
  dict features to the edge with parameter `features`

```{code-block} python
---
emphasize-lines: 7
---
from jina import Document
from jina.types.document.graph import GraphDocument

graph = GraphDocument()
d1 = Document(id='1', text='hello world')
d2 = Document(id='2', text='goodbye world')
gd.add_edge(d1, d2, features={"text": "both documents are linked"})
gd.nodes
```

```text
<jina.types.arrays.chunk.ChunkArray length=2 at 140039698424448>
```

You access the edge features using id1-id2 as key:

```python
gd.edge_features['1-2']
```

```text
<jina.types.struct.StructView text=both documents are linked at 140132368471280>
```

* `remove_edge` and `remove_node` allows removing an edge (between 2 nodes) and removing a node respectively.

* `GraphDocument` exposes methods that return node-specific information:

| Method | Description |
|---|---|
| `get_out_degree` | node outdegree  |
| `get_in_degree` | node indegree |
| `get_outgoing_nodes` | Array of outgoing nodes for a given node |
| `get_incoming_nodes` | Array of incoming nodes for a given node |

```python
from jina import Document
from jina.types.document.graph import GraphDocument

gd = GraphDocument()
d1 = Document(id='1', text='hello world')
d2 = Document(id='2', text='goodbye world')
d3 = Document(id='3')
gd.add_edge(d1, d2)
gd.add_edge(d1, d3)

assert gd.get_out_degree(d1) == 2

gd.get_outgoing_nodes(d1)
```

```text
<jina.types.arrays.chunk.ChunkArray length=2 at 140689776342112>
```

* `to_dgl_graph`: returns a `dgl.DGLGraph` from the graph document.
* `load_from_dgl_graph`: returns a `GraphDocument` from a `dgl.DGLGraph`.

