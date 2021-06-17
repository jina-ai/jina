import pytest

from google.protobuf.struct_pb2 import ListValue

from jina.types.list import ListView


def test_empty_struct_view():
    l = ListValue()
    view = ListView(l)
    assert len(view) == 0


@pytest.fixture()
def list_proto():
    lv = ListValue()
    l = [0, 1, 'hey', {'key': 'value'}, [0, 1, 2]]
    lv.extend(l)
    return lv


def test_list_view(list_proto):
    view = ListView(list_proto)
    assert len(view) == 5
    assert view[-4] == 1
    assert view[0] == 0
    assert view[1] == 1
    assert view[2] == 'hey'
    assert view[3] == {'key': 'value'}
    assert len(view[4]) == 3
    assert view[4][0] == 0
    assert view[4][1] == 1
    assert view[4][2] == 2


def test_list_view_set_items(list_proto):
    view = ListView(list_proto)
    view[0] = 20
    view[1] = 'now string'
    view[2] = {'key': 'value'}
    view[3]['key'] = 50
    view[4][0] = {'new_key': 'new_value'}
    assert view[0] == 20
    assert view[1] == 'now string'
    assert view[2] == {'key': 'value'}
    assert view[3] == {'key': 50}
    assert view[4][0] == {'new_key': 'new_value'}
    assert view[4][1] == 1
    assert view[4][2] == 2
    view[4][0]['new_key'] = None
    assert view[4][0] == {'new_key': None}


def test_list_view_delete(list_proto):
    view = ListView(list_proto)
    del view[1]
    assert len(view) == 4
    assert view[0] == 0
    assert view[1] == 'hey'
    assert view[2] == {'key': 'value'}
    assert len(view[3]) == 3
    assert view[3][0] == 0
    assert view[3][1] == 1
    assert view[3][2] == 2


def test_list_view_clear(list_proto):
    view = ListView(list_proto)
    assert len(view) == 5
    view.clear()
    assert len(view) == 0


def test_list_view_iterate(list_proto):
    view = ListView(list_proto)
    for i, element in enumerate(view):
        assert view[0] == 0
        assert view[1] == 1
        assert view[2] == 'hey'
        assert view[3] == {'key': 'value'}
        assert len(view[4]) == 3
        assert view[4][0] == 0
        assert view[4][1] == 1
        assert view[4][2] == 2
        if i == 0:
            assert element == 0
        elif i == 1:
            assert element == 1
        elif i == 2:
            assert element == 'hey'
        elif i == 3:
            assert element == {'key': 'value'}
        elif i == 4:
            assert len(element) == 3
            for j, e in enumerate(element):
                if j == 0:
                    assert e == 0
                elif j == 1:
                    assert e == 1
                elif j == 2:
                    assert e == 2


def test_list_view_dict():
    list = ListValue()
    l = [0, 1, 'hey', {'key': 'value'}, [0, 1, 2]]
    list.extend(l)
    view = ListView(list)
    assert view.dict() == l


def test_list_contains(list_proto):
    view = ListView(list_proto)
    assert 'hey' in view
    assert 'heya' not in view
    assert {'key': 'value'} in view
    assert {'key': 'value-aaa'} not in view
    assert [0, 1, 2] in view


def test_list_reverse():
    list = ListValue()
    l = [0, 2, 1]
    list.extend(l)
    view = ListView(list)
    view.reverse()
    assert view[0] == 1
    assert view[1] == 2
    assert view[2] == 0


def test_list_view_equals(list_proto):
    view_1 = ListView(list_proto)
    view_2 = ListView(list_proto)
    assert view_2 == view_1
    lv = ListValue()
    l = [0, 1, 'hey', {'key': 'value'}, [0, 1, 2]]
    lv.extend(l)
    view_3 = ListView(lv)
    assert view_2 == view_3


def test_list_view_not_equals(list_proto):
    view_1 = ListView(list_proto)
    lv = ListValue()
    l = [0, 1, 'heya', {'key': 'value'}, [0, 1, 2]]
    lv.extend(l)
    view_2 = ListView(lv)
    assert view_2 != view_1


def test_list_view_access_out_of_bounds(list_proto):
    view = ListView(list_proto)
    with pytest.raises(IndexError):
        _ = view[100]
