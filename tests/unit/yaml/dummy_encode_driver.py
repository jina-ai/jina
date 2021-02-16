from typing import Iterable
from jina import DocumentSet
from jina.drivers import FastRecursiveMixin
from jina.drivers.encode import BaseEncodeDriver


class DummyEncodeDriver(FastRecursiveMixin, BaseEncodeDriver):
    def _apply_all(
            self,
            leaves: Iterable['DocumentSet'],
            *args,
            **kwargs,
    ) -> None:
        docs = DocumentSet.flatten(leaves)
        for doc in docs:
            doc.text = 'hello from DummyEncodeDriver'
