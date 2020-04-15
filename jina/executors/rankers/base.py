from typing import Dict

import numpy as np

from . import BaseRanker


class ProbRanker(BaseRanker):
    def score(self, match_idx: 'np.ndarray', query_chunk_meta: Dict, match_chunk_meta: Dict) -> 'np.ndarray':
        a = match_idx[match_idx[:, 0].argsort()]
        _, counts = np.unique(a[:, 0], return_counts=True)
        group_idx = np.cumsum(counts)
        group_by_doc = np.split(a, group_idx)[:-1]
        r = []
        for g in group_by_doc:
            prob_d_c = self.prob_doc_given_c(g)
            prob_c_q = self.prob_c_given_q(g, query_chunk_meta)
            prob_q = self.prob_q(query_chunk_meta)
            prob_joint = self.prob_joint(prob_d_c, prob_c_q, prob_q)
            r.append(np.sum(prob_joint))
        r = np.array(r, dtype=np.float32)
        r = r[r[:, -1].argsort()[::-1]]
        return r

    def prob_doc_given_c(self, match_array):
        # idf
        return match_array[:, -1]

    def prob_c_given_q(self, match_array, query_chunk_meta):
        num_c = match_array[:, 1].unique()
        num_q = match_array[:, 2].unique()
        return np.random.rand(num_c, num_q)

    def prob_joint(self, prob_d_c, prob_c_q, prob_q):
        num_c = prob_d_c.shape[0]
        num_q = prob_q.shape[0]
        return np.random.rand(num_c, num_q)
