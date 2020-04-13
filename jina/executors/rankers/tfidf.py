import numpy as np
from typing import Dict

from . import BaseRanker


class TfIdfRanker(BaseRanker):
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
        a = match_idx[match_idx[:, 0].argsort()]
        _, counts = np.unique(a[:, 0], return_counts=True)
        group_idx = np.cumsum(counts)
        group_by_doc = np.split(a, group_idx)
        r = []
        idf = self.get_idf(match_idx)
        for g in group_by_doc:
            if g.shape[0] == 0:
                continue
            tf = self.get_tf(g, match_chunk_meta)
            score = self._get_score(g, tf, idf)
            r.append((g[0, 0], score))
        r = np.array(r, dtype=np.float32)
        r = r[r[:, -1].argsort()[::-1]]
        return r

    @staticmethod
    def get_idf(match_idx):
        """Get the idf dictionary for query chunks that matched a given doc.

        :param match_idx: an `ndarray` of the size ``N x 4``. ``N`` is the batch size of the matched chunks for the
            query doc. The columns correspond to the ``doc_id`` of the matched chunk, ``chunk_id`` of the matched chunk,
             ``chunk_id`` of the query chunk, and ``score`` of the matched chunk.

        :return: a dict in the size of query chunks

        .. note::
            The 10-based logarithm version idf is used, i.e. idf = log10(total / df). ``df`` denotes the frequency of
                the query chunk in the matched results. `total` denotes the total number of the matched chunks.
        """
        q_df, q_id = TfIdfRanker._get_df(match_idx)
        total_df = np.sum(q_df)
        return {idx: np.log10(total_df / df) for idx, df in zip(q_id, q_df)}

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
        q_tf, q_id_list, doc_id_list = self._get_tf(match_idx)
        return {q_idx: n / match_chunk_meta[doc_idx]['length']
                for doc_idx, q_idx, n in zip(doc_id_list, q_id_list, q_tf)}

    @staticmethod
    def _get_df(match_idx):
        """Get the naive document frequency

        :param match_idx: an `ndarray` of the size ``N x 4``. ``N`` is the number of chunks in a given doc that matched
            with the query doc.

        :return: a tuple of two `np.ndarray` in the size of ``M``, i.e. the document frequency array and the chunk id
            array. ``M`` is the number of query chunks.
        """
        a = match_idx[match_idx[:, 2].argsort()]
        q_id, q_df = np.unique(a[:, 2], return_counts=True)
        return q_df, q_id

    def _get_tf(self, match_idx):
        """Get the naive term frequency

        :param match_idx: an `ndarray` of the size ``N x 4``. ``N`` is the number of chunks in a given doc that matched
            with the query doc.

        :return: a tuple of three `np.ndarray` in the size of ``M``, i.e. the term frequency array, the chunk id
            array, and the doc id array.  ``M`` is the number of query chunks.
        """
        filtered_g = match_idx[match_idx[:, -1] >= self.threshold]
        a = filtered_g[filtered_g[:, 2].argsort()]
        q_id_list, q_tf = np.unique(a[:, 2], return_counts=True)
        doc_id_list = a[np.cumsum(q_tf) - 1, 1]
        return q_tf, q_id_list, doc_id_list

    @staticmethod
    def _get_score(match_idx, tf, idf):
        """Get the doc score based on the weighted sum of matching scores. The weights are calculated from the tf-idf of
             the query chunks.

        :param match_idx: an `ndarray` of the size ``N x 4``. ``N`` is the number of chunks in a given doc that matched
            with the query doc.
        :param tf: a dictionary with the query chunk id as key and the tf as value.
        :param idf: a dictionary with the query chunk id as key and the idf as value.

        :return: a scalar value of the weighted score.
        """
        weights = match_idx[:, -1]
        tfidf = np.vectorize(tf.__getitem__)(match_idx[:, 2]) * np.vectorize(idf.__getitem__)(match_idx[:, 2])
        weighted_score = weights * tfidf
        return np.sum(weighted_score) * 1.0 / np.sum(weights)


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

    @staticmethod
    def get_idf(match_idx):
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
        q_df, q_id = TfIdfRanker._get_df(match_idx)
        total_df = np.sum(q_df)
        return {idx: np.log10((total_df + 1.) / (df + 0.5)) ** 2 for idx, df in zip(q_id, q_df)}

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
        q_tf, q_id_list, doc_id_list = self._get_tf(match_idx)
        avg_n_doc = np.mean([c_meta['length'] for c_meta in match_chunk_meta.values()])
        return {
            q_idx: (1 + self.k) * tf /
                   (self.k * (1 - self.b + self.b * match_chunk_meta[doc_idx]['length'] / avg_n_doc) + tf)
            for doc_idx, q_idx, tf in zip(doc_id_list, q_id_list, q_tf)}
