import pytest
from jina.drivers import QuerySetReader


class MockQuerySetReader(QuerySetReader):
    _init_kwargs_dict = None
    _priority = None

    def __init__(self, _init_kwargs_dict, _priority, queryset):
        self._init_kwargs_dict = _init_kwargs_dict
        self._priority = _priority
        self._queryset = queryset

    @property
    def queryset(self):
        return self._queryset


class WrongMockQuerySetReader(QuerySetReader):
    _init_kwargs_dict = None
    _priority = None

    def __init__(self, _init_kwargs_dict, _priority):
        self._init_kwargs_dict = _init_kwargs_dict
        self._priority = _priority


def test_queryset_reader():
    with pytest.raises(TypeError):
        WrongMockQuerySetReader({}, 1)
