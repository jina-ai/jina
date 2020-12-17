from jina import DocumentSet, Document
from jina.drivers.encode import BaseEncodeDriver


class DummyEncodeDriver(BaseEncodeDriver):
    def _apply_all(
            self,
            docs: 'DocumentSet',
            context_doc: 'Document',
            field: str,
            *args,
            **kwargs,
    ) -> None:
        if context_doc:
            context_doc.text = 'hello from DummyEncodeDriver'
