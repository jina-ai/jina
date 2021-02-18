from typing import Dict, List, Tuple
from collections import defaultdict, namedtuple

import numpy as np

from ....executors.rankers import Chunk2DocRanker, COL_STR_TYPE
from ....types.document import Document
from ....types.score import NamedScore

from .. import BaseRankDriver

if False:
    from ....types.sets import DocumentSet


class BaseAggregateMatchesRankerDriver(BaseRankDriver):
    """Drivers inherited from this Driver focus on aggregating scores from `chunks` to its `parents`."""

    def __init__(self,
                 keep_source_matches_as_chunks: bool = False,
                 *args,
                 **kwargs):
        """

        :param keep_source_matches_as_chunks: A flag to indicate if the driver must return the old matches of the query or its chunks
            (at a greater granularity level (k + 1)) as the chunks of the new computed `matches` (at granularity level k)
            Set it to `True` when keeping track of the chunks that lead to a retrieved result.
        :param *args: *args for super
        :param **kwargs: **kwargs for super

        .. note::
            When set `keep_source_matches_as_chunks=True`, the chunks of the match contains **ONLY** the chunks leading
            to the match rather than **ALL** the chunks of the match.

        """
        super().__init__(*args, **kwargs)
        self.keep_source_matches_as_chunks = keep_source_matches_as_chunks

    QueryMatchInfo = namedtuple('QueryMatchInfo', 'match_parent_id match_id query_id score')

    def _extract_query_match_info(self, match: Document, query: Document):
        return self.QueryMatchInfo(match_parent_id=match.parent_id,
                                   match_id=match.id,
                                   query_id=query.id,
                                   score=match.score.value)

    def _insert_query_matches(self,
                              query: Document,
                              parent_id_chunk_id_map: dict,
                              chunk_matches_by_id: dict,
                              docs_scores: 'np.ndarray'):
        """
        :param query: the query Document where the resulting matches will be inserted
        :param parent_id_chunk_id_map: a map with parent_id as key and list of previous matches ids as values
        :param chunk_matches_by_id: the previous matches of the query (at a higher granularity) grouped by the new map (by its parent)
        :param docs_scores: An `np.ndarray` resulting from the ranker executor with the `scores` of the new matches
        """

        op_name = self.exec.__class__.__name__
        for doc_id, score in docs_scores:
            m = Document(id=doc_id)
            m.score = NamedScore(op_name=op_name,
                                 value=score)
            if self.keep_source_matches_as_chunks:
                for match_chunk_id in parent_id_chunk_id_map[doc_id]:
                    m.chunks.append(chunk_matches_by_id[match_chunk_id])
            query.matches.append(m)


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

        .. note::
            - It traverses on ``chunks`` not on ``matches``. This is because ranker needs context information
            from ``matches`` for several ``chunks``
    """

    def __init__(self, traversal_paths: Tuple[str] = ('c',), *args, **kwargs):
        super().__init__(traversal_paths=traversal_paths, *args, **kwargs)

    def _apply_all(self, docs: 'DocumentSet',
                   context_doc: 'Document', *args,
                   **kwargs) -> None:
        """
        :param docs: the chunks of the ``context_doc``, they are at depth_level ``k``
        :param context_doc: the owner of ``docs``, it is at depth_level ``k-1``
        :param *args: not used (kept to maintain interface)
        :param **kwargs: not used (kept to maintain interface)
        """

        match_idx = []  # type: List[Tuple[str, str, str, float]]
        query_meta = {}  # type: Dict[str, Dict]
        match_meta = {}  # type: Dict[str, Dict]
        parent_id_chunk_id_map = defaultdict(list)
        matches_by_id = defaultdict(Document)
        for chunk in docs:
            query_meta[chunk.id] = chunk.get_attrs(*self.exec.required_keys)
            for match in chunk.matches:
                match_info = self._extract_query_match_info(match=match, query=chunk)
                match_idx.append(match_info)
                match_meta[match.id] = match.get_attrs(*self.exec.required_keys)
                parent_id_chunk_id_map[match.parent_id].append(match.id)
                matches_by_id[match.id] = match

        if match_idx:
            match_idx = np.array(match_idx,
                                 dtype=[
                                     (Chunk2DocRanker.COL_PARENT_ID, COL_STR_TYPE),
                                     (Chunk2DocRanker.COL_DOC_CHUNK_ID, COL_STR_TYPE),
                                     (Chunk2DocRanker.COL_QUERY_CHUNK_ID, COL_STR_TYPE),
                                     (Chunk2DocRanker.COL_SCORE, np.float64)
                                 ]
                                 )

            docs_scores = self.exec_fn(match_idx, query_meta, match_meta)

            self._insert_query_matches(query=context_doc,
                                       parent_id_chunk_id_map=parent_id_chunk_id_map,
                                       chunk_matches_by_id=matches_by_id,
                                       docs_scores=docs_scores)


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

    def __init__(self, traversal_paths: Tuple[str] = ('m',), *args, **kwargs):
        super().__init__(traversal_paths=traversal_paths, *args, **kwargs)

    def _apply_all(self, docs: 'DocumentSet', context_doc: 'Document', *args,
                   **kwargs) -> None:
        """

        :param docs: the matches of the ``context_doc``, they are at granularity ``k``
        :param context_doc: the query document having ``docs`` as its matches, it is at granularity ``k``
        :param *args: not used (kept to maintain interface)
        :param **kwargs: not used (kept to maintain interface)

        .. note::
            - This driver will substitute the ``matches`` of `docs` to the corresponding ``parent documents`` of its current ``matches`` according
            to the executor.
            - Set the ``traversal_paths`` of this driver such that it traverses along the ``matches`` of the ``chunks`` at the granularity desired
            (with respect to the ``query``).
        """

        # if at the top-level already, no need to aggregate further
        if context_doc is None:
            return

        match_idx = []
        query_meta = {}
        match_meta = {}
        parent_id_chunk_id_map = defaultdict(list)
        matches_by_id = defaultdict(Document)

        query_meta[context_doc.id] = context_doc.get_attrs(*self.exec.required_keys)
        for match in docs:
            match_info = self._extract_query_match_info(match=match, query=context_doc)
            match_idx.append(match_info)
            match_meta[match.id] = match.get_attrs(*self.exec.required_keys)
            parent_id_chunk_id_map[match.parent_id].append(match.id)
            matches_by_id[match.id] = match

        if match_idx:
            match_idx = np.array(match_idx,
                                 dtype=[
                                     (Chunk2DocRanker.COL_PARENT_ID, COL_STR_TYPE),
                                     (Chunk2DocRanker.COL_DOC_CHUNK_ID, COL_STR_TYPE),
                                     (Chunk2DocRanker.COL_QUERY_CHUNK_ID, COL_STR_TYPE),
                                     (Chunk2DocRanker.COL_SCORE, np.float64)
                                 ]
                                 )

            docs_scores = self.exec_fn(match_idx, query_meta, match_meta)
            # This ranker will change the current matches
            context_doc.ClearField('matches')
            self._insert_query_matches(query=context_doc,
                                       parent_id_chunk_id_map=parent_id_chunk_id_map,
                                       chunk_matches_by_id=matches_by_id,
                                       docs_scores=docs_scores)
