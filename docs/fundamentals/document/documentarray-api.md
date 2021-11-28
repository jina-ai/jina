(documentarray)=
# DocumentArray

A {class}`~jina.types.arrays.document.DocumentArray` is a list of `Document` objects. You can construct, delete, insert, sort and traverse
a `DocumentArray` like a Python `list`. It implements all Python List interface. 

```{hint}
We also provide a memory-efficient version of `DocumentArray` coined as {class}`~jina.DocumentArrayMemmap`. It shares *almost* the same API as `DocumentArray`, which means you can easily use it as a drop-in replacement when your data is big. You can {ref}`can find more about here<documentarraymemmap-api>`.
```

## Construct

You can construct a `DocumentArray` in different ways:

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

````{tab} From JSON, CSV, ndarray, files, ...

You can find more details about those APIs in {class}`~jina.types.arrays.mixins.io.from_gen.FromGeneratorMixin`.

```python
da = DocumentArray.from_ndjson(...)
da = DocumentArray.from_csv(...)
da = DocumentArray.from_files(...)
da = DocumentArray.from_lines(...)
da = DocumentArray.from_ndarray(...)
```
````

## Access elements

You can access a `Document` element in the `DocumentArray` via integer index, string `id` or `slice` indices:

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

```{tip}
To access Documents with nested Documents, please refer to {ref}`traverse-doc`.
```

(bulk-access)=
## Bulk access contents

You can quickly access `.text`, `.blob`, `.buffer`, `.embedding` of all Documents in the DocumentArray without writing a for-loop.

`DocumentArray` provides the plural counterparts, i.e. {attr}`~jina.types.arrays.mixins.content.ContentPropertyMixin.texts`, {attr}`~jina.types.arrays.mixins.content.ContentPropertyMixin.buffers`, {attr}`~jina.types.arrays.mixins.content.ContentPropertyMixin.blobs`, {attr}`~jina.types.arrays.mixins.content.ContentPropertyMixin.embeddings` that allows you to **get** and **set** these properties in one shot. It is much more efficient than looping.

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



(embed-via-model)=
## Embed via model

```{important}

{meth}`~jina.types.arrays.mixins.embed.EmbedMixin.embed` function supports both CPU & GPU, which can be specified by its `device` argument.
```

When a `DocumentArray` has `.blobs` set, you can use a deep neural network to {meth}`~jina.types.arrays.mixins.embed.EmbedMixin.embed` it, which means filling `DocumentArray.embeddings`. For example, our `DocumentArray` looks like the following:

```python
from jina import DocumentArray
import numpy as np

docs = DocumentArray.empty(10)
docs.blobs = np.random.random([10, 128]).astype(np.float32)
```

And our embedding model is a simple MLP in Keras/Pytorch/Paddle:

````{tab} PyTorch

```python
import torch

model = torch.nn.Sequential(
    torch.nn.Linear(
        in_features=128,
        out_features=128,
    ),
    torch.nn.ReLU(),
    torch.nn.Linear(in_features=128, out_features=32))
```

````

````{tab} Keras
```python
import tensorflow as tf

model = tf.keras.Sequential(
    [
        tf.keras.layers.Dense(128, activation='relu'),
        tf.keras.layers.Dense(32),
    ]
)

```
````

````{tab} Paddle

```python
import paddle

model = paddle.nn.Sequential(
    paddle.nn.Linear(
        in_features=128,
        out_features=128,
    ),
    paddle.nn.ReLU(),
    paddle.nn.Linear(in_features=128, out_features=32),
)

```
````

Now, you can simply do

```python
docs.embed(model)

print(docs.embeddings)
```

```text
tensor([[-0.1234,  0.0506, -0.0015,  0.1154, -0.1630, -0.2376,  0.0576, -0.4109,
          0.0052,  0.0027,  0.0800, -0.0928,  0.1326, -0.2256,  0.1649, -0.0435,
         -0.2312, -0.0068, -0.0991,  0.0767, -0.0501, -0.1393,  0.0965, -0.2062,
```


```{hint}
By default, `.embeddings` is in the model framework's format. If you want it always be `numpy.ndarray`, use `.embed(..., to_numpy=True)`. 
```

You can also use pretrained model for embedding:

```python
import torchvision
model = torchvision.models.resnet50(pretrained=True)
docs.embed(model)
```

```{hint}
On large `DocumentArray`, you can set `batch_size` via `.embed(..., batch_size=128)`
```

(match-documentarray)=
## Find nearest neighbours

```{important}

{meth}`~jina.types.arrays.mixins.match.MatchMixin.match` function supports both CPU & GPU, which can be specified by its `device` argument.
```

