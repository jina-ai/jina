__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Dict, Iterable, Set, Tuple

from . import BaseExecutableDriver
from .helper import array2pb, pb_obj2dict
from ..proto import jina_pb2, uid


class CraftDriver(BaseExecutableDriver):
    """Drivers inherited from this Driver will bind :meth:`craft` by default """

    def __init__(self, executor: str = None, method: str = 'craft', *args, **kwargs):
        super().__init__(executor, method, *args, **kwargs)

    def _apply_all(self, docs: Iterable['jina_pb2.Document'], *args, **kwargs):
        for doc in docs:
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
            elif isinstance(v, dict):
                getattr(doc, k).update(v)
            else:
                setattr(doc, k, v)


class SegmentDriver(CraftDriver):
    """Segment document into chunks using the executor
    """

    def __init__(
            self,
            traversal_paths: Tuple[str] = ('r',),
            *args,
            **kwargs
    ):
        super().__init__(traversal_paths=traversal_paths, *args, **kwargs)

        self._protected_fields = {'length', 'id', 'parent_id', 'granularity'}

    def _apply_all(self, docs: Iterable['jina_pb2.Document'], *args, **kwargs):
        for doc in docs:
            _args_dict = pb_obj2dict(doc, self.exec.required_keys)
            ret = self.exec_fn(**_args_dict)
            if ret:
                for r in ret:
                    c = doc.chunks.add()
                    self.set_doc_attr(c, r, self._protected_fields)
                    c.length = len(ret)
                    c.parent_id = doc.id
                    c.granularity = doc.granularity + 1
                    if not c.mime_type:
                        c.mime_type = doc.mime_type
                    c.id = uid.new_doc_id(c)

            else:
                self.logger.warning(f'doc {doc.id} at level {doc.granularity} gives no chunk')
