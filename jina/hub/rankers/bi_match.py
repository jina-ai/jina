__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import numpy as np

from . import Chunk2DocRanker


class BiMatchRanker(Chunk2DocRanker):
    """The :class:`BiMatchRanker` counts the best chunk-hit from both query and doc perspective.

    .. warning:: Here we suppose that the smaller chunk score means the more similar.
    """
    required_keys = {'length'}
    D_MISS = 2000  # cost of a non-match chunk, used for normalization

    def _get_score(self, match_idx, query_chunk_meta, match_chunk_meta, *args, **kwargs):
        s1 = self._directional_score(match_idx, match_chunk_meta, col=self.col_chunk_id)
        s2 = self._directional_score(match_idx, query_chunk_meta, col=self.col_query_chunk_id)
        return self.get_doc_id(match_idx), (s1 + s2) / 2.

    def _directional_score(self, g, chunk_meta, col):
        # col = self.col_chunk_id, from matched_chunk aspect
        # col = self.col_query_chunk_id, from query chunk aspect
        # group by col
        _groups = self._group_by(g, col)
        # take the best match from each group
        _groups_best = np.stack([gg[gg[:, -1].argsort()][0] for gg in _groups])
        # doc total length
        _c = chunk_meta[_groups_best[0, col]]['length']
        # hit chunks
        _h = _groups_best.shape[0]
        # hit distance
        sum_d_hit = np.sum(_groups_best[:, -1])
        # all hit => 0, all_miss => 1
        return 1 - (sum_d_hit + self.D_MISS * (_c - _h)) / (self.D_MISS * _c)
