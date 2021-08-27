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
