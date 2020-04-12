from typing import Dict

import numpy as np

from . import BaseRanker


class BiMatchRanker(BaseRanker):
    """The :class:`BiMatchRanker` counts the best chunk-hit from both query and doc perspective."""
    required_keys = {'length'}
    D_MISS = 2000  # cost of a non-match chunk, used for normalization

    def score(self, match_idx: 'np.ndarray', query_chunk_meta: Dict, match_chunk_meta: Dict) -> 'np.ndarray':
        """

        :param match_idx: an `ndarray` of the size ``N x 4``. ``N`` is the batch size of the matched chunks for the
            query doc. The columns correspond to the ``doc_id`` of the matched chunk, ``chunk_id`` of the matched chunk,
             ``chunk_id`` of the query chunk, and ``score`` of the matched chunk.
        :param query_chunk_meta: a dict of meta info for the query chunks with **ONLY** the ``required_keys`` are kept.
        :param match_chunk_meta: a dict of meta info for the matched chunks with **ONLY** the ``required_keys`` are
            kept.

        :return: an `ndarray` of the size ``M x 2``. ``M`` is the number of matched docs. The columns correspond to the
            ``doc_id`` and ``score``.

        .. note::
            In both `query_chunk_meta` and `match_chunk_meta`, ONLY the fields from the ``required_keys`` are kept.

        """
        # sort by doc_id
        a = match_idx[match_idx[:, 0].argsort()]
        # group by doc_id
        gs = np.split(a, np.cumsum(np.unique(a[:, 0], return_counts=True)[1])[:-1])
        # for each doc group
        r = []
        for g in gs:
            s1 = self._directional_score(g, match_chunk_meta, axis=1)
            s2 = self._directional_score(g, query_chunk_meta, axis=2)
            r.append((g[0, 0], (s1 + s2) / 2))

        # sort descendingly and return
        r = np.array(r, dtype=np.float32)
        r = r[r[:, -1].argsort()[::-1]]
        return r

    def _directional_score(self, g, chunk_meta, axis):
        # axis = 1, from matched_chunk aspect
        # axis = 2, from search chunk aspect
        s_m = g[g[:, axis].argsort()]
        # group by matched_chunk_id
        gs_m = np.split(s_m, np.cumsum(np.unique(s_m[:, axis], return_counts=True)[1])[:-1])
        # take the best match from each group
        gs_mb = np.stack([gg[gg[:, -1].argsort()][0] for gg in gs_m])
        # doc total length
        _c = chunk_meta[gs_mb[0, axis]]['length']
        # hit chunks
        _h = gs_mb.shape[0]
        # hit distance
        sum_d_hit = np.sum(gs_mb[:, -1])
        # all hit => 0, all_miss => 1
        return 1 - (sum_d_hit + self.D_MISS * (_c - _h)) / (self.D_MISS * _c)
