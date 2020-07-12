__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import ctypes
import random
from typing import Dict

from . import BaseExecutableDriver, BaseDriver
from .helper import array2pb, pb_obj2dict, pb2array
from ..proto import jina_pb2


class BaseCraftDriver(BaseExecutableDriver):
    """Drivers inherited from this Driver will bind :meth:`craft` by default """

    def __init__(self, executor: str = None, method: str = 'craft', *args, **kwargs):
        super().__init__(executor, method, *args, **kwargs)

    def set_chunk(self, chunk: 'jina_pb2.Chunk', chunk_info: Dict, new_chunk_id: bool = True):
        for k, v in chunk_info.items():
            if k == 'blob':
                if isinstance(v, jina_pb2.NdArray):
                    chunk.blob.CopyFrom(v)
                else:
                    chunk.blob.CopyFrom(array2pb(v))
            elif k == 'chunk_id':
                self.logger.warning(f'you are assigning a chunk_id in in {self.exec.__class__}, '
                                    f'is it intentional? chunk_id will be override by {self.__class__} '
                                    f'anyway')
            elif isinstance(v, list) or isinstance(v, tuple):
                chunk.ClearField(k)
                getattr(chunk, k).extend(v)
            else:
                setattr(chunk, k, v)
        if new_chunk_id:
            chunk.chunk_id = random.randint(0, ctypes.c_uint(-1).value)


class ChunkCraftDriver(BaseCraftDriver):
    """Craft the chunk-level information on given keys using the executor

    """

    def __call__(self, *args, **kwargs):
        no_chunk_docs = []

        for d in self.req.docs:
            for c in d.chunks:
                _args_dict = pb_obj2dict(c, self.exec.required_keys)
                if 'blob' in self.exec.required_keys:
                    _args_dict['blob'] = pb2array(c.blob)
                ret = self.exec_fn(**_args_dict)
                if isinstance(ret, dict):  #: 1-to-1
                    self.set_chunk(c, ret, new_chunk_id=False)
                elif isinstance(ret, list):  #: 1-to-many
                    d.chunks.remove(c)  # remove the current one?
                    for c_dict in ret:
                        self.set_chunk(d.chunks.add(), c_dict)
            d.length = len(d.chunks)

        if no_chunk_docs:
            self.logger.warning(f'these docs contain no chunk: {no_chunk_docs}')


class DocCraftDriver(BaseCraftDriver):
    """Craft the doc-level information on given keys using the executor

    """

    def __call__(self, *args, **kwargs):
        for d in self.req.docs:
            _args_dict = pb_obj2dict(d, self.exec.required_keys)
            if 'blob' in self.exec.required_keys:
                _args_dict['blob'] = pb2array(d.blob)
            ret = self.exec_fn(**_args_dict)
            if ret:
                for k, v in ret.items():
                    if k == 'blob':
                        if isinstance(v, jina_pb2.NdArray):
                            d.blob.CopyFrom(v)
                        else:
                            d.blob.CopyFrom(array2pb(v))
                    else:
                        setattr(d, k, v)


class SegmentDriver(BaseCraftDriver):
    """Segment document into chunks using the executor

    .. note::
        ``chunk_id`` is auto-assign incrementally or randomly depends on ``first_chunk_id`` and ``random_chunk_id``.
        no need to self-assign it in your segmenter
    """

    def __init__(
            self, first_chunk_id: int = 0, random_chunk_id: bool = True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.first_chunk_id = first_chunk_id
        self.random_chunk_id = random_chunk_id

    def __call__(self, *args, **kwargs):
        for d in self.req.docs:
            _args_dict = pb_obj2dict(d, self.exec.required_keys)
            if 'blob' in self.exec.required_keys:
                _args_dict['blob'] = pb2array(d.blob)
            ret = self.exec_fn(**_args_dict)
            if ret:
                for r in ret:
                    c = d.chunks.add()
                    self.set_chunk(c, r)
                    c.length = len(ret)
                    c.chunk_id = self.first_chunk_id if not self.random_chunk_id else random.randint(0, ctypes.c_uint(
                        -1).value)
                    c.doc_id = d.doc_id
                    c.mime_type = d.mime_type
                    self.first_chunk_id += 1
                d.length = len(ret)
            else:
                self.logger.warning('doc %d gives no chunk' % d.doc_id)


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
            c.doc_id = d.doc_id
            c.mime_type = d.mime_type
            self.first_chunk_id += 1
            d.length = 1
