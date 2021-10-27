(documentarray)=
# DocumentArray

A `DocumentArray` is a list of `Document` objects. You can construct, delete, insert, sort and traverse
a `DocumentArray` like a Python `list`.

## Minimum working example

```python
from jina import DocumentArray, Document

da = DocumentArray([Document(), Document()]) 
```


Common methods supported by `DocumentArray`:

| Category | Attributes |
|--- |--- |
| Python `list`-like interface | `__getitem__`, `__setitem__`, `__delitem__`, `__len__`, `insert`, `append`, `reverse`, `extend`, `__iadd__`, `__add__`, `__iter__`, `clear`, `sort`, `shuffle`, `sample` |
| Persistence | `save`, `load` |
| Math operations | `match`, `visualize`, `shuffle`, `sample` |
| Advanced getters | `get_attributes`, `get_attributes_with_docs`, `traverse_flat`, `traverse` |

## Construct DocumentArray

You can construct a `DocumentArray` from an iterable of `Document`s:

````{tab} From List
```python
from jina import DocumentArray, Document

da = DocumentArray([Document(), Document()])
```
````
````{tab} From generator
```python
from jina import DocumentArray, Document

da = DocumentArray((Document() for _ in range(10)))
```
````
````{tab} From another DocumentArray
```python
from jina import DocumentArray, Document

da = DocumentArray((Document() for _ in range(10)))
da1 = DocumentArray(da)
```
````

## Persistence DocumentArray

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

## Basic operations

### Access elements

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


### Sort elements

`DocumentArray` is a subclass of `MutableSequence`, therefore you can use built-in Python `sort` to sort elements in
a `DocumentArray` object, e.g.

```{code-block} python
---
emphasize-lines: 11
---
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

### Filter elements

You can use Python's [built-in `filter()`](https://docs.python.org/3/library/functions.html#filter) to filter elements
in a `DocumentArray` object:

```{code-block} python
---
emphasize-lines: 8
---
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


### Sample elements

`DocumentArray` provides function `.sample` that sample `k` elements without replacement. It accepts 2 parameters, `k`
and `seed`. `k` is used to define the number of elements to sample, and `seed`
helps you generate pseudo random results. It should be noted that `k` should always less or equal than the length of the
document array.

To make use of the function:

```{code-block} python
---
emphasize-lines: 6, 7
---
from jina import Document, DocumentArray

da = DocumentArray()  # initialize a random document array
for idx in range(100):
    da.append(Document(id=idx))  # append 100 documents into `da`
sampled_da = da.sample(k=10)  # sample 10 documents
sampled_da_with_seed = da.sample(k=10, seed=1)  # sample 10 documents with seed.
```

### Shuffle elements

`DocumentArray` provides function `.shuffle` that shuffle the entire `DocumentArray`. It accepts the parameter `seed`
.  `seed` helps you generate pseudo random results. By default, `seed` is None.

To make use of the function:

```{code-block} python
---
emphasize-lines: 6, 7
---
from jina import Document, DocumentArray

da = DocumentArray()  # initialize a random document array
for idx in range(100):
    da.append(Document(id=idx))  # append 100 documents into `da`
shuffled_da = da.shuffle()  # shuffle the DocumentArray
shuffled_da_with_seed = da.shuffle(seed=1)  # shuffle the DocumentArray with seed.
```

### Split elements by tags

`DocumentArray` provides function `.split` that split the `DocumentArray` into multiple :class:`DocumentArray` according to the tag value (stored in `tags`) of each :class:`Document`.
It returns a python `dict` where `Documents` with the same value on `tag` are grouped together, their orders are preserved from the original :class:`DocumentArray`.

To make use of the function:

```{code-block} python
---
emphasize-lines: 10
---
from jina import Document, DocumentArray

da = DocumentArray()
da.append(Document(tags={'category': 'c'}))
da.append(Document(tags={'category': 'c'}))
da.append(Document(tags={'category': 'b'}))
da.append(Document(tags={'category': 'a'}))
da.append(Document(tags={'category': 'a'}))

rv = da.split(tag='category')
assert len(rv['c']) == 2  # category `c` is a DocumentArray has 2 Documents
```



### Iterate elements via `itertools`