Once `embeddings` is set, one can use {func}`~jina.types.arrays.mixins.match.MatchMixin.match` function to find the nearest neighbour Documents from another `DocumentArray` based on their `.embeddings`.  

The following image visualizes how `DocumentArrayA` finds `limit=5` matches from the Documents in `DocumentArrayB`. By
default, the cosine similarity is used to evaluate the score between Documents.

```{figure} match_illustration_5.svg
:align: center
```

More generally, given two `DocumentArray` objects `da_1` and `da_2` the
function `da_1.match(da_2, metric=some_metric, normalization=(0, 1), limit=N)` finds for each Document in `da_1` the `N` Documents from `da_2` with the lowest metric values according to `some_metric`.

Note that, 

- `da_1.embeddings` and `da_2.embeddings` can be Numpy `ndarray`, Scipy sparse matrix, Tensorflow tensor, PyTorch tensor or Paddle tensor.
- `metric` can be `'cosine'`, `'euclidean'`,  `'sqeuclidean'` or a callable that takes two `ndarray` parameters and
  returns an `ndarray`.
- by default `.match` returns distance not similarity. One can use `normalization` to do min-max normalization. The min distance will be rescaled to `a`, the
  max distance will be rescaled to `b`; all other values will be rescaled into range `[a, b]`. For example, to convert the distance into [0, 1] score, one can use `.match(normalization=(1,0))`.
- `limit` represents the number of nearest neighbours.

The following example finds for each element in `da1` the three closest Documents from the elements in `da2` according to Euclidean distance.

````{tab} Dense embedding 
```{code-block} python
---
emphasize-lines: 20
---
import numpy as np
from jina import DocumentArray

da1 = DocumentArray.empty(4)
da1.embeddings = np.array(
    [[0, 0, 0, 0, 1], [1, 0, 0, 0, 0], [1, 1, 1, 1, 0], [1, 2, 2, 1, 0]]
)

da2 = DocumentArray.empty(5)
da2.embeddings = np.array(
    [
        [0.0, 0.1, 0.0, 0.0, 0.0],
        [1.0, 0.1, 0.0, 0.0, 0.0],
        [1.0, 1.2, 1.0, 1.0, 0.0],
        [1.0, 2.2, 2.0, 1.0, 0.0],
        [4.0, 5.2, 2.0, 1.0, 0.0],
    ]
)

da1.match(da2, metric='euclidean', limit=3)

query = da1[2]
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
emphasize-lines: 21
---
import numpy as np
import scipy.sparse as sp
from jina import DocumentArray

da1 = DocumentArray.empty(4)
da1.embeddings = sp.csr_matrix(np.array(
    [[0, 0, 0, 0, 1], [1, 0, 0, 0, 0], [1, 1, 1, 1, 0], [1, 2, 2, 1, 0]]
))

da2 = DocumentArray.empty(5)
da2.embeddings = sp.csr_matrix(np.array(
    [
        [0.0, 0.1, 0.0, 0.0, 0.0],
        [1.0, 0.1, 0.0, 0.0, 0.0],
        [1.0, 1.2, 1.0, 1.0, 0.0],
        [1.0, 2.2, 2.0, 1.0, 0.0],
        [4.0, 5.2, 2.0, 1.0, 0.0],
    ]
))

da1.match(da2, metric='euclidean', limit=3)

query = da1[2]
print(f'query emb = {query.embedding}')
for m in query.matches:
    print('match emb =', m.embedding, 'score =', m.scores['euclidean'].value)
```

```text
query emb =   (0, 0)	1
  (0, 1)	1
  (0, 2)	1
  (0, 3)	1
match emb =   (0, 0)	1.0
  (0, 1)	1.2
  (0, 2)	1.0
  (0, 3)	1.0 score = 0.20000000298023224
match emb =   (0, 0)	1.0
  (0, 1)	2.2
  (0, 2)	2.0
  (0, 3)	1.0 score = 1.5620499849319458
match emb =   (0, 0)	1.0
  (0, 1)	0.1 score = 1.6763054132461548
```

````

### Keep only ID

Default `A.match(B)` will copy the top-K matched Documents from B to `A.matches`. When these matches are big, copying them can be time-consuming. In this case, one can leverage `.match(..., only_id=True)` to keep only {attr}`~jina.Document.id`:

```python
from jina import DocumentArray
import numpy as np

A = DocumentArray.empty(2)
A.texts = ['hello', 'world']
A.embeddings = np.random.random([2, 10])

B = DocumentArray.empty(3)
B.texts = ['long-doc1', 'long-doc2', 'long-doc3']
B.embeddings = np.random.random([3, 10])
```

