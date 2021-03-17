from jina import DocumentSet
from jina.drivers import FlatRecursiveMixin
from jina.drivers.encode import BaseEncodeDriver


class DummyEncodeDriver(FlatRecursiveMixin, BaseEncodeDriver):
    def _apply_all(
        self,
        docs: 'DocumentSet',
        *args,
        **kwargs,
    ) -> None:
        for doc in docs:
            doc.text = 'hello from DummyEncodeDriver'
