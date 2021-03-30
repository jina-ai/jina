from jina import DocumentList
from jina.drivers import FlatRecursiveMixin
from jina.drivers.encode import BaseEncodeDriver


class DummyEncodeDriver(FlatRecursiveMixin, BaseEncodeDriver):
    def _apply_all(
        self,
        docs: 'DocumentList',
        *args,
        **kwargs,
    ) -> None:
        for doc in docs:
            doc.text = 'hello from DummyEncodeDriver'
