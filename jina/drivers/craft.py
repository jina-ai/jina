__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import ctypes
import random

from . import BaseExecutableDriver
from .helper import array2pb, pb_obj2dict, pb2array


class BaseCraftDriver(BaseExecutableDriver):
    """Drivers inherited from this Driver will bind :meth:`craft` by default """

    def __init__(self, executor: str = None, method: str = 'craft', *args, **kwargs):
        super().__init__(executor, method, *args, **kwargs)


class ChunkCraftDriver(BaseCraftDriver):
    """Craft the chunk-level information on given keys using the executor

    """

    def __call__(self, *args, **kwargs):
        no_chunk_docs = []

        for d in self.req.docs:
            if not d.chunks:
                no_chunk_docs.append(d.doc_id)
                continue
            _chunks_to_add = []
            for c in d.chunks:
                _args_dict = pb_obj2dict(c, self.exec.required_keys)
                if 'blob' in self.exec.required_keys:
                    _args_dict['blob'] = pb2array(c.blob)
                ret = self.exec_fn(**_args_dict)
                if isinstance(ret, dict):
                    for k, v in ret.items():
                        if k == 'blob':
                            c.blob.CopyFrom(array2pb(v))
                        else:
                            setattr(c, k, v)
                    continue
                if isinstance(ret, list):
                    for chunk_dict in ret:
                        _chunks_to_add.append(chunk_dict)
            if len(_chunks_to_add) > 0:
                for c_dict in _chunks_to_add:
                    c = d.chunks.add()
                    for k, v in c_dict.items():
                        if k == 'blob':
                            c.blob.CopyFrom(array2pb(v))
                        elif k == 'chunk_id':
                            self.logger.warning(f'you are assigning a chunk_id in in {self.exec.__class__}, '
                                                f'is it intentional? chunk_id will be override by {self.__class__} '
                                                f'anyway')
                        else:
                            setattr(c, k, v)
                    c.length = len(_chunks_to_add) + len(d.chunks)
                    c.chunk_id = random.randint(0, ctypes.c_uint(-1).value)
            d.length = len(_chunks_to_add) + len(d.chunks)

        if no_chunk_docs:
            self.logger.warning('these docs contain no chunk: %s' % no_chunk_docs)


class DocCraftDriver(BaseCraftDriver):
    """Craft the doc-level information on given keys using the executor

    """

    def __call__(self, *args, **kwargs):
        for d in self.req.docs:
            ret = self.exec_fn(**pb_obj2dict(d, self.exec.required_keys))
            for k, v in ret.items():
                setattr(d, k, v)


class SegmentDriver(BaseCraftDriver):
    """Segment document into chunks using the executor

    .. note::
        ``chunk_id`` is auto-assign incrementally or randomly depends on ``first_chunk_id`` and ``random_chunk_id``.
        no need to self-assign it in your segmenter
    """

    def __init__(
            self, first_chunk_id: int = 0, random_chunk_id: bool = True, save_raw_bytes: bool = False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.first_chunk_id = first_chunk_id
        self.random_chunk_id = random_chunk_id
        self.save_raw_bytes = save_raw_bytes

    def __call__(self, *args, **kwargs):
        for d in self.req.docs:
            ret = self.exec_fn(**pb_obj2dict(d, self.exec.required_keys))
            if ret:
                for r in ret:
                    c = d.chunks.add()
                    for k, v in r.items():
                        if k == 'blob':
                            c.blob.CopyFrom(array2pb(v))
                        elif k == 'chunk_id':
                            self.logger.warning(f'you are assigning a chunk_id in in {self.exec.__class__}, '
                                                f'is it intentional? chunk_id will be override by {self.__class__} '
                                                f'anyway')
                        else:
                            setattr(c, k, v)
                    c.length = len(ret)
                    c.chunk_id = self.first_chunk_id if not self.random_chunk_id else random.randint(0, ctypes.c_uint(
                        -1).value)
                    c.doc_id = d.doc_id
                    self.first_chunk_id += 1
                d.length = len(ret)
                if self.save_raw_bytes:
                    d.meta_info = d.raw_bytes
            else:
                self.logger.warning('doc %d gives no chunk' % d.doc_id)
