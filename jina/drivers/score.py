# lift the chunk-level topk to doc-level topk
import numpy as np

from . import BaseExecutorDriver
from .helper import pb_obj2dict


class Chunk2DocScoreDriver(BaseExecutorDriver):
    """Extract chunk-level score and use the executor to compute the doc-level score

    It requires ``ctx`` has :class:`jina.executors.rankers.BaseRanker` equipped.
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

            match_idx = np.array(match_idx, dtype=np.float32)

            doc_idx = self.exec_fn(match_idx, query_chunk_meta, match_chunk_meta)

            for _d in doc_idx:
                r = d.topk_results.add()
                r.match_doc.doc_id = int(_d[0])
                r.score.value = _d[1]
                r.score.op_name = exec.__class__.__name__
