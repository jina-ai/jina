__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Dict, Optional, Sequence, Tuple

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

    def __init__(self,
                 query_required_keys: Optional[Sequence[str]] = None,
                 match_required_keys: Optional[Sequence[str]] = None,
                 *args,
                 **kwargs):
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
    """ A :class:`Chunk2DocRanker` translates the chunk-wise score (distance) to the doc-wise score.

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

    def score(self, match_idx: 'np.ndarray', query_chunk_meta: Dict, match_chunk_meta: Dict, *args, **kwargs) -> float:
        """
        Given a set of queries (that may correspond to the chunks of a root level query) and a set of matches
        corresping to the same parent id, compute the matching score of the common parent of the set of matches.
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
        :param args: Extra positional arguments
        :param kwargs: Extra keyword arguments
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

    def score(self, query_meta: Dict, old_match_scores: Dict, match_meta: Dict) -> 'np.ndarray':
        """
        Calculates the new scores for matches and returns them. Returns a `np.ndarray` in the shape of [N x 2] where
        `N` is the length of the `old_match_scores`. Semantic: [[match_id, new_score]]

        :param query_meta: Dictionary containing all the query meta information requested by the `required_keys` class_variable.
        :param old_match_scores: Contains old scores in the format {match_id: score}.
        :param match_meta: Dictionary containing all the matches meta information requested by the `required_keys` class_variable. Format: {match_id: {attribute: attribute_value}}e.g.{5: {"length": 3}}
        """
        raise NotImplementedError