````{tab} Only ID

```python
A.match(B, only_id=True)

for m in A.traverse_flat('m'):
    print(m.json())
```

```text
{
  "adjacency": 1,
  "id": "4a8ad5fe4f9b11ec90e61e008a366d48",
  "scores": {
    "cosine": {
      "value": 0.08097544
    }
  }
}
...
```

````

````{tab} Default (keep all attributes)

```python
A.match(B)

for m in A.traverse_flat('m'):
    print(m.json())
```

```text
{
  "adjacency": 1,
  "embedding": {
    "cls_name": "numpy",
    "dense": {
      "buffer": "csxkKGfE7T+/JUBkNzHiP3Lx96W4SdE/SVXrOxYv7T9Fmb+pp3rvP8YdsjGsXuw/CNbxUQ7v2j81AjCpbfjrP6g5iPB9hL4/PHljbxPi1D8=",
      "dtype": "<f8",
      "shape": [
        10
      ]
    }
  },
  "id": "9078d1ec4f9b11eca9141e008a366d48",
  "scores": {
    "cosine": {
      "value": 0.15957883
    }
  },
  "text": "long-doc1"
}
...
```

````

### GPU support

If `.embeddings` is a Tensorflow tensor, PyTorch tensor or Paddle tensor, `.match()` function can work directly on GPU. To do that, simply set `device=cuda`. For example,

```python
from jina import DocumentArray
import numpy as np
import torch

da1 = DocumentArray.empty(10)
da1.embeddings = torch.tensor(np.random.random([10, 256]))
da2 = DocumentArray.empty(10)
da2.embeddings = torch.tensor(np.random.random([10, 256]))

da1.match(da2, device='cuda')
```

````{tip}

When `DocumentArray`/`DocumentArrayMemmap` contain too many documents to fit into GPU memory, one can set `batch_size` to allievate the problem of OOM on GPU.

```python
da1.match(da2, device='cuda', batch_size=256)
```

````

Let's do a simple benchmark on CPU vs. GPU `.match()`:

```python
from jina import DocumentArray

Q = 10
M = 1_000_000
D = 768

da1 = DocumentArray.empty(Q)
da2 = DocumentArray.empty(M)
```

````{tab} on CPU via Numpy

```python
import numpy as np

da1.embeddings = np.random.random([Q, D]).astype(np.float32)
da2.embeddings = np.random.random([M, D]).astype(np.float32)
```

```python
%timeit da1.match(da2, only_id=True)
```

```text
6.18 s ± 7.18 ms per loop (mean ± std. dev. of 7 runs, 1 loop each)
```

````

````{tab} on GPU via PyTorch

```python
import torch

da1.embeddings = torch.tensor(np.random.random([Q, D]).astype(np.float32))
da2.embeddings = torch.tensor(np.random.random([M, D]).astype(np.float32))
```

```python
%timeit da1.match(da2, device='cuda', batch_size=1_000, only_id=True)
```

```text
3.97 s ± 6.35 ms per loop (mean ± std. dev. of 7 runs, 1 loop each)
```

````

Note that in the above GPU example we did a conversion. In practice, there is no need to do this conversion, `.embedding`/`.blob` as well as their bulk versions `.embeddings`/`.blobs` can store PyTorch/Tensorflow/Paddle/Scipy tensor **natively**. That is, in practice, you just need to assign the result directly into `.embeddings` in your Encoder via:

```python
da.embeddings = torch_model(da.blobs)  # <- no .numpy() is necessary
```

And then in just use `.match(da)`.

### Evaluate matches

You can easily evaluate the performance of matches via {func}`~jina.types.arrays.mixins.evaluation.EvaluationMixin.evaluate`, provide that you have the groundtruth of the matches.

Jina provides some common metrics used in the information retrieval community that allows one to evaluate the nearest-neighbour matches. These metrics include: precision, recall, R-precision, hit rate, NDCG, etc. The full list of functions can be found in {class}`~jina.math.evaluation`.

For example, let's create a `DocumentArray` with random embeddings and matching it to itself:

```python
import numpy as np
from jina import DocumentArray

da = DocumentArray.empty(10)
da.embeddings = np.random.random([10, 3])
da.match(da, exclude_self=True)
```

Now `da.matches` contains the matches. Let's use it as the groundtruth. Now let's create imperfect matches by mixing in ten "noise Documents" to every `d.matches`.

```python
da2 = copy.deepcopy(da)

for d in da2:
    d.matches.extend(DocumentArray.empty(10))
    d.matches = d.matches.shuffle()

print(da2.evaluate(da, metric='precision_at_k', k=5))
```

