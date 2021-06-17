import pytest

from google.protobuf.struct_pb2 import Struct

from jina.types.struct import StructView


def test_empty_struct_view():
    struct = Struct()
    view = StructView(struct)
    assert len(view) == 0


@pytest.fixture()
def struct_proto():
    struct = Struct()
    d = {
        'key_int': 0,
        'key_float': 1.5,
        'key_string': 'string_value',
        'key_array': [0, 1],
        'key_nested': {
            'key_nested_int': 2,
            'key_nested_string': 'string_nested_value',
            'key_nested_nested': {'empty': []},
        },
    }
    struct.update(d)
    return struct


def test_struct_view(struct_proto):
    view = StructView(struct_proto)
    assert len(view) == 5
    assert len(view.keys()) == 5
    assert len(view.values()) == 5
    assert len(view.items()) == 5
    assert 'key_int' in view
    assert 'key_float' in view
    assert 'key_string' in view
    assert 'key_array' in view
    assert 'key_nested' in view

    assert 0 in view.values()
    assert 1.5 in view.values()
    assert 'string_value' in view.values()

    assert view['key_int'] == 0
    assert view['key_float'] == 1.5
    assert view['key_string'] == 'string_value'
    assert len(view['key_array']) == 2
    assert view['key_array'][0] == 0
    assert view['key_array'][1] == 1
    assert len(view['key_nested'].keys()) == 3
    assert view['key_nested']['key_nested_int'] == 2
    assert view['key_nested']['key_nested_string'] == 'string_nested_value'
    assert len(view['key_nested']['key_nested_nested'].keys()) == 1
    assert len(view['key_nested']['key_nested_nested']['empty']) == 0


def test_struct_view_set_items(struct_proto):
    view = StructView(struct_proto)
    view['key_array'][0] = 2
    assert view['key_array'][0] == 2


def test_struct_view_set_listitems(struct_proto):
    view = StructView(struct_proto)
    view['key_int'] = 20
    view['key_new'] = 30
    view['key_nested']['key_nested_nested']['empty'] = [1, 2, 3]
    view['key_nested']['key_nested_string'] = 'updated_string'
    assert view['key_int'] == 20
    assert view['key_new'] == 30
    assert view['key_nested']['key_nested_nested']['empty'][0] == 1
    assert view['key_nested']['key_nested_nested']['empty'][1] == 2
    assert view['key_nested']['key_nested_nested']['empty'][2] == 3
    assert view['key_nested']['key_nested_string'] == 'updated_string'


def test_struct_view_delete(struct_proto):
    view = StructView(struct_proto)
    del view['key_int']
    assert len(view) == 4
    del view['key_nested']['key_nested_nested']
    assert len(view['key_nested'].keys()) == 2
    del view['key_nested']
    assert len(view) == 3


def test_struct_view_clear(struct_proto):
    view = StructView(struct_proto)
    view.clear()
    assert len(view) == 0


def test_struct_view_iterate(struct_proto):
    view = StructView(struct_proto)
    assert set(view.keys()) == {
        'key_int',
        'key_float',
        'key_string',
        'key_array',
        'key_nested',
    }
    assert set([key for key, value in view.items()]) == {
        'key_int',
        'key_float',
        'key_string',
        'key_array',
        'key_nested',
    }
    assert set([element for element in view]) == {
        'key_int',
        'key_float',
        'key_string',
        'key_array',
        'key_nested',
    }


def test_struct_view_update(struct_proto):
    view = StructView(struct_proto)
    update_dict = {'new_dict': 'new_value'}
    view.update(update_dict)
    assert len(view) == 6
    assert 'new_dict' in view.keys()
    assert view['new_dict'] == 'new_value'

    update_dict2 = {'key_int': 100}
    view.update(update_dict2)
    assert len(view) == 6
    assert 'new_dict' in view.keys()
    assert view['key_int'] == 100

    update_dict3 = {'key_nested': {'new_key_nested': 'very_new'}}
    view.update(update_dict3)
    assert len(view) == 6
    assert len(view['key_nested'].keys()) == 1
    assert view['key_nested']['new_key_nested'] == 'very_new'


def test_struct_view_dict_eq():
    struct = Struct()
    d = {'a': 1, 'ma': [1, 2, 3], 'b': 2, 'c': {'e': None, 'l': [40, 30]}, 'f': [5, 1]}
    struct.update(d)
    view = StructView(struct)
    assert view.dict() == d
    assert view == d
    d['a'] = 3
    assert view != d


def test_struct_contains(struct_proto):
    view = StructView(struct_proto)
    assert 'key_nested' in view
    assert 'a' not in view
