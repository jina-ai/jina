__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Dict

import numpy as np

from . import BaseRanker


class BiMatchRanker(BaseRanker):
    """The :class:`BiMatchRanker` counts the best chunk-hit from both query and doc perspective."""
    required_keys = {'length'}
    D_MISS = 2000  # cost of a non-match chunk, used for normalization

    def _get_score(self, match_idx, query_chunk_meta, match_chunk_meta, *args, **kwargs):
        s1 = self._directional_score(match_idx, match_chunk_meta, axis=self.col_chunk_id)
        s2 = self._directional_score(match_idx, query_chunk_meta, axis=self.col_query_chunk_id)
        return self.get_doc_id(match_idx), (s1 + s2) / 2.

    def _directional_score(self, g, chunk_meta, axis):
        # axis = self.col_chunk_id, from matched_chunk aspect
        # axis = self.col_query_chunk_id, from query chunk aspect
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
