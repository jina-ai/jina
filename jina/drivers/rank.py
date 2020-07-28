__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

# lift the chunk-level topk to doc-level topk
import numpy as np

from . import BaseExecutableDriver
from .helper import pb_obj2dict

if False:
    from ..proto import jina_pb2


class BaseRankDriver(BaseExecutableDriver):
    """Drivers inherited from this Driver will bind :meth:`craft` by default """

    def __init__(self, executor: str = None, method: str = 'score', *args, **kwargs):
        super().__init__(executor, method, *args, **kwargs)


class Chunk2DocRankDriver(BaseRankDriver):
    """Extract chunk-level score and use the executor to compute the doc-level score

    In multi-level document, this aggregates kth level score back to (k-1)th level. It is recursive until we hit level-0
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.recursion_order = 'post'

    def _apply(self, doc: 'jina_pb2.Document', *args, **kwargs):
        match_idx = []
        query_chunk_meta = {}
        match_chunk_meta = {}
        for c in doc.chunks:
            for k in c.matches:
                match_idx.append((k.id, k.parent_id, c.id, k.score.value))
                query_chunk_meta[c.id] = pb_obj2dict(c, self.exec.required_keys)
                match_chunk_meta[k.id] = pb_obj2dict(k, self.exec.required_keys)

        # np.uint32 uses 32 bits. np.float32 uses 23 bit mantissa, so integer greater than 2^23 will have their
        # least significant bits truncated.

        if match_idx:
            match_idx = np.array(match_idx, dtype=np.float64)

            docs_scores = self.exec_fn(match_idx, query_chunk_meta, match_chunk_meta)
            for doc_id, score in docs_scores:
                r = doc.matches.add()
                r.id = int(doc_id)
                r.level_depth = doc.level_depth  # the match and doc are always on the same level_depth
                r.score.ref_id = doc.id  # label the score is computed against doc
                r.score.value = score
                r.score.op_name = exec.__class__.__name__


class DocRankDriver(BaseRankDriver):
    """Score documents' matches based on their features and the query document
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.recursion_order = 'post'

    def _apply(self, doc: 'jina_pb2.Document', *args, **kwargs):
        # Score all documents' matches
        match_idx = []
        query_doc_meta = {doc.id: pb_obj2dict(doc, self.exec.required_keys)}
        match_doc_meta = {}

        for match in doc.matches:
            match_idx.append(match.id)
            match_doc_meta[match.id] = pb_obj2dict(match, self.exec.required_keys)

        if match_idx:
            match_idx = np.array(match_idx, dtype=np.float64)
            doc_scores = self.exec_fn(match_idx, query_doc_meta, match_doc_meta)

            for idx, _, score in enumerate(doc_scores):
                doc.matches[idx].score.value = score
                doc.matches[idx].score.op_name = exec.__class__.__name__
