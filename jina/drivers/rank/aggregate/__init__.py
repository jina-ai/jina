from typing import Dict, List, Tuple
from collections import defaultdict, namedtuple

import numpy as np

from ....executors.rankers import Chunk2DocRanker
from ....types.document import Document
from ....types.score import NamedScore

from .. import BaseRankDriver

if False:
    from ....types.sets import DocumentSet

COL_STR_TYPE = 'U64'  #: the ID column data type for score matrix


class BaseAggregateMatchesRankerDriver(BaseRankDriver):
    """Drivers inherited from this Driver focus on aggregating scores from `chunks` to its `parents`.

    :param keep_source_matches_as_chunks: A flag to indicate if the driver must return the old matches of the query or its chunks
            (at a greater granularity level (k + 1)) as the chunks of the new computed `matches` (at granularity level k)
            Set it to `True` when keeping track of the chunks that lead to a retrieved result.
    :param args: additional positional arguments which are just used for the parent initialization
    :param kwargs: additional key value arguments which are just used for the parent initialization

    .. note::
        When set `keep_source_matches_as_chunks=True`, the chunks of the match contains **ONLY** the chunks leading
        to the match rather than **ALL** the chunks of the match."""

    def __init__(self, keep_source_matches_as_chunks: bool = False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.keep_source_matches_as_chunks = keep_source_matches_as_chunks

    QueryMatchInfo = namedtuple(
        'QueryMatchInfo', 'match_parent_id match_id query_id score'
    )

    def _extract_query_match_info(self, match: Document, query: Document):
        return self.QueryMatchInfo(
            match_parent_id=match.parent_id,
            match_id=match.id,
            query_id=query.id,
            score=match.score.value,
        )

    def _insert_query_matches(
        self,
        query: Document,
        parent_id_chunk_id_map: dict,
        chunk_matches_by_id: dict,
        docs_scores: 'np.ndarray',
    ):
        """
        :param query: the query Document where the resulting matches will be inserted
        :param parent_id_chunk_id_map: a map with parent_id as key and list of previous matches ids as values
        :param chunk_matches_by_id: the previous matches of the query (at a higher granularity) grouped by the new map (by its parent)
        :param docs_scores: An `np.ndarray` resulting from the ranker executor with the `scores` of the new matches
        """

        op_name = self.exec.__class__.__name__
        for doc_id, score in docs_scores:
            m = Document(id=doc_id)
            m.score = NamedScore(op_name=op_name, value=score)
            if self.keep_source_matches_as_chunks:
                for match_chunk_id in parent_id_chunk_id_map[doc_id]:
                    m.chunks.append(chunk_matches_by_id[match_chunk_id])
            query.matches.append(m)

    @staticmethod
    def _group_by(match_idx, col_name):
        """
        Create an list of numpy arrays with the same ``col_name`` in each position of the list

        :param match_idx: Numpy array of Tuples with document id and score
        :param col_name:  Column name in the structured numpy array of Tuples

        :return: List of numpy arrays with the same ``doc_id`` in each position of the list
        :rtype: np.ndarray.
        """
        _sorted_m = np.sort(match_idx, order=col_name)
        list_numpy_arrays = []
        prev_val = _sorted_m[col_name][0]
        prev_index = 0
        for i, current_val in enumerate(_sorted_m[col_name]):
            if current_val != prev_val:
                list_numpy_arrays.append(_sorted_m[prev_index:i])
                prev_index = i
                prev_val = current_val
        list_numpy_arrays.append(_sorted_m[prev_index:])
        return list_numpy_arrays

    @staticmethod
    def _sort_doc_by_score(r):
        """
        Sort a numpy array  of dtype (``doc_id``, ``score``) by the ``score``.

        :param r: Numpy array of Tuples with document id and score
        :type r: np.ndarray[Tuple[np.str_, np.float64]]
        """
        r[::-1].sort(order=Chunk2DocRanker.COL_SCORE)

    def _score(
        self, match_idx: 'np.ndarray', query_chunk_meta: Dict, match_chunk_meta: Dict
    ) -> 'np.ndarray':
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
            the value is extracted by the ``query_required_keys``.
        :param match_chunk_meta: The meta information of the matched chunks, where the key is matched chunks'
            ``chunk_id``, the value is extracted by the ``match_required_keys``.
        :return: A [N x 2] numpy ``ndarray``, where the first column is the matched documents' ``doc_id`` (integer)
                the second column is the score/distance/metric between the matched doc and the query doc (float).
        :rtype: np.ndarray.
        """
        _groups = self._group_by(match_idx, Chunk2DocRanker.COL_PARENT_ID)
        n_groups = len(_groups)
        res = np.empty(
            (n_groups,),
            dtype=[
                (Chunk2DocRanker.COL_PARENT_ID, COL_STR_TYPE),
                (Chunk2DocRanker.COL_SCORE, np.float64),
            ],
        )

        for i, _g in enumerate(_groups):
            res[i] = (
                _g[Chunk2DocRanker.COL_PARENT_ID][0],
                self.exec_fn(_g, query_chunk_meta, match_chunk_meta),
            )

        self._sort_doc_by_score(res)
        return res


class Chunk2DocRankDriver(BaseAggregateMatchesRankerDriver):
    """Extract matches score from chunks and use the executor to compute the rank and assign the resulting matches to the
    level above.

    Input-Output ::
        Input:
        document: {granularity: k-1}
                |- chunks: {granularity: k}
                |    |- matches: {granularity: k}
                |
                |- chunks: {granularity: k}
                    |- matches: {granularity: k}
        Output:
        document: {granularity: k-1}
                |- chunks: {granularity: k}
                |    |- matches: {granularity: k}
                |
                |- chunks: {granularity: k}
                |    |- matches: {granularity: k}
                |
                |-matches: {granularity: k-1} (Ranked according to Ranker Executor)
    """

    def __init__(self, traversal_paths: Tuple[str] = ('r',), *args, **kwargs):
        super().__init__(traversal_paths=traversal_paths, *args, **kwargs)

    def _apply_all(self, docs: 'DocumentSet', *args, **kwargs) -> None:
        """
        :param docs: the doc which gets bubbled up matches
        :param args: not used (kept to maintain interface)
        :param kwargs: not used (kept to maintain interface)
        """
        for doc in docs:
            chunks = doc.chunks
            match_idx = []  # type: List[Tuple[str, str, str, float]]
            query_meta = {}  # type: Dict[str, Dict]
            match_meta = {}  # type: Dict[str, Dict]
            parent_id_chunk_id_map = defaultdict(list)
            matches_by_id = defaultdict(Document)
            for chunk in chunks:
                query_meta[chunk.id] = (
                    chunk.get_attrs(*self._exec_query_keys)
                    if self._exec_query_keys
                    else None
                )
                for match in chunk.matches:
                    match_info = self._extract_query_match_info(
                        match=match, query=chunk
                    )
                    match_idx.append(match_info)
                    match_meta[match.id] = (
                        match.get_attrs(*self._exec_match_keys)
                        if self._exec_match_keys
                        else None
                    )
                    parent_id_chunk_id_map[match.parent_id].append(match.id)
                    matches_by_id[match.id] = match

            if match_idx:
                match_idx = np.array(
                    match_idx,
                    dtype=[
                        (Chunk2DocRanker.COL_PARENT_ID, COL_STR_TYPE),
                        (Chunk2DocRanker.COL_DOC_CHUNK_ID, COL_STR_TYPE),
                        (Chunk2DocRanker.COL_QUERY_CHUNK_ID, COL_STR_TYPE),
                        (Chunk2DocRanker.COL_SCORE, np.float64),
                    ],
                )

                docs_scores = self._score(match_idx, query_meta, match_meta)

                self._insert_query_matches(
                    query=doc,
                    parent_id_chunk_id_map=parent_id_chunk_id_map,
                    chunk_matches_by_id=matches_by_id,
                    docs_scores=docs_scores,
                )


class AggregateMatches2DocRankDriver(BaseAggregateMatchesRankerDriver):
    """This Driver is intended to take a `document` with matches at a `given granularity > 0`, clear those matches and substitute
    these matches by the documents at a lower granularity level.
    Input-Output ::
        Input:
        document: {granularity: k}
            |- matches: {granularity: k}

        Output:
        document: {granularity: k}
            |- matches: {granularity: k-1} (Sorted according to Ranker Executor)

    Imagine a case where we are querying a system with text documents chunked by sentences. When we query the system,
    we use sentences (chunks) to query it. So at some point we will have:
    `query sentence (documents of granularity 1):
        matches: indexed sentences (documents of level depth 1)`
    `
    But in the output we want to have the full document that better matches the `sentence`.
    `query sentence (documents of granularity 1):
        matches: indexed full documents (documents of granularity 0).
    `
    Using this Driver before querying a Binary Index with full binary document data can be very useful to implement a search system.
    """

    def __init__(self, traversal_paths: Tuple[str] = ('r',), *args, **kwargs):
        super().__init__(traversal_paths=traversal_paths, *args, **kwargs)

    def _apply_all(self, docs: 'DocumentSet', *args, **kwargs) -> None:
        """

        :param docs: the document at granularity ``k``
        :param args: not used (kept to maintain interface)
        :param kwargs: not used (kept to maintain interface)

        .. note::
            - This driver will substitute the ``matches`` of `docs` to the corresponding ``parent documents`` of its current ``matches`` according
            to the executor.
            - Set the ``traversal_paths`` of this driver to identify the documents, which needs to get bubbled up matches.
        """

        for doc in docs:
            matches = doc.matches

            match_idx = []
            query_meta = {}
            match_meta = {}
            parent_id_chunk_id_map = defaultdict(list)
            matches_by_id = defaultdict(Document)

            query_meta[doc.id] = (
                doc.get_attrs(*self._exec_query_keys) if self._exec_query_keys else None
            )

            for match in matches:
                match_info = self._extract_query_match_info(match=match, query=doc)
                match_idx.append(match_info)
                match_meta[match.id] = (
                    match.get_attrs(*self._exec_match_keys)
                    if self._exec_match_keys
                    else None
                )
                parent_id_chunk_id_map[match.parent_id].append(match.id)
                matches_by_id[match.id] = match

            if match_idx:
                match_idx = np.array(
                    match_idx,
                    dtype=[
                        (Chunk2DocRanker.COL_PARENT_ID, COL_STR_TYPE),
                        (Chunk2DocRanker.COL_DOC_CHUNK_ID, COL_STR_TYPE),
                        (Chunk2DocRanker.COL_QUERY_CHUNK_ID, COL_STR_TYPE),
                        (Chunk2DocRanker.COL_SCORE, np.float64),
                    ],
                )

                docs_scores = self._score(match_idx, query_meta, match_meta)
                # This ranker will change the current matches
                doc.ClearField('matches')
                self._insert_query_matches(
                    query=doc,
                    parent_id_chunk_id_map=parent_id_chunk_id_map,
                    chunk_matches_by_id=matches_by_id,
                    docs_scores=docs_scores,
                )
