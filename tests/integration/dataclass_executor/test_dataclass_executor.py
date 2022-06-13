import dataclasses

from docarray import DocumentArray
from jina import Executor, Flow, requests


def test_executor_dataclass():
    @dataclasses.dataclass
    class MyDataClassExecutor(Executor):
        my_field: str

        @requests(on=['/search'])
        def baz(self, docs, **kwargs):
            for doc in docs:
                doc.tags['metas_name'] = self.metas.name
                doc.tags['my_field'] = self.my_field

    f = Flow().add(
        uses=MyDataClassExecutor,
        uses_with={'my_field': 'this is my field'},
        uses_metas={'name': 'test-name-updated'},
        uses_requests={'/foo': 'baz'},
    )
    with f:
        res = f.post(on='/foo', inputs=DocumentArray.empty(2))
    assert len(res) == 2
    for r in res:
        assert r.tags['metas_name'] == 'test-name-updated'
        assert r.tags['my_field'] == 'this is my field'
