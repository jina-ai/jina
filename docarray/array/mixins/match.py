import warnings
from typing import Optional, Union, Callable, Tuple, Sequence, TYPE_CHECKING

import numpy as np

from ...math.helper import top_k, minmax_normalize, update_rows_x_mat_best

if TYPE_CHECKING:
    from ... import DocumentArray, Document, DocumentArrayMemmap
    from ...ndarray import ArrayType


class MatchMixin:
    """ A mixin that provides match functionality to DocumentArrays """

    def match(
        self,
        darray: Union['DocumentArray', 'DocumentArrayMemmap'],
        metric: Union[
            str, Callable[['ArrayType', 'ArrayType'], 'np.ndarray']
        ] = 'cosine',
        limit: Optional[Union[int, float]] = 20,
        normalization: Optional[Tuple[float, float]] = None,
        metric_name: Optional[str] = None,
        batch_size: Optional[int] = None,
        traversal_ldarray: Optional[Sequence[str]] = None,
        traversal_rdarray: Optional[Sequence[str]] = None,
        exclude_self: bool = False,
        filter_fn: Optional[Callable[['Document'], bool]] = None,
        only_id: bool = False,
        use_scipy: bool = False,
        device: str = 'cpu',
        num_worker: Optional[int] = 1,
        **kwargs,
    ) -> None:
        """Compute embedding based nearest neighbour in `another` for each Document in `self`,
        and store results in `matches`.
        .. note::
            'cosine', 'euclidean', 'sqeuclidean' are supported natively without extra dependency.
            You can use other distance metric provided by ``scipy``, such as `braycurtis`, `canberra`, `chebyshev`,
            `cityblock`, `correlation`, `cosine`, `dice`, `euclidean`, `hamming`, `jaccard`, `jensenshannon`,
            `kulsinski`, `mahalanobis`, `matching`, `minkowski`, `rogerstanimoto`, `russellrao`, `seuclidean`,
            `sokalmichener`, `sokalsneath`, `sqeuclidean`, `wminkowski`, `yule`.
            To use scipy metric, please set ``use_scipy=True``.
        - To make all matches values in [0, 1], use ``dA.match(dB, normalization=(0, 1))``
        - To invert the distance as score and make all values in range [0, 1],
            use ``dA.match(dB, normalization=(1, 0))``. Note, how ``normalization`` differs from the previous.
        - If a custom metric distance is provided. Make sure that it returns scores as distances and not similarity, meaning the smaller the better.
        :param darray: the other DocumentArray or DocumentArrayMemmap to match against
        :param metric: the distance metric
        :param limit: the maximum number of matches, when not given defaults to 20.
        :param normalization: a tuple [a, b] to be used with min-max normalization,
                                the min distance will be rescaled to `a`, the max distance will be rescaled to `b`
                                all values will be rescaled into range `[a, b]`.
        :param metric_name: if provided, then match result will be marked with this string.
        :param batch_size: if provided, then ``darray`` is loaded in batches, where each of them is at most ``batch_size``
            elements. When `darray` is big, this can significantly speedup the computation.
        :param traversal_ldarray: DEPRECATED. if set, then matching is applied along the `traversal_path` of the
                left-hand ``DocumentArray``.
        :param traversal_rdarray: DEPRECATED. if set, then matching is applied along the `traversal_path` of the
                right-hand ``DocumentArray``.
        :param filter_fn: DEPRECATED. if set, apply the filter function to filter docs on the right hand side (rhv) to be matched
        :param exclude_self: if set, Documents in ``darray`` with same ``id`` as the left-hand values will not be
                        considered as matches.
        :param only_id: if set, then returning matches will only contain ``id``
        :param use_scipy: if set, use ``scipy`` as the computation backend. Note, ``scipy`` does not support distance
            on sparse matrix.
        :param device: the computational device for ``.match()``, can be either `cpu` or `cuda`.
        :param num_worker: the number of parallel workers. If not given, then the number of CPUs in the system will be used.

                .. note::
                    This argument is only effective when ``batch_size`` is set.

        :param kwargs: other kwargs.
        """
        if limit is not None:
            if limit <= 0:
                raise ValueError(f'`limit` must be larger than 0, receiving {limit}')
            else:
                limit = int(limit)

        if batch_size is not None:
            if batch_size <= 0:
                raise ValueError(
                    f'`batch_size` must be larger than 0, receiving {batch_size}'
                )
            else:
                batch_size = int(batch_size)

        lhv = self
        rhv = darray

        if traversal_rdarray or traversal_ldarray or filter_fn:
            warnings.warn(
                '''
            `traversal_ldarray` and `traversal_rdarray` will be removed soon. 
            Instead of doing `da.match(..., traveral_ldarray=[...])`, you can achieve the same via 
            `da.traverse_flat(traversal_paths=[...]).match(...)`.
            Same goes with `da.match(..., traveral_rdarray=[...])`, you can do it via: 
            `da.match(da2.traverse_flat(traversal_paths=[...]))`.             
            '''
            )

        if traversal_ldarray:
            lhv = self.traverse_flat(traversal_ldarray)

            from ..document import DocumentArray

            if not isinstance(lhv, DocumentArray):
                lhv = DocumentArray(lhv)

        if traversal_rdarray or filter_fn:
            rhv = darray.traverse_flat(traversal_rdarray or ['r'], filter_fn=filter_fn)

            from ..document import DocumentArray

            if not isinstance(rhv, DocumentArray):
                rhv = DocumentArray(rhv)

        if not (lhv and rhv):
            return

        if callable(metric):
            cdist = metric
        elif isinstance(metric, str):
            if use_scipy:
                from scipy.spatial.distance import cdist as cdist
            else:
                from ...math.distance import cdist as _cdist

                cdist = lambda *x: _cdist(*x, device=device)
        else:
            raise TypeError(
                f'metric must be either string or a 2-arity function, received: {metric!r}'
            )

        metric_name = metric_name or (metric.__name__ if callable(metric) else metric)
        _limit = len(rhv) if limit is None else (limit + (1 if exclude_self else 0))

        if batch_size:
            dist, idx = lhv._match_online(
                rhv, cdist, _limit, normalization, metric_name, batch_size, num_worker
            )
        else:
            dist, idx = lhv._match(rhv, cdist, _limit, normalization, metric_name)

        def _get_id_from_da(rhv, int_offset):
            return rhv._pb_body[int_offset].id

        def _get_id_from_dam(rhv, int_offset):
            return rhv._int2str_id(int_offset)

        from ...memmap import DocumentArrayMemmap
        from ... import Document

        if isinstance(rhv, DocumentArrayMemmap):
            _get_id = _get_id_from_dam
        else:
            _get_id = _get_id_from_da

        for _q, _ids, _dists in zip(lhv, idx, dist):
            _q.matches.clear()
            num_matches = 0
            for _id, _dist in zip(_ids, _dists):
                # Note, when match self with other, or both of them share the same Document
                # we might have recursive matches .
                # checkout https://github.com/jina-ai/jina/issues/3034
                if only_id:
                    d = Document(id=_get_id(rhv, _id))
                else:
                    d = rhv[int(_id)]  # type: Document

                if d.id in lhv:
                    d = Document(d, copy=True)
                    d.pop('matches')
                if not (d.id == _q.id and exclude_self):
                    d.scores = {metric_name: _dist}
                    _q.matches.append(d)
                    num_matches += 1
                    if num_matches >= (limit or _limit):
                        break

    def _match(self, darray, cdist, limit, normalization, metric_name):
        """
        Computes the matches between self and `darray` loading `darray` into main memory.
        :param darray: the other DocumentArray or DocumentArrayMemmap to match against
        :param cdist: the distance metric
        :param limit: the maximum number of matches, when not given
                      all Documents in `darray` are considered as matches
        :param normalization: a tuple [a, b] to be used with min-max normalization,
                                the min distance will be rescaled to `a`, the max distance will be rescaled to `b`
                                all values will be rescaled into range `[a, b]`.
        :param metric_name: if provided, then match result will be marked with this string.
        :return: distances and indices
        """

        x_mat = self.embeddings
        y_mat = darray.embeddings

        dists = cdist(x_mat, y_mat, metric_name)
        dist, idx = top_k(dists, min(limit, len(darray)), descending=False)
        if isinstance(normalization, (tuple, list)) and normalization is not None:
            # normalization bound uses original distance not the top-k trimmed distance
            min_d = np.min(dists, axis=-1, keepdims=True)
            max_d = np.max(dists, axis=-1, keepdims=True)
            dist = minmax_normalize(dist, normalization, (min_d, max_d))

        return dist, idx

    def _match_online(
        self,
        darray,
        cdist,
        limit,
        normalization,
        metric_name,
        batch_size,
        num_worker,
    ):
        """
        Computes the matches between self and `darray` loading `darray` into main memory in chunks of size `batch_size`.

        :param darray: the other DocumentArray or DocumentArrayMemmap to match against
        :param cdist: the distance metric
        :param limit: the maximum number of matches, when not given
                      all Documents in `another` are considered as matches
        :param normalization: a tuple [a, b] to be used with min-max normalization,
                              the min distance will be rescaled to `a`, the max distance will be rescaled to `b`
                              all values will be rescaled into range `[a, b]`.
        :param batch_size: length of the chunks loaded into memory from darray.
        :param metric_name: if provided, then match result will be marked with this string.
        :param num_worker: the number of parallel workers. If not given, then the number of CPUs in the system will be used.
        :return: distances and indices
        """

        x_mat = self.embeddings
        n_x = x_mat.shape[0]

        idx = 0
        top_dists = np.inf * np.ones((n_x, limit))
        top_inds = np.zeros((n_x, limit), dtype=int)

        def _get_dist(da: 'DocumentArray'):
            y_batch = da.embeddings

            distances = cdist(x_mat, y_batch, metric_name)
            dists, inds = top_k(distances, limit, descending=False)

            if isinstance(normalization, (tuple, list)) and normalization is not None:
                dists = minmax_normalize(dists, normalization)

            return dists, inds, y_batch.shape[0]

        if num_worker is None or num_worker > 1:
            # notice that all most all computations (regardless the framework) are conducted in C
            # hence there is no worry on Python GIL and the backend can be safely put to `thread` to
            # save unnecessary data passing. This in fact gives a huge boost on the performance.
            _gen = darray.map_batch(
                _get_dist,
                batch_size=batch_size,
                backend='thread',
                num_worker=num_worker,
            )
        else:
            _gen = (_get_dist(b) for b in darray.batch(batch_size=batch_size))

        for (dists, inds, _bs) in _gen:
            inds += idx
            idx += _bs
            top_dists, top_inds = update_rows_x_mat_best(
                top_dists, top_inds, dists, inds, limit
            )

        # sort final the final `top_dists` and `top_inds` per row
        permutation = np.argsort(top_dists, axis=1)
        dist = np.take_along_axis(top_dists, permutation, axis=1)
        idx = np.take_along_axis(top_inds, permutation, axis=1)

        return dist, idx