As `DocumentArray` is an `Iterable`, you can also
use [Python's built-in `itertools` module](https://docs.python.org/3/library/itertools.html) on it. This enables
advanced "iterator algebra" on the `DocumentArray`.

For instance, you can group a `DocumentArray` by `parent_id`:

```{code-block} python
---
emphasize-lines: 5
---
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


#### Advanced iterator on nested Documents

`DocumentArray.traverse` can be used for iterating over nested & recursive Documents. As return value you get a generator which
generates `DocumentArrays` matching the provided traversal paths. Let's assume you have the following `Document`
structure:

```python
from jina import DocumentArray, Document

da = DocumentArray()

root1 = Document(id='r1')

chunk1 = Document(id='r1c1')
root1.chunks.append(chunk1)
root1.chunks[0].matches.append(Document(id='r1c1m1'))

chunk2 = Document(id='r1c2')
root1.chunks.append(chunk2)
chunk2_chunk1 = Document(id='r1c2c1')
chunk2_chunk2 = Document(id='r1c2c2')
root1.chunks[1].chunks.extend([chunk2_chunk1, chunk2_chunk2])
root1.chunks[1].chunks[0].matches.extend([Document(id='r1c2c1m1'), Document(id='r1c2c1m2')])

chunk3 = Document(id='r1c3')
root1.chunks.append(chunk3)

root2 = Document(id='r2')

da.extend([root1, root2])
```

When calling `da.traverse(['cm', 'ccm'])` you get a generator over two `DocumentArrays`. The first `DocumentArray`
contains the `Matches` of the `Chunks` and the second `DocumentArray` contains the `Matches` of the `Chunks` of
the `Chunks`. The following `DocumentArrays` are emitted from the generator:

```python
from jina import Document
from jina.types.arrays import MatchArray

MatchArray([Document(id='r1c1m1', adjacency=1)], reference_doc=da['r1'].chunks['c1'])
MatchArray([], reference_doc=da['r1'].chunks['c2'])
MatchArray([], reference_doc=da['r1'].chunks['c3'])
MatchArray([Document(id='r1c2c1m1', adjacency=1, granularity=2), Document(id='r1c2c1m2', adjacency=1, granularity=2)],
           reference_doc=da['r1'].chunks['c2'].chunks['c2c1'])
MatchArray([], reference_doc=da['r1'].chunks['c2'].chunks['c2c2'])
```

`DocumentArray.traverse_flat` is doing the same but flattens all `DocumentArrays` in the generator. When
calling `da.traverse_flat(['cm', 'ccm'])` the result in our example will be the following:

```python
from jina import Document, DocumentArray

assert da.traverse_flat(['cm', 'ccm']) == DocumentArray([
    Document(id='r1c1m1', adjacency=1, granularity=1),
    Document(id='r1c2c1m1', adjacency=1, granularity=2),
    Document(id='r1c2c1m2', adjacency=1, granularity=2)
])
```

`DocumentArray.traverse_flat_per_path` is a further method for `Document` traversal. It works
like `DocumentArray.traverse_flat` but groups the `Documents` into `DocumentArrays` based on the traversal path. When
calling `da.traverse_flat_per_path(['cm', 'ccm'])`, the resulting generator emits the following `DocumentArrays`:

```python
from jina import Document, DocumentArray

DocumentArray([
    Document(id='r1c1m1', adjacency=1, granularity=1),
])
DocumentArray([
    Document(id='r1c2c1m1', adjacency=1, granularity=2),
    Document(id='r1c2c1m2', adjacency=1, granularity=2)
])
```

### Get attributes of elements

`DocumentArray` implements powerful getters that lets you fetch multiple attributes from the Documents it contains in
one-shot:

```{code-block} python
---
emphasize-lines: 9
---
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

## DocumentArray embeddings

There is a faster version to extract embeddings from a `DocumentArray` or `DocumentArrayMemmap`, the property `.embeddings`. This property assumes all embeddings in the array have the same shape and dtype. Note that

```
da.embeddings
```

will produce the same output as `np.stack(da.get_attributes('embedding'))` but the results will be retrieved faster.

```
[[1 2 3]
 [4 5 6]
 [7 8 9]]
```

````{admonition} Note
:class: note
Using `.embeddings` in a DocumenArray or DocumentArrayMemmap with different shapes or dtypes might yield to unnexpected results.
````


### Visualize embeddings

`DocumentArray` provides function `.visualize` to plot document embeddings in a 2D graph. `visualize` supports 2 methods
to project in 2D space: `pca` and `tsne`.

In the following example, we add 3 different distributions of embeddings and see 3 kinds of point clouds in the graph.

```{code-block} python
---
emphasize-lines: 13
---
import numpy as np
from jina import Document, DocumentArray

da = DocumentArray(
    [
        Document(embedding=np.random.normal(0, 1, 50)) for _ in range(500)
    ] + [
        Document(embedding=np.random.normal(5, 2, 50)) for _ in range(500)
    ] + [
        Document(embedding=np.random.normal(2, 5, 50)) for _ in range(500)
    ]
)
da.visualize()

```

```{figure} ../../../.github/2.0/document-array-visualize.png
:align: center
```


(match-documentarray)=
## Matching DocumentArray to another

`DocumentArray` provides a`.match` function that finds the closest documents between two `DocumentArray` objects. This
function requires all documents to be compared have an `embedding` and all embeddings to have the same length.

The following image shows how `DocumentArrayA` finds `limit=5` matches from the documents in `DocumentArrayB`. By
default, the cosine similarity is used to evaluate the score between documents.

```{figure} ../../../.github/images/match_illustration_5.svg
:align: center
```

More generally, given two `DocumentArray` objects `da_1` and `da_2` the
function `da_1.match(da_2, metric=some_metric, normalization=(0, 1), limit=N)` finds for each document in `da_1` the `N` documents from `da_2` with the lowest metric values according to `some_metric`.

- `metric` can be `'cosine'`, `'euclidean'`,  `'sqeuclidean'` or a callable that takes 2 `ndarray` parameters and
  returns an `ndarray`
- `normalization` is a tuple [a, b] to be used with min-max normalization. The min distance will be rescaled to `a`, the
  max distance will be rescaled to `b`; all other values will be rescaled into range `[a, b]`.

The following example finds for each element in `da_1` the 3 closest documents from the elements in `da_2` )according to the euclidean distance).

