__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Dict, Optional, List

import numpy as np

from .. import BaseExecutor


class BaseRanker(BaseExecutor):
    """
    The base class for a `Ranker`
    :param query_required_keys: Set of keys or features to be extracted from query `Document` by the `Driver` so that
        they are passed as query features or metainfo.
    :param match_required_keys: Set of keys or features to be extracted from match `Document` by the `Driver` so that
        they are passed as match features or metainfo.
    :param args: Extra positional arguments
    :param kwargs: Extra keyword arguments

    .. note::
        See how the attributes are accessed in :class:`Document` in :meth:`get_attrs`.

        .. highlight:: python
        .. code-block:: python

            query = Document({'tags': {'color': 'blue'})
            match = Document({'tags': {'color': 'blue', 'price': 1000}})

            ranker = BaseRanker(query_required_keys=('tags__color'), match_required_keys=('tags__color, 'tags__price')
    """

    def __init__(
        self,
        query_required_keys: Optional[List[str]] = None,
        match_required_keys: Optional[List[str]] = None,
        *args,
        **kwargs
    ):
        """

        :param query_required_keys: Set of keys or features to be extracted from query `Document` by the `Driver` so that
            they are passed as query features or metainfo.
        :param match_required_keys: Set of keys or features to be extracted from match `Document` by the `Driver` so that
            they are passed as match features or metainfo.
        :param args: Extra positional arguments
        :param kwargs: Extra keyword arguments

        .. note::
            See how the attributes are accessed in :class:`Document` in :meth:`get_attrs`.

            .. highlight:: python
            .. code-block:: python

                query = Document({'tags': {'color': 'blue'})
                match = Document({'tags': {'color': 'blue', 'price': 1000}})

                ranker = BaseRanker(query_required_keys=('tags__color'), match_required_keys=('tags__color, 'tags__price')
        """
        super().__init__(*args, **kwargs)
        self.query_required_keys = query_required_keys
        self.match_required_keys = match_required_keys

    def score(self, *args, **kwargs):
        """Calculate the score. Base class method needs to be implemented in subclass.
        :param args: Extra positional arguments
        :param kwargs: Extra keyword arguments
        """
        raise NotImplementedError


class Chunk2DocRanker(BaseRanker):
    """A :class:`Chunk2DocRanker` translates the chunk-wise score (distance) to the doc-wise score.

    In the query-time, :class:`Chunk2DocRanker` is an almost-always required component.
    Because in the end we want to retrieve top-k documents of given query-document not top-k chunks of
    given query-chunks. The purpose of :class:`Chunk2DocRanker` is to aggregate the already existed top-k chunks
    into documents.

    The key function here is :func:`score`.

    .. seealso::
        :mod:`jina.drivers.handlers.score`

    """

    COL_PARENT_ID = 'match_parent_id'
    COL_DOC_CHUNK_ID = 'match_doc_chunk_id'
    COL_QUERY_CHUNK_ID = 'match_query_chunk_id'
    COL_SCORE = 'score'

    def score(
        self, match_idx: 'np.ndarray', query_chunk_meta: Dict, match_chunk_meta: Dict
    ) -> float:
        """
        Given a set of queries (that may correspond to the chunks of a root level query) and a set of matches
        corresponding to the same parent id, compute the matching score of the common parent of the set of matches.
        Returns a score corresponding to the score of the parent document of the matches in `match_idx`

        :param match_idx: A [N x 4] numpy ``ndarray``, column-wise:
                - ``match_idx[:, 0]``: ``parent_id`` of the matched docs, integer
                - ``match_idx[:, 1]``: ``id`` of the matched chunks, integer
                - ``match_idx[:, 2]``: ``id`` of the query chunks, integer
                - ``match_idx[:, 3]``: distance/metric/score between the query and matched chunks, float.
                All the matches belong to the same `parent`
        :param query_chunk_meta: The meta information of the query chunks, where the key is query chunks' ``chunk_id``,
            the value is extracted by the ``query_required_keys``.
        :param match_chunk_meta: The meta information of the matched chunks, where the key is matched chunks'
            ``chunk_id``, the value is extracted by the ``match_required_keys``.


        TODO:
        - ``match_idx[:, 0]`` is redundant because all the matches have the same ``parent_id``.

        """
        raise NotImplementedError


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

    def score(
        self,
        old_matches_scores: List[List[float]],
        queries_metas: List[Dict],
        matches_metas: List[List[Dict]],
    ) -> List[List[float]]:
        """
        Calculates the new scores for matches and returns them. Returns an iterable of the scores to be assigned to the matches.
        The returned scores need to be returned in the same order as the input `:param old_match_scores`.

        .. note::
            The length of `old_match_scores`, `queries_metas` and `matches_metas` correspond to the amount of queries in the batch for which
            one wants to score its matches.

            Every Sequence in match metas correspond to the amount of retrieved matches per query.

            The resulting list of scores will provide a list of score for every query. And every list will be ordered in the same way as the `matches_metas` lists

        :param old_matches_scores: Contains old scores in a list for every query
        :param queries_metas: List of dictionaries containing all the query meta information requested by the `query_required_keys` class_variable for each query in a batch.
        :param matches_metas: List of lists containing all the matches meta information requested by the `match_required_keys` class_variable for every query. Sorted in the same way as `old_match_scores`
        """
        raise NotImplementedError
