from jina.clients import Client
from jina.drivers import QuerySetReader, BaseDriver
from jina.drivers.querylang.sort import SortQL
from jina.drivers.querylang.slice import SliceQL
from jina.drivers.querylang.select import ExcludeQL
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
    qs = QueryLang({'name': 'SliceQL', 'parameters': {'start': 1, 'end': 4}, 'priority': 1})
    Client.check_input(random_docs(10), queryset=qs)


def test_read_from_req(mocker):
    def validate1(req):
        assert len(req.docs) == 5

    def validate2(req):
        assert len(req.docs) == 3

    response_mock = mocker.Mock(wrap=validate1)
    response_mock_2 = mocker.Mock(wrap=validate2)
    response_mock_3 = mocker.Mock(wrap=validate1)

    qs = QueryLang({'name': 'SliceQL', 'priority': 1, 'parameters': {'start': 1, 'end': 4}})

    f = Flow(callback_on='body').add(uses='- !SliceQL | {start: 0, end: 5}')

    # without queryset
    with f:
        f.index(random_docs(10), on_done=response_mock)

    response_mock.assert_called()
    # with queryset
    with f:
        f.index(random_docs(10), queryset=qs, on_done=response_mock_2)

    response_mock_2.assert_called()

    qs.priority = -1
    # with queryset, but priority is no larger than driver's default
    with f:
        f.index(random_docs(10), queryset=qs, on_done=response_mock_3)

    response_mock_3.assert_called()


def test_querlang_driver():
    qld2 = DummyDriver(arg1='world')
    assert qld2.arg1 == 'world'


def test_as_querylang():
    sortql = SortQL(field='field_value', reverse=False, priority=2)
    sort_querylang = sortql.as_querylang
    assert sort_querylang.name == 'SortQL'
    assert sort_querylang.priority == 2
    assert sort_querylang.parameters['field'] == 'field_value'
    assert not sort_querylang.parameters['reverse']

    sliceql = SliceQL(start=10, end=20)
    slice_querylang = sliceql.as_querylang
    assert slice_querylang.name == 'SliceQL'
    assert slice_querylang.priority == 0
    assert slice_querylang.parameters['start'] == 10
    assert slice_querylang.parameters['end'] == 20

    excludeql = ExcludeQL(fields=('field1', 'field2'))
    exclude_querylang = excludeql.as_querylang
    assert exclude_querylang.name == 'ExcludeQL'
    assert exclude_querylang.priority == 0
    assert exclude_querylang.parameters['fields'] == ['field1', 'field2']

    excludeql2 = ExcludeQL(fields='field1')
    exclude_querylang2 = excludeql2.as_querylang
    assert exclude_querylang2.name == 'ExcludeQL'
    assert exclude_querylang2.priority == 0
    assert exclude_querylang2.parameters['fields'] == ['field1']
