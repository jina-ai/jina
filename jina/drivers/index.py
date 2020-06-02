__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import numpy as np

from . import BaseExecutableDriver
from .helper import extract_chunks
from typing import Union, List, Tuple


class BaseIndexDriver(BaseExecutableDriver):
    """Drivers inherited from this Driver will bind :meth:`craft` by default """

    def __init__(self, executor: str = None, method: str = 'add', *args, **kwargs):
        super().__init__(executor, method, *args, **kwargs)


class VectorIndexDriver(BaseIndexDriver):
    """Extract chunk-level embeddings and add it to the executor

    """
    def __init__(self, filter_by: Union[List[str], Tuple[str]] = [], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filter_by = filter_by

    def __call__(self, *args, **kwargs):
        embed_vecs, chunk_pts, no_chunk_docs, bad_chunk_ids = \
            extract_chunks(self.req.docs, self.filter_by, embedding=True)

        if no_chunk_docs:
            self.pea.logger.warning('these docs contain no chunk: %s' % no_chunk_docs)

        if bad_chunk_ids:
            self.pea.logger.warning('these bad chunks can not be added: %s' % bad_chunk_ids)

        if chunk_pts:
            self.exec_fn(np.array([c.chunk_id for c in chunk_pts]), np.stack(embed_vecs))


class KVIndexDriver(BaseIndexDriver):
    """Serialize the documents/chunks in the request to key-value JSON pairs and write it using the executor

    Number of key-value pairs depends on the ``level``

         - ``level=chunk``: D x C
         - ``level=doc``: D
         - ``level=all``: D x C + D

    where:
        - D is the number of queries
        - C is the number of chunks per query/doc
    """

    def __init__(self, level: str, filter_by: Union[List[str], Tuple[str]] = [], *args, **kwargs):
        """

        :param level: index level "chunk" or "doc", or "all"
        :param args:
        :param kwargs:
        """
        super().__init__(*args, **kwargs)
        self.level = level
        self.filter_by = filter_by

    def __call__(self, *args, **kwargs):
        from google.protobuf.json_format import MessageToJson
        if self.level == 'doc':
            content = {f'd{d.doc_id}': MessageToJson(d) for d in self.req.docs}
        elif self.level == 'chunk':
            content = {f'c{c.chunk_id}': MessageToJson(c) for d in self.req.docs for c in d.chunks
                       if self.filter_by and c.field_name in self.filter_by}
        elif self.level == 'all':
            content = {f'c{c.chunk_id}': MessageToJson(c) for d in self.req.docs for c in d.chunks
                       if self.filter_by and c.field_name in self.filter_by}
            content.update({f'd{d.doc_id}': MessageToJson(d) for d in self.req.docs})
        else:
            raise TypeError(f'level={self.level} is not supported, must choose from "chunk" or "doc" ')
        if content:
            self.exec_fn(content)


class DocKVIndexDriver(KVIndexDriver):
    """A shortcut of :class:`MergeTopKDriver` with ``level=chunk``"""

    def __init__(self, level: str = 'doc', *args, **kwargs):
        super().__init__(level, *args, **kwargs)


class ChunkKVIndexDriver(KVIndexDriver):
    def __init__(self,
                 level: str = 'chunk', filter_by: Union[str, List[str], Tuple[str]] = None, *args, **kwargs):
        super().__init__(level, *args, **kwargs)
        self.filter_by = filter_by if self.filter_by else []

    def __call__(self, *args, **kwargs):
        from google.protobuf.json_format import MessageToJson
        content = {
            f'c{c.chunk_id}': MessageToJson(c)
            for d in self.req.docs for c in d.chunks
            if len(self.filter_by) > 0 and c.field_name in self.filter_by}
        if content:
            self.exec_fn(content)
