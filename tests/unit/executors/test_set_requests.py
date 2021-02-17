from jina.drivers.delete import DeleteDriver
from jina.drivers.encode import EncodeDriver
from jina.drivers.querylang.filter import FilterQL
from jina.executors import BaseExecutor

y_no_fill = """
!BaseEncoder
requests:
    use_default: false
"""


def test_no_fill():
    be = BaseExecutor.load_config(y_no_fill)
    assert not be._drivers


y_no_fill_with_index_request = """
!BaseEncoder
requests:
    use_default: false
    on:
        IndexRequest:
            - !RouteDriver {}
"""


def test_no_fill_with_index_request():
    be = BaseExecutor.load_config(y_no_fill_with_index_request)
    assert len(be._drivers) == 2
    assert 'IndexRequest' in be._drivers
    assert 'ControlRequest' in be._drivers


y_fill_default_with_index_request = """
!BaseEncoder
requests:
    use_default: true
    on:
        IndexRequest:
            - !EncodeDriver {}
"""


def test_fill_default_with_index_request():
    be = BaseExecutor.load_config(y_fill_default_with_index_request)
    assert len(be._drivers) == 6
    assert isinstance(be._drivers['IndexRequest'][0], EncodeDriver)
    print(be._drivers['IndexRequest'][0]._init_kwargs_dict)


y_fill_default_with_index_request_no_with = """
!BaseEncoder
requests:
    use_default: true
    on:
        IndexRequest:
            drivers:
                - !FilterQL
                  with:
                    lookups:
                        mime_type: image/jpeg
                - !EncodeDriver {}
"""


def test_with_common_kwargs_on_index_no_with():
    be = BaseExecutor.load_config(y_fill_default_with_index_request_no_with)
    assert len(be._drivers) == 6
    assert isinstance(be._drivers['IndexRequest'][1], EncodeDriver)
    assert isinstance(be._drivers['IndexRequest'][0], FilterQL)


y_fill_default_with_index_request_with_common = """
!BaseEncoder
requests:
    use_default: true
    on:
        IndexRequest:
            with:
                traversal_paths: ['mmm']
            drivers:
                - !FilterQL
                  with:
                    lookups:
                        mime_type: image/jpeg
                - !EncodeDriver {}
"""


def test_with_common_kwargs_on_index():
    be = BaseExecutor.load_config(y_fill_default_with_index_request_with_common)
    assert len(be._drivers) == 6
    assert isinstance(be._drivers['IndexRequest'][1], EncodeDriver)
    assert isinstance(be._drivers['IndexRequest'][0], FilterQL)
    assert be._drivers['IndexRequest'][0]._traversal_paths == ['mmm']
    assert be._drivers['IndexRequest'][1]._traversal_paths == ['mmm']


y_fill_default_with_two_request_with_common = """
!BaseEncoder
requests:
    use_default: true
    on:
        [IndexRequest, SearchRequest]:
            with:
                traversal_paths: ['mmm']
            drivers:
                - !FilterQL
                  with:
                    lookups:
                        mime_type: image/jpeg
                - !EncodeDriver {}
        [DeleteRequest]:
            with:
                traversal_paths: ['ccc']
            drivers:
                - !FilterQL
                  with:
                    lookups:
                        mime_type: image/jpeg
                - !DeleteDriver {}
"""


def test_with_common_kwargs_on_two_requests():
    be = BaseExecutor.load_config(y_fill_default_with_two_request_with_common)
    assert len(be._drivers) == 6

    for r in ('IndexRequest', 'SearchRequest', 'DeleteRequest'):
        if r == 'DeleteRequest':
            assert isinstance(be._drivers[r][1], DeleteDriver)
        else:
            assert isinstance(be._drivers[r][1], EncodeDriver)
        assert isinstance(be._drivers[r][0], FilterQL)
        if r == 'DeleteRequest':
            assert be._drivers[r][0]._traversal_paths == ['ccc']
            assert be._drivers[r][1]._traversal_paths == ['ccc']
        else:
            assert be._drivers[r][0]._traversal_paths == ['mmm']
            assert be._drivers[r][1]._traversal_paths == ['mmm']
