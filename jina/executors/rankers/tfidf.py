import numpy as np
from typing import Dict

from . import BaseRanker


class TfIdfRanker(BaseRanker):
    required_keys = {'length', 'doc_id'}

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
        a = match_idx[match_idx[:, 0].argsort()]
        _, counts = np.unique(a[:, 0], return_counts=True)
        group_idx = np.cumsum(counts)
        group_by_doc = np.split(a, group_idx)
        r = []
        idf = self._get_idf(match_idx)
        for g in group_by_doc:
            if g.shape[0] == 0:
                continue
            tf = self._get_tf(g, match_chunk_meta)
            score = self._get_tfidf(g, idf, tf)
            r.append((g[0, 0], score))
        r = np.array(r, dtype=np.float32)
        r = r[r[:, -1].argsort()[::-1]]
        return r

    @staticmethod
    def _get_idf(match_idx):
        """Get the idf dictionary for query chunks that matched a given doc.

        :param match_idx: an `ndarray` of the size ``N x 4``. ``N`` is the batch size of the matched chunks for the
            query doc. The columns correspond to the ``doc_id`` of the matched chunk, ``chunk_id`` of the matched chunk,
             ``chunk_id`` of the query chunk, and ``score`` of the matched chunk.

        :return: a dict in the size of query chunks

        .. note::
            The 10-based logarithm version idf is used, i.e. idf = log10(total / df). ``df`` denotes the frequency of
                the query chunk in the matched results. `total` denotes the total number of the matched chunks.
        """
        a = match_idx[match_idx[:, 2].argsort()]
        q_id, q_df = np.unique(a[:, 2], return_counts=True)
        total_df = np.sum(q_df)
        return {idx: np.log10(total_df / df) for idx, df in zip(q_id, q_df)}

    @staticmethod
    def _get_tf(g, match_chunk_meta, threshold=0.1):
        """Get the tf dictionary for query chunks that matched a given doc.

        :param g: an `ndarray` of the size ``N x 4``. ``N`` is the number of chunks in a given doc that matched with the
             query doc.
        :param match_chunk_meta: a dict of meta info for the matched chunks with **ONLY** the ``required_keys`` are
            kept.

        :return: a dict in the size of query chunks
        .. note::
            The term-frequency of a query chunk is frequency of the query chunk that has a matching score higher than
                the ``threshold``.
            To avoid the effects of long texts, the term-frequency of a query chunk is normalized by the total number of
                 chunks in the matched doc, i.e. tf = (n / n_doc). ``n`` denotes the frequency of the query chunk in the
                  matched doc. ``n_doc`` denotes the total number of chunks in the matched doc.
        """
        filtered_g = g[g[:, -1] >= threshold]
        a = filtered_g[filtered_g[:, 2].argsort()]
        q_id_list, q_tf = np.unique(a[:, 2], return_counts=True)
        doc_id_list = a[np.cumsum(q_tf) - 1, 1]
        return {q_idx: tf / match_chunk_meta[doc_idx]['length']
                for doc_idx, q_idx, tf in zip(doc_id_list, q_id_list, q_tf)}

    @staticmethod
    def _get_tfidf(g, idf, tf):
        """Get the doc score based on the weighted sum of matching scores. The weights are calculated from the tf-idf of
             the query chunks."""
        weights = g[:, -1]
        tfidf = np.vectorize(tf.__getitem__)(g[:, 2]) * np.vectorize(idf.__getitem__)(g[:, 2])
        weighted_score = weights * tfidf
        return np.sum(weighted_score) * 1.0 / np.sum(weights)
