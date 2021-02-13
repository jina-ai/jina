__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Tuple, Optional

from . import BaseExecutableDriver, FastRecursiveMixin
from ..types.document import Document

if False:
    from .. import DocumentSet


class SegmentDriver(FastRecursiveMixin, BaseExecutableDriver):
    """Drivers inherited from this Driver will bind :meth:`segment` by default """

    def __init__(
            self,
            executor: Optional[str] = None,
            method: str = 'segment',
            traversal_paths: Tuple[str] = ('r',),
            *args,
            **kwargs
    ):
        super().__init__(executor, method, traversal_paths=traversal_paths, *args, **kwargs)

    def _apply_all(self, docs: 'DocumentSet', *args, **kwargs):
        for doc in docs:
            _args_dict = doc.get_attrs(*self.exec.required_keys)
            ret = self.exec_fn(**_args_dict)
            if ret:
                self._update(doc, ret)

    @staticmethod
    def _update(doc, ret):
        for r in ret:
            with Document(length=len(ret), **r) as c:
                if not c.mime_type:
                    c.mime_type = doc.mime_type
            doc.chunks.append(c)
