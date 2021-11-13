(documentarray)=
# DocumentArray

A `DocumentArray` is a list of `Document` objects. You can construct, delete, insert, sort and traverse
a `DocumentArray` like a Python `list`. It implements all Python List interface, including `__getitem__`, `__setitem__`, `__delitem__`, `__len__`, `insert`, `append`, `reverse`, `extend`, `__iadd__`, `__add__`, `__iter__`, `clear`, `sort`. 

## Minimum working example

```python
from jina import DocumentArray, Document

da = DocumentArray([Document(), Document()])  # equivalent to DocumentArray.empty(2)  
```

## Construct

You can construct a `DocumentArray` from an iterable of `Document`s:

````{tab} From empty Documents
```python
from jina import DocumentArray

da = DocumentArray.empty(10)
```
````
````{tab} From list of Documents
```python
from jina import DocumentArray, Document

da = DocumentArray([Document(...), Document(...)])
```
````
````{tab} From generator
```python
from jina import DocumentArray, Document

da = DocumentArray((Document(...) for _ in range(10)))
```
````
````{tab} From another DocumentArray
```python
from jina import DocumentArray, Document

da = DocumentArray((Document() for _ in range(10)))
da1 = DocumentArray(da)
```
````


## Access Documents

You can access a `Document` in the `DocumentArray` via integer index, string `id` or `slice` indices:

```python
from jina import DocumentArray, Document

da = DocumentArray([Document(id='hello'), Document(id='world'), Document(id='goodbye')])

da[0]
da['world']
da[1:2]
```

```text
<jina.types.document.Document id=hello at 5699749904>
<jina.types.document.Document id=world at 5736614992>
<jina.types.arrays.document.DocumentArray length=1 at 5705863632>
```

(bulk-access)=
## Bulk access content

You can quickly access `.text`, `.blob`, `.buffer`, `.embedding` of all Documents in the DocumentArray without writing a for-loop.

`DocumentArray` provides the plural counterparts, i.e. `.texts`, `.blobs`, `.buffers`, `.embeddings` that allows you to **get** and **set** these properties in one shot. It is much more efficient than looping.

```python
from jina import DocumentArray

da = DocumentArray.empty(2)
da.texts = ['hello', 'world']

print(da[0], da[1])
```

```text
<jina.types.document.Document ('id', 'text') at 4520833232>
<jina.types.document.Document ('id', 'text') at 5763350672>
```

When accessing `.blobs` or `.embeddings`, it automatically ravels/unravels the ndarray (can be Numpy/TensorFlow/PyTorch/SciPy/PaddlePaddle) for you.

```python
import numpy as np
import scipy.sparse
from jina import DocumentArray

sp_embed = np.random.random([10, 256])
sp_embed[sp_embed > 0.1] = 0
sp_embed = scipy.sparse.coo_matrix(sp_embed) 

da = DocumentArray.empty(10)

da.embeddings = scipy.sparse.coo_matrix(sp_embed)

print('da.embeddings.shape=', da.embeddings.shape)

for d in da:
    print('d.embedding.shape=', d.embedding.shape)
```

```text
da.embeddings.shape= (10, 256)
d.embedding.shape= (1, 256)
d.embedding.shape= (1, 256)
d.embedding.shape= (1, 256)
d.embedding.shape= (1, 256)
d.embedding.shape= (1, 256)
d.embedding.shape= (1, 256)
d.embedding.shape= (1, 256)
d.embedding.shape= (1, 256)
d.embedding.shape= (1, 256)
d.embedding.shape= (1, 256)
```

(match-documentarray)=

## Finding nearest neighbours

`DocumentArray` provides a `.match` function that finds the closest Documents between two `DocumentArray` objects based on their `.embeddings`. This
function requires that all Documents being compared have an `embedding` of the same length.

The following image shows how `DocumentArrayA` finds `limit=5` matches from the Documents in `DocumentArrayB`. By
default, the cosine similarity is used to evaluate the score between Documents.

```{figure} ../../../.github/images/match_illustration_5.svg
:align: center
```

More generally, given two `DocumentArray` objects `da_1` and `da_2` the
function `da_1.match(da_2, metric=some_metric, normalization=(0, 1), limit=N)` finds for each Document in `da_1` the `N` Documents from `da_2` with the lowest metric values according to `some_metric`.

- `metric` can be `'cosine'`, `'euclidean'`,  `'sqeuclidean'` or a callable that takes two `ndarray` parameters and
  returns an `ndarray`
- `normalization` is a tuple [a, b] to be used with min-max normalization. The min distance will be rescaled to `a`, the
  max distance will be rescaled to `b`; all other values will be rescaled into range `[a, b]`.

The following example finds for each element in `da_1` the three closest Documents from the elements in `da_2` (according to Euclidean distance).

````{tab} Dense embedding 
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
````

````{tab} Sparse embedding


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

da_1.match(da_2, metric='euclidean', limit=4)
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

````

## Traverse nested Documents

`DocumentArray.traverse` can be used for iterating over nested and recursive Documents. You get a generator as the return value, which
generates `DocumentArray`s matching the provided traversal paths. Let's assume you have the following `Document`
structure:

```python
from jina import DocumentArray, Document

root = Document(id='r1')

chunk1 = Document(id='r1c1')
root.chunks.append(chunk1)
root.chunks[0].matches.append(Document(id='r1c1m1'))

chunk2 = Document(id='r1c2')
root.chunks.append(chunk2)
chunk2_chunk1 = Document(id='r1c2c1')
chunk2_chunk2 = Document(id='r1c2c2')
root.chunks[1].chunks.extend([chunk2_chunk1, chunk2_chunk2])
root.chunks[1].chunks[0].matches.extend([Document(id='r1c2c1m1'), Document(id='r1c2c1m2')])

chunk3 = Document(id='r1c3')
root.chunks.append(chunk3)

da = DocumentArray([root])
```

