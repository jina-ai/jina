# Jina Math

Jina offers several Math helpers used by its core logic that users can use for their own purposes (for example, in their Executors).


<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
Table of Contents

- [Distances](#distances)
- [Dimension Reduction](#dimension-reduction)
- [Other helpers](#other-helpers)
  - [Min-max normalization](#min-max-normalization)
  - [Top K:](#top-k)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Distances
You can compute distances between ndarrays within a single matrix using `pdist` or between 2 matrices using `cdist`.

```python
import numpy as np
from jina.math.distance import pdist
embeddings = np.array([[1, 0, 0], [2, 0, 0], [3, 0, 0]])
pdist(embeddings, metric='euclidean')
```

```text
array([[0., 1., 2.],
       [1., 0., 1.],
       [2., 1., 0.]])
```

```python
import numpy as np
from jina.math.distance import cdist
embeddings_1 = np.array([[1, 0, 0], [2, 0, 0], [3, 0, 0]])
embeddings_2 = np.array([[0, 1, 0], [0, 0, 1], [1, 0, 0]])
cdist(embeddings_1, embeddings_2, metric='euclidean')
```

```text
array([[1.41421356, 1.41421356, 0.        ],
       [2.23606798, 2.23606798, 1.        ],
       [3.16227766, 3.16227766, 2.        ]])
```

These functions support the following metrics:
* `cosine`: cosine similarity
* `sqeuclidean`: euclidean square distance
* `euclidean`: euclidean distance

You can also specify whether computation should be done with sparse data by setting `is_sparse` to `True`.

## Dimension Reduction

Dimension reduction is offered with class `PCA`. It performs Principal Component Analysis given a number of components.
To reduce reduce the dimensions of a dataset, you can either call `PCA.fit` and then `PCA.transform` or directly call `PCA.fit_transform`.
`fit` computes the projection matrix and stores it while transform uses the projection matrix to apply reduction.

```python
import numpy as np
from jina.math.dimensionality_reduction import PCA

embeddings = np.array([[1, 0, 0], [2, 0, 0], [3, 0, 0]])
pca = PCA(n_components=2)
pca.fit(embeddings)
pca.transform(embeddings)
```

```text
array([[1., 0.],
       [2., 0.],
       [3., 0.]])
```

Or you can just do:

```python
import numpy as np
from jina.math.dimensionality_reduction import PCA

embeddings = np.array([[1, 0, 0], [2, 0, 0], [3, 0, 0]])
pca = PCA(n_components=2)
pca.fit_transform(embeddings)
```

## Other helpers

### Min-max normalization
The function `minmax_normalize` normalizes the input `ndarray` so that values fit in `t_range` (by default `(0, 1)`):

```python
import numpy as np
from jina.math.helper import minmax_normalize
a = np.array([1, 2, 3])
minmax_normalize(a)
```

```text
array([0. , 0.5, 1. ])
```

### Top K:
Using function `top_k`, you can extract the top k values along with their indices from a list of vectors.
The function returns a tuple of arrays: the selected distances and the indices array:

```python
from jina.math.helper import top_k
import numpy as np

dist, idx = top_k(np.array([[1, 0, 2], [2, 0, 10]]), 2)
print("distances")
print(dist)
print("indices")
print(idx)
```

```text
distances
[[0 1]
 [0 2]]
indices
[[1 0]
 [1 0]]
```
