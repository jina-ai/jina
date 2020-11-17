from jina.clients.python import PyClient
from jina.drivers import QuerySetReader, BaseDriver
from jina.drivers.querylang.slice import SliceQL
from jina.flow import Flow
from jina.proto import jina_pb2
from jina.types.querylang import QueryLang


def random_docs(num_docs):
    for j in range(num_docs):
        d = jina_pb2.DocumentProto()
        d.tags['id'] = j
        d.text = 'hello world'
        d.uri = 'doc://'
        for m in range(10):
            dm = d.matches.add()
            dm.text = 'match to hello world'
            dm.uri = 'doc://match'
            dm.tags['id'] = m
            dm.score.ref_id = d.id
            for mm in range(10):
                dmm = dm.matches.add()
                dmm.text = 'nested match to match'
                dmm.uri = 'doc://match/match'
                dmm.tags['id'] = mm
                dmm.score.ref_id = dm.id
        yield d


class DummyDriver(QuerySetReader, BaseDriver):

    def __init__(self, arg1='hello', arg2=456, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._arg1 = arg1
        self._arg2 = arg2


def test_querylang_request():
    qs = QueryLang(SliceQL(start=1, end=4, priority=1))
    PyClient.check_input(random_docs(10), queryset=qs)


def test_read_from_req():
    def validate1(req):
        assert len(req.docs) == 5

    def validate2(req):
        assert len(req.docs) == 3

    qs = QueryLang(SliceQL(start=1, end=4, priority=1))

    f = Flow(callback_on='body').add(uses='- !SliceQL | {start: 0, end: 5}')

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


def test_querlang_driver():
    qld2 = DummyDriver(arg1='world')
    assert qld2.arg1 == 'world'