```{code-block} python
---
emphasize-lines: 18
---
from jina import Document, DocumentArray
import numpy as np

d1 = Document(embedding=np.array([0, 0, 0, 0, 1]))
d2 = Document(embedding=np.array([1, 0, 0, 0, 0]))
d3 = Document(embedding=np.array([1, 1, 1, 1, 0]))
d4 = Document(embedding=np.array([1, 2, 2, 1, 0]))

d1_m = Document(embedding=np.array([0, 0.1, 0, 0, 0]))
d2_m = Document(embedding=np.array([1, 0.1, 0, 0, 0]))
d3_m = Document(embedding=np.array([1, 1.2, 1, 1, 0]))
d4_m = Document(embedding=np.array([1, 2.2, 2, 1, 0]))
d5_m = Document(embedding=np.array([4, 5.2, 2, 1, 0]))

da_1 = DocumentArray([d1, d2, d3, d4])
da_2 = DocumentArray([d1_m, d2_m, d3_m, d4_m, d5_m])

da_1.match(da_2, metric='euclidean', limit=3)
query = da_1[2]
print(f'query emb = {query.embedding}')
for m in query.matches:
    print('match emb =', m.embedding, 'score =', m.scores['euclidean'].value)
```

```text
query emb = [1 1 1 1 0]
match emb = [1.  1.2 1.  1.  0. ] score = 0.20000000298023224
match emb = [1.  2.2 2.  1.  0. ] score = 1.5620499849319458
match emb = [1.  0.1 0.  0.  0. ] score = 1.6763054132461548
```

### Matching sparse embeddings

We can use sparse embeddings and do the `.match` using `is_sparse=True`

```{code-block} python
---
emphasize-lines: 18
---
from jina import Document, DocumentArray
import scipy.sparse as sp

d1 = Document(embedding=sp.csr_matrix([0, 0, 0, 0, 1]))
d2 = Document(embedding=sp.csr_matrix([1, 0, 0, 0, 0]))
d3 = Document(embedding=sp.csr_matrix([1, 1, 1, 1, 0]))
d4 = Document(embedding=sp.csr_matrix([1, 2, 2, 1, 0]))

d1_m = Document(embedding=sp.csr_matrix([0, 0.1, 0, 0, 0]))
d2_m = Document(embedding=sp.csr_matrix([1, 0.1, 0, 0, 0]))
d3_m = Document(embedding=sp.csr_matrix([1, 1.2, 1, 1, 0]))
d4_m = Document(embedding=sp.csr_matrix([1, 2.2, 2, 1, 0]))
d5_m = Document(embedding=sp.csr_matrix([4, 5.2, 2, 1, 0]))

da_1 = DocumentArray([d1, d2, d3, d4])
da_2 = DocumentArray([d1_m, d2_m, d3_m, d4_m, d5_m])

da_1.match(da_2, metric='euclidean', limit=4, is_sparse=True)
query = da_1[2]
print(f'query emb = {query.embedding.todense()}')
for m in query.matches:
    print('match emb =', m.embedding.todense(), 'score =', m.scores['euclidean'].value)
```

```text
query emb = [[1 1 1 1 0]]
match emb = [[1.  1.2 1.  1.  0. ]] score = 0.20000000298023224
match emb = [[1.  2.2 2.  1.  0. ]] score = 1.5620499849319458
match emb = [[1.  0.1 0.  0.  0. ]] score = 1.6763054132461548
```



