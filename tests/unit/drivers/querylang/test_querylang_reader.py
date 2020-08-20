import unittest

from jina.drivers import QuerySetReader, BaseDriver
from jina.flow import Flow
from jina.proto import jina_pb2
from tests import JinaTestCase


def random_docs(num_docs):
    for j in range(num_docs):
        d = jina_pb2.Document()
        d.id = j
        d.text = 'hello world'
        d.uri = 'doc://'
        for m in range(10):
            dm = d.matches.add()
            dm.text = 'match to hello world'
            dm.uri = 'doc://match'
            dm.id = m
            dm.score.ref_id = d.id
            for mm in range(10):
                dmm = dm.matches.add()
                dmm.text = 'nested match to match'
                dmm.uri = 'doc://match/match'
                dmm.id = mm
                dmm.score.ref_id = m
        yield d


class dummyDriver(QuerySetReader, BaseDriver):

    def __init__(self, arg1='hello', arg2=456, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._arg1 = arg1
        self._arg2 = arg2


class QueryLangReaderTestCase(JinaTestCase):

    def test_read_from_req(self):
        def validate1(req):
            assert len(req.docs) == 5

        def validate2(req):
            assert len(req.docs) == 3

        qs = jina_pb2.QueryLang(name='SliceQL', priority=1)
        qs.parameters['start'] = 1
        qs.parameters['end'] = 4

        f = Flow(callback_on_body=True).add(uses='- !SliceQL | {start: 0, end: 5}')

        # without queryset
        with f:
            f.index(random_docs(10), output_fn=validate1)

        # with queryset
        with f:
            f.index(random_docs(10), queryset=qs, output_fn=validate2)

        qs.priority = -1
        # with queryset, but priority is no larger than driver's default
        with f:
            f.index(random_docs(10), queryset=qs, output_fn=validate1)

    def test_querlang_driver(self):
        qld2 = dummyDriver(arg1='world')
        assert qld2.arg1 == 'world'


if __name__ == '__main__':
    unittest.main()
