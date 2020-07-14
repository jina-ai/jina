__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import ctypes
import random
from typing import Dict, Set, List

from . import BaseExecutableDriver, BaseDriver
from .helper import array2pb, pb_obj2dict
from ..proto import jina_pb2


class BaseCraftDriver(BaseExecutableDriver):
    """Drivers inherited from this Driver will bind :meth:`craft` by default """

    def __init__(self, executor: str = None, method: str = 'craft', *args, **kwargs):
        super().__init__(executor, method, *args, **kwargs)

    def apply(self, doc: 'jina_pb2.Document', *args, **kwargs):
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
                self.logger.warning(f'you are assigning a chunk_id in in {self.exec.__class__}, '
                                    f'is it intentional? {k} will be override by {self.__class__} '
                                    f'anyway')
            elif isinstance(v, list) or isinstance(v, tuple):
                doc.ClearField(k)
                getattr(doc, k).extend(v)
            else:
                setattr(doc, k, v)


class SegmentDriver(BaseCraftDriver):
    """Segment document into chunks using the executor
    """

    def __init__(self, level_names: List[str] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if isinstance(level_names, list) and (self._depth_end - self._depth_start + 1) != len(self.level_names):
            self.level_names = level_names
        elif self.level_names is None:
            pass
        else:
            raise ValueError(f'bad level names: {level_names}, the length of it should match the recursive depth + 1')

        # for adding new chunks, preorder is safer
        self.recursion_order = 'pre'

    def apply(self, doc: 'jina_pb2.Document', *args, **kwargs):
        _args_dict = pb_obj2dict(doc, self.exec.required_keys)
        ret = self.exec_fn(**_args_dict)
        if ret:
            for r in ret:
                c = doc.chunks.add()
                self.set_doc_attr(c, r, {'length', 'id', 'parent_id', 'level_depth', 'mime_type'})
                c.length = len(ret)
                c.id = random.randint(0, ctypes.c_uint(-1).value)
                c.parent_id = doc.id
                c.level_depth = doc.level_depth + 1
                c.mime_type = doc.mime_type
            doc.length = len(ret)
        else:
            self.logger.warning(f'doc {doc.id} at level {doc.level_depth} gives no chunk')


class UnarySegmentDriver(BaseDriver):
    """ The :class:`UnarySegmentDriver` copies whatever ``content`` set in the doc level to the chunk level, hence
    creates a single-chunk document
    """

    def __init__(
            self, first_chunk_id: int = 0, random_chunk_id: bool = True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.first_chunk_id = first_chunk_id
        self.random_chunk_id = random_chunk_id

    def __call__(self, *args, **kwargs):
        for d in self.req.docs:
            c = d.chunks.add()
            c.length = 1
            d_type = d.WhichOneof('content')
            if d_type in {'blob'}:
                getattr(c, d_type).CopyFrom(getattr(d, d_type))
            else:
                setattr(c, d_type, getattr(d, d_type))
            c.chunk_id = self.first_chunk_id if not self.random_chunk_id else random.randint(0, ctypes.c_uint(
                -1).value)
            c.parent_id = d.id
            c.mime_type = d.mime_type
            self.first_chunk_id += 1
            d.length = 1
