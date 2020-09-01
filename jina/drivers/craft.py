__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Dict, Set, List

from . import BaseExecutableDriver
from .helper import array2pb, pb_obj2dict
from ..counter import RandomUintCounter, SimpleCounter
from ..proto import jina_pb2


class CraftDriver(BaseExecutableDriver):
    """Drivers inherited from this Driver will bind :meth:`craft` by default """

    def __init__(self, executor: str = None, method: str = 'craft', *args, **kwargs):
        super().__init__(executor, method, *args, **kwargs)
        self._is_apply_all = False

    def _apply(self, doc: 'jina_pb2.Document', *args, **kwargs):
        ret = self.exec_fn(**pb_obj2dict(doc, self.exec.required_keys))
        if ret:
            self.set_doc_attr(doc, ret)

    def set_doc_attr(self, doc: 'jina_pb2.Document', doc_info: Dict, protected_keys: Set = None):
        for k, v in doc_info.items():
            if k == 'blob':
                if isinstance(v, jina_pb2.NdArray):
                    doc.blob.CopyFrom(v)
                else:
                    doc.blob.CopyFrom(array2pb(v))
            elif isinstance(protected_keys, dict) and k in protected_keys:
                self.logger.warning(f'you are assigning a {k} in {self.exec.__class__}, '
                                    f'is it intentional? {k} will be overwritten by {self.__class__} '
                                    f'anyway.')
            elif isinstance(v, list) or isinstance(v, tuple):
                doc.ClearField(k)
                getattr(doc, k).extend(v)
            else:
                setattr(doc, k, v)


class SegmentDriver(CraftDriver):
    """Segment document into chunks using the executor
    """

    def __init__(self, first_chunk_id: int = 0, random_chunk_id: bool = True,
                 level_names: List[str] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if isinstance(level_names, list) and (self._depth_end - self._depth_start + 1) != len(self.level_names):
            self.level_names = level_names
        elif level_names is None:
            pass
        else:
            raise ValueError(f'bad level names: {level_names}, the length of it should match the recursive depth + 1')

        # for adding new chunks, preorder is safer
        self.recursion_order = 'pre'
        self._counter = RandomUintCounter() if random_chunk_id else SimpleCounter(first_chunk_id)
        self._protected_fields = {'length', 'id', 'parent_id', 'granularity', 'mime_type'}

    def _apply(self, doc: 'jina_pb2.Document', *args, **kwargs):
        _args_dict = pb_obj2dict(doc, self.exec.required_keys)
        ret = self.exec_fn(**_args_dict)
        if ret:
            for r in ret:
                c = doc.chunks.add()
                self.set_doc_attr(c, r, self._protected_fields)
                c.length = len(ret)
                c.id = next(self._counter)
                c.parent_id = doc.id
                c.granularity = doc.granularity + 1
                c.mime_type = doc.mime_type
        else:
            self.logger.warning(f'doc {doc.id} at level {doc.granularity} gives no chunk')
