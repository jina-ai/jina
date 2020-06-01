__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Dict

import numpy as np

from .. import BaseExecutor


class BaseRanker(BaseExecutor):
    """The base class for a `Ranker`"""

    def score(self, *args, **kwargs):
        raise NotImplementedError


class Chunk2DocRanker(BaseRanker):
    """ A :class:`Chunk2DocRanker` translates the chunk-wise score (distance) to the doc-wise score.

    In the query-time, :class:`Chunk2DocRanker` is an almost-always required component.
    Because in the end we want to retrieve top-k documents of given query-document not top-k chunks of
    given query-chunks. The purpose of :class:`Chunk2DocRanker` is to aggregate the already existed top-k chunks
    into documents.

    The key function here is :func:`score`.

    .. seealso::
        :mod:`jina.drivers.handlers.score`

    """

    required_keys = {'text'}  #: a set of ``str``, key-values to extracted from the chunk-level protobuf message

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.col_doc_id = 0
        self.col_chunk_id = 1
        self.col_query_chunk_id = 2
        self.col_score = 3

    def score(self, match_idx: 'np.ndarray', query_chunk_meta: Dict, match_chunk_meta: Dict) -> 'np.ndarray':
        """Translate the chunk-level top-k results into doc-level top-k results. Some score functions may leverage the
        meta information of the query, hence the meta info of the query chunks and matched chunks are given
        as arguments.

        :param match_idx: a [N x 4] numpy ``ndarray``, column-wise:

                - ``match_idx[:, 0]``: ``doc_id`` of the matched chunks, integer
                - ``match_idx[:, 1]``: ``chunk_id`` of the matched chunks, integer
                - ``match_idx[:, 2]``: ``chunk_id`` of the query chunks, integer
                - ``match_idx[:, 3]``: distance/metric/score between the query and matched chunks, float
        :param query_chunk_meta: the meta information of the query chunks, where the key is query chunks' ``chunk_id``,
            the value is extracted by the ``required_keys``.
        :param match_chunk_meta: the meta information of the matched chunks, where the key is matched chunks'
            ``chunk_id``, the value is extracted by the ``required_keys``.
        :return: a [N x 2] numpy ``ndarray``, where the first column is the matched documents' ``doc_id`` (integer)
                the second column is the score/distance/metric between the matched doc and the query doc (float).
        """
        _groups = self.group_by_doc_id(match_idx)
        r = []
        for _g in _groups:
            _doc_id, _doc_score = self._get_score(_g, query_chunk_meta, match_chunk_meta)
            r.append((_doc_id, _doc_score))
        return self.sort_doc_by_score(r)

    def group_by_doc_id(self, match_idx):
        """
        Group the ``match_idx`` by ``doc_id``
        :return: an iterator over the groups
        """
        return self._group_by(match_idx, self.col_doc_id)

    @staticmethod
    def _group_by(match_idx, col):
        # sort by ``col``
        _sorted_m = match_idx[match_idx[:, col].argsort()]
        _, _doc_counts = np.unique(_sorted_m[:, col], return_counts=True)
        # group by ``col``
        return np.split(_sorted_m, np.cumsum(_doc_counts))[:-1]

    def _get_score(self, match_idx, query_chunk_meta, match_chunk_meta, *args, **kwargs):
        raise NotImplementedError

    @staticmethod
    def sort_doc_by_score(r):
        """
        Sort a list of (``doc_id``, ``score``) tuples by the ``score``.
        :return: an `np.ndarray` in the shape of [N x 2], where `N` in the length of the input list.
        """
        r = np.array(r, dtype=np.float64)
        r = r[r[:, -1].argsort()[::-1]]
        return r

    def get_doc_id(self, match_with_same_doc_id):
        return match_with_same_doc_id[0, self.col_doc_id]


class MaxRanker(Chunk2DocRanker):
    """
    :class:`MaxRanker` calculates the score of the matched doc form the matched chunks. For each matched doc, the score
        is the maximal score from all the matched chunks belonging to this doc.

    .. warning: Here we suppose that the larger chunk score means the more similar.
    """

    def _get_score(self, match_idx, query_chunk_meta, match_chunk_meta, *args, **kwargs):
        return self.get_doc_id(match_idx), match_idx[:, self.col_score].max()


class MinRanker(Chunk2DocRanker):
    """
    :class:`MinRanker` calculates the score of the matched doc form the matched chunks. For each matched doc, the score
        is `1 / (1 + s)`, where `s` is the minimal score from all the matched chunks belonging to this doc.

    .. warning:: Here we suppose that the smaller chunk score means the more similar.
    """

    def _get_score(self, match_idx, query_chunk_meta, match_chunk_meta, *args, **kwargs):
        _doc_id = match_idx[0, self.col_doc_id]
        return self.get_doc_id(match_idx), 1. / (1. + match_idx[:, self.col_score].min())
