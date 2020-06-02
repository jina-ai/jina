__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Dict

import numpy as np

from . import Chunk2DocRanker


class TfIdfRanker(Chunk2DocRanker):
    """
    :class:`TfIdfRanker` calculates the weighted score from the matched chunks. The weights of each chunk is based on
        the tf-idf algorithm. Each query chunk is considered as a ``term``, and the frequency of the query chunk in a
        specific matched document is considered as the naive ``term-frequency``. All the matched results as a whole is
        considered as the corpus, and therefore the frequency of the query chunk in all the matched docs is considered
        as the naive ``document-frequency``. Please refer to the functions for the details of calculating ``tf`` and
        ``idf``.
    """
    required_keys = {'length', 'doc_id'}

    def __init__(self, threshold=0.1, *args, **kwargs):
        """

        :param threshold: the threshold of matching scores. Only the matched chunks with a score that is higher or equal
            to the ``threshold`` are counted as matched.
        """
        super().__init__(*args, **kwargs)
        self.threshold = threshold

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
        _groups = self.group_by_doc_id(match_idx)
        r = []
        _q_idf = self.get_idf(match_idx)
        for _g in _groups:
            _doc_id, _doc_score = self._get_score(_g, query_chunk_meta, match_chunk_meta, _q_idf)
            r.append((_doc_id, _doc_score))
        return self.sort_doc_by_score(r)

    def get_idf(self, match_idx):
        """Get the idf dictionary for query chunks that matched a given doc.

        :param match_idx: an `ndarray` of the size ``N x 4``. ``N`` is the batch size of the matched chunks for the
            query doc. The columns correspond to the ``doc_id`` of the matched chunk, ``chunk_id`` of the matched chunk,
             ``chunk_id`` of the query chunk, and ``score`` of the matched chunk.

        :return: a dict in the size of query chunks

        .. note::
            The 10-based logarithm version idf is used, i.e. idf = log10(total / df). ``df`` denotes the frequency of
                the query chunk in the matched results. `total` denotes the total number of the matched chunks.
        """
        _q_df, _q_id = self._get_df(match_idx)
        _total_df = np.sum(_q_df)
        return {idx: np.log10(_total_df / df + 1e-10) for idx, df in zip(_q_id, _q_df)}

    def get_tf(self, match_idx, match_chunk_meta):
        """Get the tf dictionary for query chunks that matched a given doc.

        :param match_idx: an `ndarray` of the size ``N x 4``. ``N`` is the number of chunks in a given doc that matched
            with the query doc.
        :param match_chunk_meta: a dict of meta info for the matched chunks with **ONLY** the ``required_keys`` are
            kept.

        :return: a dict in the size of query chunks
        .. note::
            The term-frequency of a query chunk is frequency of the query chunk that has a matching score equal or
                higher than the ``threshold``.
            To avoid the effects of long texts, the term-frequency of a query chunk is normalized by the total number of
                 chunks in the matched doc, i.e. tf = (n / n_doc). ``n`` denotes the frequency of the query chunk in the
                  matched doc. ``n_doc`` denotes the total number of chunks in the matched doc.
        """
        q_tf_list, q_id_list, c_id_list = self._get_tf(match_idx)
        return {q_idx: n / match_chunk_meta[doc_idx]['length']
                for doc_idx, q_idx, n in zip(c_id_list, q_id_list, q_tf_list)}

    def _get_df(self, match_idx):
        """Get the naive document frequency

        :param match_idx: an `ndarray` of the size ``N x 4``. ``N`` is the number of chunks in a given doc that matched
            with the query doc.

        :return: a tuple of two `np.ndarray` in the size of ``M``, i.e. the document frequency array and the chunk id
            array. ``M`` is the number of query chunks.
        """
        a = match_idx[match_idx[:, self.col_query_chunk_id].argsort()]
        q_id, q_df = np.unique(a[:, self.col_query_chunk_id], return_counts=True)
        return q_df, q_id

    def _get_tf(self, match_idx):
        """Get the naive term frequency of the query chunks

        :param match_idx: an `ndarray` of the size ``N x 4``. ``N`` is the number of chunks in a given doc that matched
            with the query doc.

        :return: a tuple of three `np.ndarray` in the size of ``M``, i.e. the term frequency array, the query chunk id
            array, and the matched chunk id array.  ``M`` is the number of query chunks.

        .. note::
            The query chunks with matching scores that is lower than the threshold are dropped.
        """
        _m = match_idx[match_idx[:, self.col_score] >= self.threshold]
        _sorted_m = _m[_m[:, self.col_query_chunk_id].argsort()]
        q_id_list, q_tf_list = np.unique(_sorted_m[:, self.col_query_chunk_id], return_counts=True)
        row_id = np.cumsum(q_tf_list) - 1
        c_id_list = _sorted_m[row_id, self.col_chunk_id]
        return q_tf_list, q_id_list, c_id_list

    def _get_score(self, match_idx, query_chunk_meta, match_chunk_meta, idf, *args, **kwargs):
        """Get the doc score based on the weighted sum of matching scores. The weights are calculated from the tf-idf of
             the query chunks.

        :param match_idx: an `ndarray` of the size ``N x 4``. ``N`` is the number of chunks in a given doc that matched
            with the query doc.
        :param tf: a dictionary with the query chunk id as key and the tf as value.
        :param idf: a dictionary with the query chunk id as key and the idf as value.

        :return: a scalar value of the weighted score.
        """
        tf = self.get_tf(match_idx, match_chunk_meta)
        _weights = match_idx[:, self.col_score]
        _q_tfidf = np.vectorize(tf.get)(match_idx[:, self.col_query_chunk_id], 0) * \
                   np.vectorize(idf.get)(match_idx[:, self.col_query_chunk_id], 0)
        _sum = np.sum(_q_tfidf)
        _doc_id = self.get_doc_id(match_idx)
        _score = 0. if _sum == 0 else np.sum(_weights * _q_tfidf) * 1.0 / _sum
        return _doc_id, _score


