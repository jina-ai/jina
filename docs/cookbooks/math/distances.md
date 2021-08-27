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
