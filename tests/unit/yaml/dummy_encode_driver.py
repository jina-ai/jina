from jina import DocumentArray
from jina.drivers import FlatRecursiveMixin
from jina.drivers.encode import BaseEncodeDriver


class DummyEncodeDriver(FlatRecursiveMixin, BaseEncodeDriver):
    def _apply_all(
        self,
        docs: 'DocumentArray',
        *args,
        **kwargs,
    ) -> None:
        for doc in docs:
            doc.text = 'hello from DummyEncodeDriver'
