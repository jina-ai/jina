from math import inf
from typing import Optional, Union

import numpy as np

from jina import Document
from ...math.distance import cdist
from ...math.helper import top_k

if False:
    from .document import DocumentArray
    from .memmap import DocumentArrayMemmap


class DocumentArrayNeuralOpsMixin:
    """ A mixin that provides match functionality to DocumentArrays """

    def match(
        self,
        darray: Union['DocumentArray', 'DocumentArrayMemmap'],
        metric: str = 'cosine',
        limit: Optional[int] = inf,
        is_distance: bool = False,
    ) -> None:
        """Compute embedding based nearest neighbour in `another` for each Document in `self`,
        and store results in `matches`.

        Note:
            - If metric is 'cosine' it uses the cosine **distance**.
            - If metric is 'euclidean' it uses the euclidean **distance**.
            - If metric is 'sqeuclidean' it uses the euclidean **distance** squared.

        :param darray: the other DocumentArray or DocumentArrayMemmap to match against
        :param metric: the distance metric
        :param limit: the maximum number of matches, when not given
                      all Documents in `another` are considered as matches
        :param is_distance: Boolean flag informing if `metric` values want to be considered as distances or scores.
        """

        X = np.stack(self.get_attributes('embedding'))
        Y = np.stack(darray.get_attributes('embedding'))
        limit = min(limit, len(darray))

        dists = cdist(X, Y, metric)
        dist, idx = top_k(dists, limit, descending=False)
        if not is_distance:
            if metric == 'cosine':
                dist = 1 - dist
            elif metric == 'sqeuclidean' or metric == 'euclidean':
                dist = 1 / (dist + 1)

        for _q, _ids, _dists in zip(self, idx, dist):
            _q.matches.clear()
            for _id, _dist in zip(_ids, _dists):
                d = Document(darray[int(_id)], copy=True)
                d.scores[metric] = _dist
                _q.matches.append(d)