class BM25Ranker(TfIdfRanker):
    """
    :class:`BM25Ranker` calculates the weighted score from the matched chunks. The weights of each chunk is based on
        the tf-idf algorithm. Each query chunk is considered as a ``term``, and the frequency of the query chunk in a
        specific matched document is considered as the naive ``term-frequency``. All the matched results as a whole is
        considered as the corpus, and therefore the frequency of the query chunk in all the matched docs is considered
        as the naive ``document-frequency``. Please refer to the functions for the details of calculating ``tf`` and
        ``idf``.
    """

    def __init__(self, k=1.2, b=0.75, *args, **kwargs):
        """

        :param k: the parameter ``k`` for the BM25 algorithm.
        :param b: the parameter ``b`` for the BM25 algorithm.
        """
        super().__init__(*args, **kwargs)
        self.k = k
        self.b = b

    def get_idf(self, match_idx):
        """Get the idf dictionary for query chunks that matched a given doc.

        :param match_idx: an `ndarray` of the size ``N x 4``. ``N`` is the batch size of the matched chunks for the
            query doc. The columns correspond to the ``doc_id`` of the matched chunk, ``chunk_id`` of the matched chunk,
             ``chunk_id`` of the query chunk, and ``score`` of the matched chunk.

        :return: a dict in the size of query chunks

        .. note::
            The 10-based logarithm version idf is used, i.e. idf = log10(1 + (total - df + 0.5) / (df + 0.5)). ``df``
                denotes the frequency of the query chunk in all the matched chunks. `total` denotes the total number of
                 the matched chunks.
        """
        _q_df, _q_id = self._get_df(match_idx)
        _total_df = np.sum(_q_df)
        return {idx: np.log10((_total_df + 1.) / (df + 0.5)) ** 2 for idx, df in zip(_q_id, _q_df)}

    def get_tf(self, match_idx, match_chunk_meta):
        """Get the tf dictionary for query chunks that matched a given doc.

        :param match_idx: an `ndarray` of the size ``N x 4``. ``N`` is the number of chunks in a given doc that matched
            with the query doc.
        :param match_chunk_meta: a dict of meta info for the matched chunks with **ONLY** the ``required_keys`` are
            kept.

        :return: a dict in the size of query chunks
        .. note::
            The term-frequency of a query chunk is frequency of the query chunk that has a matching score equal or
                higher than the ``threshold``.
            In BM25, tf = (1 + k) * tf / (k * (1 - b + b * n_doc / avg_n_doc) + tf). ``n`` denotes the
                frequency of the query chunk in the matched doc. ``n_doc`` denotes the total number of chunks in the
                matched doc. ``avg_n_doc`` denotes the average number of chunks over all the matched docs.
        """
        _q_tf_list, _q_id_list, _c_id_list = self._get_tf(match_idx)
        _avg_n_doc = np.mean([c_meta['length'] for c_meta in match_chunk_meta.values()])
        return {q_idx: (1 + self.k) * tf / (
                self.k * (1 - self.b + self.b * match_chunk_meta[c_idx]['length'] / _avg_n_doc) + tf)
                for c_idx, q_idx, tf in zip(_c_id_list, _q_id_list, _q_tf_list)}
