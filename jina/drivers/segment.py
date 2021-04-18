__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Optional, Tuple, Any, Dict, List

from . import BaseExecutableDriver, FlatRecursiveMixin, DocsExtractUpdateMixin
from ..types.document import Document


class SegmentDriver(DocsExtractUpdateMixin, FlatRecursiveMixin, BaseExecutableDriver):
    """Drivers inherited from this Driver will bind :meth:`segment` by default """

    def __init__(
        self,
        executor: Optional[str] = None,
        method: str = 'segment',
        traversal_paths: Tuple[str] = ('r',),
        *args,
        **kwargs,
    ):
        super().__init__(
            executor, method, traversal_paths=traversal_paths, *args, **kwargs
        )

    def update_single_doc(self, doc: 'Document', exec_result: List[Dict]) -> None:
        """Update the document's chunks field with executor's returns.

        :param doc: the Document object
        :param exec_result: the single result from :meth:`exec_fn`
        """
        new_chunks = []
        for chunk in exec_result:
            with Document(**chunk) as c:
                if not c.mime_type:
                    c.mime_type = doc.mime_type
            new_chunks.append(c)
        doc.chunks.extend(new_chunks)