Now we should have the average Precision@10 close to 0.5.
```text
0.5399999999999999
```

Note that this value is an average number over all Documents of `da2`. If you want to look at the individual evaluation, you can check {attr}`~jina.Document.evaluations` attribute, e.g.

```python
for d in da2:
    print(d.evaluations['precision_at_k'].value)
```

```text
0.4000000059604645
0.6000000238418579
0.5
0.5
0.5
0.4000000059604645
0.5
0.4000000059604645
0.5
0.30000001192092896
```

Note that `evaluate()` works only when two `DocumentArray` have the same length and their Documents are aligned by a hash function. The default hash function simply uses {attr}`~jina.Document.id`. You can specify your own hash function.

(traverse-doc)=
## Traverse nested elements

{meth}`~jina.types.arrays.mixins.traverse.TraverseMixin.traverse_flat` function is an extremely powerful tool for iterating over nested and recursive Documents. You get a generator as the return value, which generates `Document`s on the provided traversal paths. You can use or modify `Document`s and the change will be applied in-place. 


### Syntax of traversal path

`.traverse_flat()` function accepts a `traversal_paths` string which can be defined as follow:

```text
path1,path2,path3,...
```

```{tip}
Its syntax is similar to `subscripts` in [`numpy.einsum()`](https://numpy.org/doc/stable/reference/generated/numpy.einsum.html), but without `->` operator.
```

Note that,
- paths are separated by comma `,`;
- each path is a string represents a path from the top-level `Document`s to the destination. You can use `c` to select chunks, `m` to select matches;
- a path can be a single letter, e.g. `c`, `m` or multi-letters, e.g. `ccc`, `cmc`, depending on how deep you want to go;
- to select top-level `Document`s, you can use `r`;
- a path can only go deep, not go back. You can use comma `,` to "reset" the path back to the very top-level;

### Example

Let's look at an example. Assume you have the following `Document` structure:

````{dropdown} Click to see the construction of the nested Document
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
root.plot()
```
````

```{figure} traverse-example-docs.svg
:align: center
```

Now one can use `da.traverse_flat('c')` To get all the `Chunks` of the root `Document`; `da.traverse_flat('m')` to can get all the `Matches` of the root `Document`.

This allows us to composite the `c` and `m` to find `Chunks`/`Matches` which are in a deeper level:

- `da.traverse_flat('cm')` will find all `Matches` of the `Chunks` of root `Document`.
- `da.traverse_flat('cmc')` will find all `Chunks` of the `Matches` of `Chunks` of root `Document`.
- `da.traverse_flat('c,m')` will find all `Chunks` and `Matches` of root `Document`.

````{dropdown} Examples

```python
for ma in da.traverse_flat('cm'):
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
for ma in da.traverse_flat('ccm'):
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
for ma in da.traverse('cm', 'ccm'):
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

When calling `da.traverse_flat('cm,ccm')` the result in our example will be:

```text
DocumentArray([
    Document(id='r1c1m1', adjacency=1, granularity=1),
    Document(id='r1c2c1m1', adjacency=1, granularity=2),
    Document(id='r1c2c1m2', adjacency=1, granularity=2)
])
```

{meth}`jina.types.arrays.mixins.traverse.TraverseMixin.traverse_flat_per_path` is another method for `Document` traversal. It works
like `traverse_flat` but groups `Documents` into `DocumentArrays` based on traversal path. When
calling `da.traverse_flat_per_path('cm,ccm')`, the resulting generator yields the following `DocumentArray`:

```text
DocumentArray([
    Document(id='r1c1m1', adjacency=1, granularity=1),
])

DocumentArray([
    Document(id='r1c2c1m1', adjacency=1, granularity=2),
    Document(id='r1c2c1m2', adjacency=1, granularity=2)
])
```

### Flatten Document

If you simply want to traverse **all** chunks and matches regardless their levels. You can simply use {meth}`~jina.types.arrays.mixins.traverse.TraverseMixin.flatten`. It will return a `DocumentArray` with all chunks and matches flattened into the top-level, no more nested structure.

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

```{figure} document-array-visualize.png
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

## Batching

One can batch a large `DocumentArray` into small ones via {func}`~jina.types.arrays.mixins.group.GroupMixin.batch`. This is useful when a `DocumentArray` is too big to process at once. It is particular useful on `DocumentArrayMemmap`, which ensures the data gets loaded on-demand and in a conservative manner.

```python
from jina import DocumentArray

da = DocumentArray.empty(1000)

for b_da in da.batch(batch_size=256):
    print(len(b_da))
```

```text
256
256
256
232
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