````{dropdown} Visualization of Root Document

```python
root.plot()
```

```{figure} ../../../.github/images/traverse-example-docs.svg
:align: center
```

````

`DocumentArray.traverse` can be used via `da.traverse(['c'])` to get all the `Chunks` of the root `Document`. You can also use `m` to present `Matches`, for example, `da.traverse['m']` can get all the `Matches` of the root `Document`.

This allows us to composite the `c` and `m` to find `Chunks`/`Matches` which are in a deeper level:

- `da.traverse['cm']` will find all `Matches` of the `Chunks` of root `Document`.
- `da.traverse['cmc']` will find all `Chunks` of the `Matches` of `Chunks` of root `Document`.
- `da.traverse['c', 'm']` will find all `Chunks` and `Matches` of root `Document`.

````{dropdown} Examples

```python
for ma in da.traverse(['cm']):
  for m in ma:
    print(m.json())
```

```json
{
  "adjacency": 1,
  "granularity": 1,
  "id": "r1c1m1"
}
```

```python
for ma in da.traverse(['ccm']):
  for m in ma:
    print(m.json())
```

```json
{
  "adjacency": 1,
  "granularity": 2,
  "id": "r1c2c1m1"
}
{
  "adjacency": 1,
  "granularity": 2,
  "id": "r1c2c1m2"
}
```

```python
for ma in da.traverse(['cm', 'ccm']):
  for m in ma:
    print(m.json())
```

```json
{
  "adjacency": 1,
  "granularity": 1,
  "id": "r1c1m1"
}
{
  "adjacency": 1,
  "granularity": 2,
  "id": "r1c2c1m1"
}
{
  "adjacency": 1,
  "granularity": 2,
  "id": "r1c2c1m2"
}
```
````

`DocumentArray.traverse_flat` does the same but flattens all `DocumentArrays` in the generator. When
calling `da.traverse_flat(['cm', 'ccm'])` the result in our example will be:

```python
from jina import Document, DocumentArray

assert da.traverse_flat(['cm', 'ccm']) == DocumentArray([
    Document(id='r1c1m1', adjacency=1, granularity=1),
    Document(id='r1c2c1m1', adjacency=1, granularity=2),
    Document(id='r1c2c1m2', adjacency=1, granularity=2)
])
```

`DocumentArray.traverse_flat_per_path` is a another method for `Document` traversal. It works
like `DocumentArray.traverse_flat` but groups `Documents` into `DocumentArrays` based on traversal path. When
calling `da.traverse_flat_per_path(['cm', 'ccm'])`, the resulting generator yields the following `DocumentArrays`:

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

## Visualization

`DocumentArray` provides the `.plot_embeddings` function to plot Document embeddings in a 2D graph. `visualize` supports two methods
to project in 2D space: `pca` and `tsne`.

In the following example, we add three different distributions of embeddings and see three kinds of point clouds in the graph.

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
da.plot_embeddings()

```

```{figure} ../../../.github/2.0/document-array-visualize.png
:align: center
```

## Persistence

To save all elements in a `DocumentArray` in a JSON line format:

```python
from jina import DocumentArray, Document

da = DocumentArray([Document(), Document()])

da.save('data.json')
da1 = DocumentArray.load('data.json')
```

`DocumentArray` can be also stored in binary format, which is much faster and yields a smaller file:

```python
from jina import DocumentArray, Document

da = DocumentArray([Document(), Document()])

da.save('data.bin', file_format='binary')
da1 = DocumentArray.load('data.bin', file_format='binary')
```




## Sort

`DocumentArray` is a subclass of `MutableSequence`, therefore you can use Python's built-in `sort` to sort elements in
a `DocumentArray` object:

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

## Filter

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


## Sampling

`DocumentArray` provides a `.sample` function that samples `k` elements without replacement. It accepts two parameters, `k`
and `seed`. `k` defines the number of elements to sample, and `seed`
helps you generate pseudo-random results. Note that `k` should always be less than or equal to the length of the
`DocumentArray`.

To make use of the function:

```{code-block} python
---
emphasize-lines: 6, 7
---
from jina import Document, DocumentArray

da = DocumentArray()  # initialize a random DocumentArray
for idx in range(100):
    da.append(Document(id=idx))  # append 100 Documents into `da`
sampled_da = da.sample(k=10)  # sample 10 Documents
sampled_da_with_seed = da.sample(k=10, seed=1)  # sample 10 Documents with seed.
```

## Shuffle

`DocumentArray` provides a `.shuffle` function that shuffles the entire `DocumentArray`. It accepts the parameter `seed`
.  `seed` helps you generate pseudo-random results. By default, `seed` is None.

To make use of the function:

```{code-block} python
---
emphasize-lines: 6, 7
---
from jina import Document, DocumentArray

da = DocumentArray()  # initialize a random DocumentArray
for idx in range(100):
    da.append(Document(id=idx))  # append 100 Documents into `da`
shuffled_da = da.shuffle()  # shuffle the DocumentArray
shuffled_da_with_seed = da.shuffle(seed=1)  # shuffle the DocumentArray with seed.
```

## Split by `.tags`

`DocumentArray` provides a `.split` function that splits the `DocumentArray` into multiple `DocumentArray`s according to the tag value (stored in `tags`) of each `Document`.
It returns a Python `dict` where `Documents` with the same `tag` value are grouped together, with their orders preserved from the original `DocumentArray`.

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



## Iterate via `itertools`

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




## Get bulk attributes

`DocumentArray` implements powerful getters that let you fetch multiple attributes from the `Document`s it contains in
one shot:

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
