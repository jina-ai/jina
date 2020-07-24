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

    def apply(self, doc: 'jina_pb2.Document', *args, **kwargs):
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

            doc_idx = self.exec_fn(match_idx, query_chunk_meta, match_chunk_meta)
            for _d in doc_idx:
                r = doc.matches.add()
                r.id = int(_d[0])
                r.score.ref_id = doc.id  # label the score is computed against doc
                r.score.value = _d[1]
                r.score.op_name = exec.__class__.__name__
