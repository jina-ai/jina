__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Optional, Any

from . import BaseExecutableDriver, FlatRecursiveMixin, DocsExtractUpdateMixin

# noinspection PyUnreachableCode
if False:
    from .. import Document
    from .. import DocumentSet


class BaseEncodeDriver(BaseExecutableDriver):
    """Drivers inherited from this Driver will bind :meth:`encode` by default """

    def __init__(
        self, executor: Optional[str] = None, method: str = 'encode', *args, **kwargs
    ):
        super().__init__(executor, method, *args, **kwargs)


class EncodeDriver(DocsExtractUpdateMixin, FlatRecursiveMixin, BaseEncodeDriver):
    """Extract the content from documents and call executor and do encoding"""

    def update_single_doc(self, doc: 'Document', exec_result) -> None:
        """Update the document embedding with returned ndarray result

        :param doc: the Document object
        :param exec_result: the single result from :meth:`exec_fn`
        """
        doc.embedding = exec_result


class ScipySparseEncodeDriver(
    DocsExtractUpdateMixin, FlatRecursiveMixin, BaseEncodeDriver
):
    """Extract the content from documents and call executor and do encoding"""

    def update_docs(self, docs_pts: 'DocumentSet', exec_results: Any) -> None:
        """Update the document embedding with returned sparse matrix

        :param: docs_pts: the set of document to be updated
        :param: exec_results: the results from :meth:`exec_fn`
        """
        for idx, doc in enumerate(docs_pts):
            doc.embedding = exec_results.getrow(idx)
