import pytest
from google.protobuf.json_format import MessageToJson, Parse

from jina.proto.jina_pb2 import Document


@pytest.fixture(scope='function')
def document():
    d = Document()
    d.tags['int'] = 1  # will convert to float!!!
    d.tags['str'] = 'blah'
    d.tags['float'] = 0.1234
    d.tags['bool'] = True
    d.tags['nested'] = {'bool': True}
    return d


def test_tags(document):
    jd = MessageToJson(document)
    d2 = Parse(jd, Document())
    assert isinstance(d2.tags['int'], float)
    assert isinstance(d2.tags['str'], str)
    assert isinstance(d2.tags['float'], float)
    assert isinstance(d2.tags['bool'], bool)
    assert isinstance(d2.tags['nested']['bool'], bool)
    # can be used as a dict
    for _, _ in d2.tags['nested'].items():
        continue
