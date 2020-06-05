__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

# lift the chunk-level topk to doc-level topk
import numpy as np

from . import BaseExecutableDriver
from .helper import pb_obj2dict


class BaseRankDriver(BaseExecutableDriver):
    """Drivers inherited from this Driver will bind :meth:`craft` by default """

    def __init__(self, executor: str = None, method: str = 'score', *args, **kwargs):
        super().__init__(executor, method, *args, **kwargs)


class Chunk2DocRankDriver(BaseRankDriver):
    """Extract chunk-level score and use the executor to compute the doc-level score

    """

    def __call__(self, *args, **kwargs):
        exec = self.exec

        for d in self.req.docs:  # d is a query in this context, i.e. for each query, compute separately
            match_idx = []
            query_chunk_meta = {}
            match_chunk_meta = {}
            for c in d.chunks:
                for k in c.topk_results:
                    match_idx.append((k.match_chunk.doc_id, k.match_chunk.chunk_id, c.chunk_id, k.score.value))
                    query_chunk_meta[c.chunk_id] = pb_obj2dict(c, exec.required_keys)
                    match_chunk_meta[k.match_chunk.chunk_id] = pb_obj2dict(k.match_chunk, exec.required_keys)

            # np.uint32 uses 32 bits. np.float32 uses 23 bit mantissa, so integer greater than 2^23 will have their
            # least significant bits truncated.

            if not match_idx:
                continue

            match_idx = np.array(match_idx, dtype=np.float64)

            doc_idx = self.exec_fn(match_idx, query_chunk_meta, match_chunk_meta)

            for _d in doc_idx:
                r = d.topk_results.add()
                r.match_doc.doc_id = int(_d[0])
                r.score.value = _d[1]
                r.score.op_name = exec.__class__.__name__
