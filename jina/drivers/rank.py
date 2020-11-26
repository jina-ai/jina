__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Dict, List, Tuple

import numpy as np

from . import BaseExecutableDriver
from ..executors.rankers import Chunk2DocRanker
from ..types.document import uid, Document

if False:
    from ..types.sets import DocumentSet


class BaseRankDriver(BaseExecutableDriver):
    """Drivers inherited from this Driver will bind :meth:`rank` by default """

    def __init__(self, executor: str = None, method: str = 'score', *args, **kwargs):
        super().__init__(executor, method, *args, **kwargs)


class Chunk2DocRankDriver(BaseRankDriver):
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

    def _apply_all(self, docs: 'DocumentSet', context_doc: 'Document', *args,
                   **kwargs) -> None:
        """
        :param docs: the chunks of the ``context_doc``, they are at depth_level ``k``
        :param context_doc: the owner of ``docs``, it is at depth_level ``k-1``
        :return:
        """

        match_idx = []  # type: List[Tuple[int, int, int, float]]
        query_chunk_meta = {}  # type: Dict[int, Dict]
        match_chunk_meta = {}  # type: Dict[int, Dict]
        for chunk in docs:
            query_chunk_meta[hash(chunk.id)] = chunk.get_attrs(*self.exec.required_keys)
            for match in chunk.matches:
                match_idx.append(
                    (hash(match.parent_id),
                     hash(match.id),
                     hash(chunk.id),
                     match.score.value)
                )
                match_chunk_meta[hash(match.id)] = match.get_attrs(*self.exec.required_keys)

        if match_idx:
            match_idx = np.array(
                match_idx,
                dtype=[
                    (Chunk2DocRanker.COL_MATCH_PARENT_HASH, np.int64),
                    (Chunk2DocRanker.COL_MATCH_HASH, np.int64),
                    (Chunk2DocRanker.COL_DOC_CHUNK_HASH, np.int64),
                    (Chunk2DocRanker.COL_SCORE, np.float64)
                ]
            )

            docs_scores = self.exec_fn(match_idx, query_chunk_meta, match_chunk_meta)
            op_name = exec.__class__.__name__
            for doc_hash, score in docs_scores:
                m = Document(id=doc_hash)
                m.score.value = score
                m.score.op_name = op_name
                context_doc.matches.append(m)


class CollectMatches2DocRankDriver(BaseRankDriver):
    """This Driver is intended to take a `document` with matches at a `given granularity > 0`, clear those matches and substitute
    these matches by the documents at a lower granularity level.
    Input-Output ::
        Input:
        query document: {granularity: k}
            |- matches: {granularity: k}
        Output:
        query document: {granularity: k}
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
        :return:

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
        query_chunk_meta = {}
        match_chunk_meta = {}
        for match in docs:
            query_chunk_meta[hash(context_doc.id)] = context_doc.get_attrs(*self.exec.required_keys)
            match_idx.append((
                hash(match.parent_id),
                hash(match.id),
                hash(context_doc.id),
                match.score.value
            ))
            match_chunk_meta[hash(match.id)] = match.get_attrs(*self.exec.required_keys)

        if match_idx:
            match_idx = np.array(match_idx,
                                 dtype=[
                                     (Chunk2DocRanker.COL_MATCH_PARENT_HASH, np.int64),
                                     (Chunk2DocRanker.COL_MATCH_HASH, np.int64),
                                     (Chunk2DocRanker.COL_DOC_CHUNK_HASH, np.int64),
                                     (Chunk2DocRanker.COL_SCORE, np.float64)
                                 ]
                                 )

            docs_scores = self.exec_fn(match_idx, query_chunk_meta, match_chunk_meta)
            # These ranker will change the current matches
            context_doc.ClearField('matches')
            op_name = exec.__class__.__name__
            for doc_hash, score in docs_scores:
                m = Document(id=doc_hash)
                m.score.value = score
                m.score.op_name = op_name
                context_doc.matches.append(m)


class Matches2DocRankDriver(BaseRankDriver):
    """ This driver is intended to only resort the given matches on the 0 level granularity for a document.
    It gets the scores from a Ranking Executor, which does only change the scores of matches.
    Afterwards, the Matches2DocRankDriver resorts all matches for a document.
    Input-Output ::
        Input:
        document: {granularity: 0, adjacency: k}
            |- matches: {granularity: 0, adjacency: k+1}
        Output:
        document: {granularity: 0, adjacency: k}
            |- matches: {granularity: 0, adjacency: k+1} (Sorted according to scores from Ranker Executor)
    """

    def __init__(self, reverse: bool = False, traversal_paths: Tuple[str] = ('m',), *args, **kwargs):
        super().__init__(traversal_paths=traversal_paths, *args, **kwargs)
        self.reverse = reverse

    def _apply_all(self, docs: 'DocumentSet', context_doc: 'Document', *args,
                   **kwargs) -> None:
        """

        :param docs: the matches of the ``context_doc``, they are at granularity ``k``
        :param context_doc: the query document having ``docs`` as its matches, it is at granularity ``k``
        :return:

        .. note::
            - This driver will change in place the ordering of ``matches`` of the ``context_doc`.
            - Set the ``traversal_paths`` of this driver such that it traverses along the ``matches`` of the ``chunks`` at the level desired.
        """

        # if at the top-level already, no need to aggregate further
        query_meta = context_doc.get_attrs(*self.exec.required_keys)

        old_match_scores = {hash(match.id): match.score.value for match in docs}
        match_meta = {hash(match.id): match.get_attrs(*self.exec.required_keys) for match in docs}
        # if there are no matches, no need to sort them
        if not old_match_scores:
            return

        new_match_scores = self.exec_fn(query_meta, old_match_scores, match_meta)
        self._sort_matches_in_place(context_doc, new_match_scores)

    def _sort_matches_in_place(self, context_doc: 'Document', match_scores: 'np.ndarray') -> None:
        cm = context_doc.matches
        cm.build()
        for match_hash, score in match_scores:
            cm[uid.hash2id(match_hash)].score.value = score
        cm.sort(key=lambda x: x.score.value, reverse=True)
