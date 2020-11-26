__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Tuple

from . import BaseExecutableDriver
from ..types.document import Document

if False:
    from ..types.document import DocumentSet


class CraftDriver(BaseExecutableDriver):
    """Drivers inherited from this Driver will bind :meth:`craft` by default """

    def __init__(self, executor: str = None, method: str = 'craft', *args, **kwargs):
        super().__init__(executor, method, *args, **kwargs)

    def _apply_all(self, docs: 'DocumentSet', *args, **kwargs):
        for doc in docs:
            _args_dict = doc.get_attrs(*self.exec.required_keys)
            ret = self.exec_fn(**_args_dict)
            if ret:
                self.update(doc, ret)

    @staticmethod
    def update(doc, ret):
        doc.set_attrs(**ret)


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

    @staticmethod
    def update(doc, ret):
        for r in ret:
            with Document(length=len(ret), **r) as c:
                if not c.mime_type:
                    c.mime_type = doc.mime_type
            doc.chunks.append(c)
