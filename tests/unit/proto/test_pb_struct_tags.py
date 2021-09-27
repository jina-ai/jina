import pytest
from google.protobuf.json_format import MessageToJson, Parse
from jina import Document

from jina.proto.jina_pb2 import DocumentProto


@pytest.fixture(scope='function')
def document():
    d = DocumentProto()
    d.tags['int'] = 1  # will convert to float!!!
    d.tags['str'] = 'blah'
    d.tags['float'] = 0.1234
    d.tags['bool'] = True
    d.tags['nested'] = {'bool': True}
    return d


def test_tags(document):
    jd = MessageToJson(document)
    d2 = Parse(jd, DocumentProto())
    assert isinstance(d2.tags['int'], float)
    assert isinstance(d2.tags['str'], str)
    assert isinstance(d2.tags['float'], float)
    assert isinstance(d2.tags['bool'], bool)
    assert isinstance(d2.tags['nested']['bool'], bool)
    # can be used as a dict
    for _, _ in d2.tags['nested'].items():
        continue


def test_tags_property():
    d = Document()
    assert not d.tags
    assert not d.proto.tags

    # set item
    d.tags['hello'] = 'world'
    assert d.tags == {'hello': 'world'}
    assert d.proto.tags['hello'] == 'world'

    # set composite item
    d.tags = {'world': ['hello', 'world']}
    # TODO: Issue about having proper ListValueView, not really expected
    assert d.tags.dict() == {'world': ['hello', 'world']}
    assert d.proto.tags['world'][0] == 'hello'
    assert d.proto.tags['world'][1] == 'world'

    # set scalar item
    d.tags['world'] = 123
    assert d.tags['world'] == 123
    assert d.proto.tags['world'] == 123

    # clear
    d.clear()
    assert not d.tags
    assert not d.proto.tags

    # update
    d.tags.update({'hello': 'world'})
    assert d.tags['hello'] == 'world'
    assert d.proto.tags['hello'] == 'world'

    # delete
    del d.tags['hello']
    assert not d.tags
    assert not d.proto.tags

    # init from the Doc
    d = Document(tags={'123': 456})
    assert d.tags['123'] == 456
    assert d.proto.tags['123'] == 456

    # copy from other doc
    d1 = Document(d, copy=True)
    assert d1.tags['123'] == 456
    assert d1.proto.tags['123'] == 456

    # copy is a deep copy
    d1.tags.clear()
    assert not d1.tags
    assert not d1.proto.tags
    assert d.tags['123'] == 456
    assert d.proto.tags['123'] == 456

    # init from another doc.tags
    d2 = Document(tags=d.tags)
    assert d2.tags['123'] == 456
    assert d2.proto.tags['123'] == 456

    # copy is a deep copy
    d.tags.clear()
    assert not d.tags
    assert not d.proto.tags
    assert d2.tags['123'] == 456
    assert d2.proto.tags['123'] == 456


def test_tags_assign():
    d = DocumentProto()
    d.tags.update({'int': 1, 'float': 0.1234})
    with pytest.raises(AttributeError):
        d.tags = {'int': 1, 'float': 0.1234}
