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
        self._is_apply = False


class Chunk2DocRankDriver(BaseRankDriver):
    """Extract chunk-level score and use the executor to compute the doc-level score

    In multi-level document, this aggregates kth level score back to (k-1)th level. It is recursive until we hit level-0
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.recursion_order = 'post'

    def _apply_all(self, docs: 'jina_pb2.Document', context_doc: 'jina_pb2.Document', *args, **kwargs):
        """

        :param docs: the chunks of the ``context_doc``, they are at depth_level ``k``
        :param context_doc: the owner of ``docs``, it is at depth_level ``k-1``
        :param args:
        :param kwargs:
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
                r.level_depth = context_doc.level_depth  # the match and doc are always on the same level_depth
                r.score.ref_id = context_doc.id  # label the score is computed against doc
                r.score.value = score
                r.score.op_name = exec.__class__.__name__
