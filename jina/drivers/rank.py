__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

# lift the chunk-level topk to doc-level topk
from typing import Dict, Iterable, List, Tuple

import numpy as np

from . import BaseExecutableDriver
from .helper import pb_obj2dict
from ..executors.rankers import Chunk2DocRanker, Match2DocRanker
from ..proto import uid

if False:
    from ..proto import jina_pb2


class BaseRankDriver(BaseExecutableDriver):
    """Drivers inherited from this Driver will bind :meth:`rank` by default """

    def __init__(self, executor: str = None, method: str = 'score', *args, **kwargs):
        super().__init__(executor, method, *args, **kwargs)

        self.hash2id = uid.hash2id
        self.id2hash = uid.id2hash


class Chunk2DocRankDriver(BaseRankDriver):
    """Extract matches score from chunks and use the executor to compute the rank and assign the resulting matches to the
    level above.

    Note that it traverses on ``chunks`` not on ``matches``

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

    def __init__(self, traversal_paths: Tuple[str] = ('c',), *args, **kwargs):
        super().__init__(traversal_paths=traversal_paths, *args, **kwargs)

    def _apply_all(self, docs: Iterable['jina_pb2.Document'], context_doc: 'jina_pb2.Document', *args,
                   **kwargs) -> None:
        """
        :param docs: the chunks of the ``context_doc``, they are at depth_level ``k``
        :param context_doc: the owner of ``docs``, it is at depth_level ``k-1``
        :return:
        """

        match_idx = []  # type: List[Tuple[int, int, int, float]]
        query_chunk_meta = {}  # type: Dict[int, Dict]
        match_chunk_meta = {}  # type: Dict[int, Dict]
        for c in docs:
            for match in c.matches:
                match_idx.append(
                    (self.id2hash(match.parent_id),
                     self.id2hash(match.id),
                     self.id2hash(c.id),
                     match.score.value)
                )
                query_chunk_meta[self.id2hash(c.id)] = pb_obj2dict(c, self.exec.required_keys)
                match_chunk_meta[self.id2hash(match.id)] = pb_obj2dict(match, self.exec.required_keys)

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
            for doc_hash, score in docs_scores:
                r = context_doc.matches.add()
                r.id = self.hash2id(doc_hash)
                r.granularity = context_doc.granularity
                r.adjacency = context_doc.adjacency + 1
                r.score.ref_id = context_doc.id  # label the score is computed against doc
                r.score.value = score
                r.score.op_name = exec.__class__.__name__


class CollectMatches2DocRankDriver(BaseRankDriver):
    """This Driver is intended to take a `document` with matches at a `given level depth > 0`, clear those matches and substitute
    these matches by the documents at a lower depth level.
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
        matches: indexed full documents (documents of level depth 0).
    `
    Using this Driver before querying a Binary Index with full binary document data can be very useful to implement a search system.
    """

    def __init__(self, traversal_paths: Tuple[str] = ('m',), *args, **kwargs):
        super().__init__(traversal_paths=traversal_paths, *args, **kwargs)

    def _apply_all(self, docs: Iterable['jina_pb2.Document'], context_doc: 'jina_pb2.Document', *args,
                   **kwargs) -> None:
        """

        :param docs: the chunks of the ``context_doc``, they are at depth_level ``k``
        :param context_doc: the owner of ``docs``, it is at depth_level ``k-1``
        :return:
        """

        # if at the top-level already, no need to aggregate further
        if context_doc is None:
            return

        match_idx = []
        query_chunk_meta = {}
        match_chunk_meta = {}
        # doc_id_to_match_map = {}
        for match in docs:
            # doc_id_to_match_map[match.id] = index
            match_idx.append((
                self.id2hash(match.parent_id),
                self.id2hash(match.id),
                self.id2hash(context_doc.id),
                match.score.value
            ))
            query_chunk_meta[self.id2hash(context_doc.id)] = pb_obj2dict(context_doc, self.exec.required_keys)
            match_chunk_meta[self.id2hash(match.id)] = pb_obj2dict(match, self.exec.required_keys)

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
            for doc_hash, score in docs_scores:
                r = context_doc.matches.add()
                r.id = self.hash2id(doc_hash)
                r.score.ref_id = context_doc.id  # label the score is computed against doc
                r.score.value = score
                r.score.op_name = exec.__class__.__name__


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

    def _apply_all(self, docs: Iterable['jina_pb2.Document'], context_doc: 'jina_pb2.Document', *args,
                   **kwargs) -> None:
        """ Call executer for score and sort afterwards here. """

        # if at the top-level already, no need to aggregate further
        query_meta = pb_obj2dict(context_doc, self.exec.required_keys)

        old_match_scores = {self.id2hash(match.id): match.score.value for match in docs}
        match_meta = {self.id2hash(match.id): pb_obj2dict(match, self.exec.required_keys) for match in docs}
        # if there are no matches, no need to sort them
        if not old_match_scores:
            return

        new_match_scores = self.exec_fn(query_meta, old_match_scores, match_meta)
        self._sort_matches_in_place(context_doc, new_match_scores)

    def _sort_matches_in_place(self, context_doc: 'jina_pb2.Document', match_scores: 'np.ndarray') -> None:
        sorted_scores = self._sort(match_scores)
        old_matches = {match.id: match for match in context_doc.matches}
        context_doc.ClearField('matches')
        for match_hash, score in sorted_scores:
            new_match = context_doc.matches.add()
            new_match.CopyFrom(old_matches[self.hash2id(match_hash)])
            new_match.score.value = score
            new_match.score.op_name = exec.__class__.__name__

    def _sort(self, docs_scores: 'np.ndarray') -> 'np.ndarray':
        return np.sort(docs_scores, order=Match2DocRanker.COL_SCORE)[::-1]
