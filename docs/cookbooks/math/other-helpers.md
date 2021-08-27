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
