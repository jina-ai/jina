__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Dict

import numpy as np

from .. import BaseExecutor

COL_STR_TYPE = 'U64'  #: the ID column data type for score matrix


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
    """set: Set of required keys to be extracted from matches and query to fill the information of `query` and `chunk` meta information.
    These are the set of keys to be extracted from `Document`.

    All the keys not found in the `DocumentProto` fields, will be extracted from the `tags` structure of `Document`.
    .. seealso::

        :meth:`get_attrs` of :class:`Document`

    """
    COL_PARENT_ID = 'match_parent_id'
    COL_DOC_CHUNK_ID = 'match_doc_chunk_id'
    COL_QUERY_CHUNK_ID = 'match_query_chunk_id'
    COL_SCORE = 'score'

    def score(self, match_idx: 'np.ndarray', query_chunk_meta: Dict, match_chunk_meta: Dict) -> 'np.ndarray':
        """
        Translate the chunk-level top-k results into doc-level top-k results. Some score functions may leverage the
        meta information of the query, hence the meta info of the query chunks and matched chunks are given
        as arguments.

        :param match_idx: A [N x 4] numpy ``ndarray``, column-wise:
                - ``match_idx[:, 0]``: ``doc_id`` of the matched chunks, integer
                - ``match_idx[:, 1]``: ``chunk_id`` of the matched chunks, integer
                - ``match_idx[:, 2]``: ``chunk_id`` of the query chunks, integer
                - ``match_idx[:, 3]``: distance/metric/score between the query and matched chunks, float
        :type match_idx: np.ndarray.
        :param query_chunk_meta: The meta information of the query chunks, where the key is query chunks' ``chunk_id``,
            the value is extracted by the ``required_keys``.
        :type query_chunk_meta: Dict.
        :param match_chunk_meta: The meta information of the matched chunks, where the key is matched chunks'
            ``chunk_id``, the value is extracted by the ``required_keys``.
        :type query_chunk_meta: Dict.
        :return: A [N x 2] numpy ``ndarray``, where the first column is the matched documents' ``doc_id`` (integer)
                the second column is the score/distance/metric between the matched doc and the query doc (float).
        :rtype: np.ndarray.
        """
        _groups = self.group_by_doc_id(match_idx)
        r = []
        for _g in _groups:
            _doc_id, _doc_score = self._get_score(_g, query_chunk_meta, match_chunk_meta)
            r.append((_doc_id, _doc_score))
        return self.sort_doc_by_score(r)

    def group_by_doc_id(self, match_idx):
        """
        Group the ``match_idx`` by ``doc_id``.
        :return: an iterator over the groups.
        :rtype: :class:`Chunk2DocRanker`.
        """
        return self._group_by(match_idx, self.COL_PARENT_ID)

    @staticmethod
    def _group_by(match_idx, col_name):
        # sort by ``col
        _sorted_m = np.sort(match_idx, order=col_name)
        _, _doc_counts = np.unique(_sorted_m[col_name], return_counts=True)
        # group by ``col``
        return np.split(_sorted_m, np.cumsum(_doc_counts))[:-1]

    def _get_score(self, match_idx, query_chunk_meta, match_chunk_meta, *args, **kwargs):
        raise NotImplementedError

    @staticmethod
    def sort_doc_by_score(r):
        """
        Sort a list of (``doc_id``, ``score``) tuples by the ``score``.
        :param r: List of Tuples with document id and score
        :type r: List[Tuple[Any, Any]]
        :return: A `np.ndarray` in the shape of [N x 2], where `N` in the length of the input list.
        :rtype: np.ndarray
        """
        r = np.array(r, dtype=[
            (Chunk2DocRanker.COL_PARENT_ID, COL_STR_TYPE),
            (Chunk2DocRanker.COL_SCORE, np.float64)]
                     )
        return np.sort(r, order=Chunk2DocRanker.COL_SCORE)[::-1]

    def get_doc_id(self, match_with_same_doc_id):
        """Return document id that matches with given id :param:`match_with_same_doc_id`"""
        return match_with_same_doc_id[0][self.COL_PARENT_ID]


class Match2DocRanker(BaseRanker):
    """
    Re-scores the matches for a document. This Ranker is only responsible for
    calculating new scores and not for the actual sorting. The sorting is handled
    in the respective ``Matches2DocRankDriver``.

    Possible implementations:
        - ReverseRanker (reverse scores of all matches)
        - BucketShuffleRanker (first buckets matches and then sort each bucket).
    """

    COL_MATCH_ID = 'match_doc_chunk_id'
    COL_SCORE = 'score'

    def score(self, query_meta: Dict, old_match_scores: Dict, match_meta: Dict) -> 'np.ndarray':
        """
        Calculates the new scores for matches and returns them.

        :param query_meta: Dictionary containing all the query meta information
            requested by the `required_keys` class_variable.
        :type query_meta: Dict
        :param old_match_scores: Contains old scores in the format {match_id: score}
        :type old_match_scores: Dict
        :param match_meta: Dictionary containing all the matches meta information
            requested by the `required_keys` class_variable.
            Format: {match_id: {attribute: attribute_value}}e.g.{5: {"length": 3}}
        :type match_meta: Dict
        :return: A `np.ndarray` in the shape of [N x 2] where `N` is the length of
            the `old_match_scores`. Semantic: [[match_id, new_score]]
        :rtype: np.ndarray
        """
        raise NotImplementedError
