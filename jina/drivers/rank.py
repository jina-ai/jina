__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

# lift the chunk-level topk to doc-level topk
from typing import Iterable

import numpy as np

from . import BaseExecutableDriver
from .helper import pb_obj2dict

if False:
    from ..proto import jina_pb2


class BaseRankDriver(BaseExecutableDriver):
    """Drivers inherited from this Driver will bind :meth:`rank` by default """

    def __init__(self, executor: str = None, method: str = 'score', *args, **kwargs):
        super().__init__(executor, method, *args, **kwargs)
        self._is_apply = False


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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, recur_on='chunks', **kwargs)
        self.recursion_order = 'post'

    def _apply_all(self, docs: Iterable['jina_pb2.Document'], context_doc: 'jina_pb2.Document', *args, **kwargs):
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
        for c in docs:
            for match in c.matches:
                match_idx.append((match.parent_id, match.id, c.id, match.score.value))
                query_chunk_meta[c.id] = pb_obj2dict(c, self.exec.required_keys)
                match_chunk_meta[match.id] = pb_obj2dict(match, self.exec.required_keys)

        # np.uint32 uses 32 bits. np.float32 uses 23 bit mantissa, so integer greater than 2^23 will have their
        # least significant bits truncated.
        if match_idx:
            match_idx = np.array(match_idx, dtype=np.float64)

            docs_scores = self.exec_fn(match_idx, query_chunk_meta, match_chunk_meta)
            for doc_id, score in docs_scores:
                r = context_doc.matches.add()
                r.id = int(doc_id)
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.recursion_order = 'post'

    def _apply_all(self, docs: Iterable['jina_pb2.Document'], context_doc: 'jina_pb2.Document', *args, **kwargs):
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
        for match in context_doc.matches:
            # doc_id_to_match_map[match.id] = index
            match_idx.append((match.parent_id, match.id, context_doc.id, match.score.value))
            query_chunk_meta[context_doc.id] = pb_obj2dict(context_doc, self.exec.required_keys)
            match_chunk_meta[match.id] = pb_obj2dict(match, self.exec.required_keys)

        if match_idx:
            match_idx = np.array(match_idx, dtype=np.float64)

            docs_scores = self.exec_fn(match_idx, query_chunk_meta, match_chunk_meta)
            # These ranker will change the current matches
            context_doc.ClearField('matches')
            for doc_id, score in docs_scores:
                r = context_doc.matches.add()
                r.id = int(doc_id)
                r.score.ref_id = context_doc.id  # label the score is computed against doc
                r.score.value = score
                r.score.op_name = exec.__class__.__name__
