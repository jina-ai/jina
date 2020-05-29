__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import ctypes
import random
import urllib.parse
import urllib.request

from . import BaseExecutableDriver, BaseDriver
from .helper import array2pb, pb_obj2dict, pb2array
from ..proto import jina_pb2


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
                            if isinstance(v, jina_pb2.NdArray):
                                c.blob.CopyFrom(v)
                            else:
                                c.blob.CopyFrom(array2pb(v))
                        else:
                            setattr(c, k, v)
                    continue
                elif isinstance(ret, list):
                    _chunks_to_add.extend(ret)
            for c_dict in _chunks_to_add:
                c = d.chunks.add()
                for k, v in c_dict.items():
                    if k == 'blob':
                        if isinstance(v, jina_pb2.NdArray):
                            c.blob.CopyFrom(v)
                        else:
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
            _args_dict = pb_obj2dict(d, self.exec.required_keys)
            if 'blob' in self.exec.required_keys:
                _args_dict['blob'] = pb2array(d.blob)
            ret = self.exec_fn(**_args_dict)
            if ret:
                for k, v in ret.items():
                    setattr(d, k, v)


class MIMEDriver(BaseDriver):
    """Guessing the MIME type based on the doc content

    Can be used before/after :class:`DocCraftDriver` to fill MIME type
    """

    def __init__(self, default_mime: str = 'application/octet-stream', *args, **kwargs):
        """

        :param default_mime: for text documents without a specific subtype, text/plain should be used.
            Similarly, for binary documents without a specific or known subtype, application/octet-stream should be used.
        """
        super().__init__(*args, **kwargs)
        self.default_mime = default_mime

    def __call__(self, *args, **kwargs):
        import mimetypes

        for d in self.req.docs:
            # mime_type may be a file extension
            m_type = d.mime_type
            if m_type and m_type not in mimetypes.types_map.values():
                m_type = mimetypes.guess_type(f'*.{m_type}')[0]

            d_type = d.WhichOneof('content')
            if not m_type and d_type:  # for ClientInputType=PROTO, d_type could be empty
                if d_type == 'buffer':
                    d_content = getattr(d, d_type)
                    # d.mime_type = 'application/octet-stream'  # default by IANA standard
                    try:
                        import magic
                        m_type = magic.from_buffer(d_content, mime=True)
                    except (ImportError, ModuleNotFoundError):
                        self.logger.warning(f'can not sniff the MIME type '
                                            f'MIME sniffing requires pip install "jina[http]" '
                                            f'and brew install libmagic (Mac)/ apt-get install libmagic1 (Linux)')
                    except Exception as ex:
                        self.logger.warning(f'can not sniff the MIME type due to the exception {ex}')
                elif d_type in {'file_path', 'data_uri'}:
                    d_content = getattr(d, d_type)
                    m_type = mimetypes.guess_type(d_content)[0]
                    if not m_type and urllib.parse.urlparse(d_content).scheme in {'http', 'https', 'data'}:
                        tmp = urllib.request.urlopen(d_content)
                        m_type = tmp.info().get_content_type()

            if m_type:
                d.mime_type = m_type
            else:
                d.mime_type = self.default_mime
                self.logger.warning(f'can not determine the MIME type, set to default {self.default_mime}')


class SegmentDriver(BaseCraftDriver):
    """Segment document into chunks using the executor

    .. note::
        ``chunk_id`` is auto-assign incrementally or randomly depends on ``first_chunk_id`` and ``random_chunk_id``.
        no need to self-assign it in your segmenter
    """

    def __init__(
            self, first_chunk_id: int = 0, random_chunk_id: bool = True, save_buffer: bool = False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.first_chunk_id = first_chunk_id
        self.random_chunk_id = random_chunk_id
        self.save_buffer = save_buffer

    def __call__(self, *args, **kwargs):
        for d in self.req.docs:
            _args_dict = pb_obj2dict(d, self.exec.required_keys)
            if 'blob' in self.exec.required_keys:
                _args_dict['blob'] = pb2array(d.blob)
            ret = self.exec_fn(**_args_dict)
            if ret:
                for r in ret:
                    c = d.chunks.add()
                    for k, v in r.items():
                        if k == 'blob':
                            if isinstance(v, jina_pb2.NdArray):
                                c.blob.CopyFrom(v)
                            else:
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
                    c.mime_type = d.mime_type
                    self.first_chunk_id += 1
                d.length = len(ret)
                if self.save_buffer:
                    d.meta_info = d.buffer
            else:
                self.logger.warning('doc %d gives no chunk' % d.doc_id)


class UnarySegmentDriver(BaseDriver):
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
            getattr(c, d_type).CopyFrom(getattr(d, d_type))
            c.chunk_id = self.first_chunk_id if not self.random_chunk_id else random.randint(0, ctypes.c_uint(
                -1).value)
            c.doc_id = d.doc_id
            c.mime_type = d.mime_type
            self.first_chunk_id += 1
            d.length = 1
