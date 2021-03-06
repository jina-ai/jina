import json

import numpy as np
import pytest

from google.protobuf.json_format import MessageToDict
from jina import NdArray, Request
from jina.proto.jina_pb2 import DocumentProto
from jina.types.document import Document
from jina.types.score import NamedScore
from tests import random_docs


@pytest.mark.parametrize('field', ['blob', 'embedding'])
def test_ndarray_get_set(field):
    a = Document()
    b = np.random.random([10, 10])
    setattr(a, field, b)
    np.testing.assert_equal(getattr(a, field), b)

    b = np.random.random([10, 10])
    c = NdArray()
    c.value = b
    setattr(a, field, c)
    np.testing.assert_equal(getattr(a, field), b)

    b = np.random.random([10, 10])
    c = NdArray()
    c.value = b
    setattr(a, field, c._pb_body)
    np.testing.assert_equal(getattr(a, field), b)


def test_doc_update_fields():
    a = Document()
    b = np.random.random([10, 10])
    c = {'tags': 'string', 'tag-tag': {'tags': 123.45}}
    d = [12, 34, 56]
    e = 'text-mod'
    w = 2.0
    a.set_attrs(embedding=b, tags=c, location=d, modality=e, weight=w)
    np.testing.assert_equal(a.embedding, b)
    assert list(a.location) == d
    assert a.modality == e
    assert MessageToDict(a.tags) == c
    assert a.weight == w


def test_granularity_get_set():
    d = Document()
    d.granularity = 1
    assert d.granularity == 1


def test_uri_get_set():
    a = Document()
    a.uri = 'https://abc.com/a.jpg'
    assert a.uri == 'https://abc.com/a.jpg'
    assert a.mime_type == 'image/jpeg'

    with pytest.raises(ValueError):
        a.uri = 'abcdefg'


def test_set_get_mime():
    a = Document()
    a.mime_type = 'jpg'
    assert a.mime_type == 'image/jpeg'
    b = Document()
    b.mime_type = 'jpeg'
    assert b.mime_type == 'image/jpeg'
    c = Document()
    c.mime_type = '.jpg'
    assert c.mime_type == 'image/jpeg'


def test_no_copy_construct():
    a = DocumentProto()
    b = Document(a, copy=False)
    a.id = '1' * 16
    assert b.id == '1' * 16

    b.id = '2' * 16
    assert a.id == '2' * 16


def test_copy_construct():
    a = DocumentProto()
    b = Document(a, copy=True)
    a.id = '1' * 16
    assert b.id != '1' * 16

    b.id = '2' * 16
    assert a.id == '1' * 16


def test_bad_good_doc_id():
    b = Document()
    b.id = 'hello'
    b.id = 'abcd' * 4
    b.id = 'de09' * 4
    b.id = 'af54' * 4
    b.id = 'abcdef0123456789'


def test_id_context():
    with Document() as d:
        d.buffer = b'123'
    assert d.id


def test_doc_content():
    d = Document()
    assert d.content is None
    d.text = 'abc'
    assert d.content == 'abc'
    c = np.random.random([10, 10])
    d.blob = c
    np.testing.assert_equal(d.content, c)
    d.buffer = b'123'
    assert d.buffer == b'123'


def test_request_docs_mutable_iterator():
    """To test the weak reference work in docs"""
    r = Request()
    r.request_type = 'index'
    for d in random_docs(10):
        r.docs.append(d)

    for idx, d in enumerate(r.docs):
        assert isinstance(d, Document)
        d.text = f'look I changed it! {idx}'

    # iterate it again should see the change
    doc_pointers = []
    for idx, d in enumerate(r.docs):
        assert isinstance(d, Document)
        assert d.text == f'look I changed it! {idx}'
        doc_pointers.append(d)

    # pb-lize it should see the change
    rpb = r.proto

    for idx, d in enumerate(rpb.index.docs):
        assert isinstance(d, DocumentProto)
        assert d.text == f'look I changed it! {idx}'

    # change again by following the pointers
    for d in doc_pointers:
        d.text = 'now i change it back'

    # iterate it again should see the change
    for idx, d in enumerate(rpb.index.docs):
        assert isinstance(d, DocumentProto)
        assert d.text == 'now i change it back'


def test_request_docs_chunks_mutable_iterator():
    """Test if weak reference work in nested docs"""
    r = Request()
    r.request_type = 'index'
    for d in random_docs(10):
        r.docs.append(d)

    for d in r.docs:
        assert isinstance(d, Document)
        for idx, c in enumerate(d.chunks):
            assert isinstance(d, Document)
            c.text = f'look I changed it! {idx}'

    # iterate it again should see the change
    doc_pointers = []
    for d in r.docs:
        assert isinstance(d, Document)
        for idx, c in enumerate(d.chunks):
            assert c.text == f'look I changed it! {idx}'
            doc_pointers.append(c)

    # pb-lize it should see the change
    rpb = r.proto

    for d in rpb.index.docs:
        assert isinstance(d, DocumentProto)
        for idx, c in enumerate(d.chunks):
            assert isinstance(c, DocumentProto)
            assert c.text == f'look I changed it! {idx}'

    # change again by following the pointers
    for d in doc_pointers:
        d.text = 'now i change it back'

    # iterate it again should see the change
    for d in rpb.index.docs:
        assert isinstance(d, DocumentProto)
        for c in d.chunks:
            assert c.text == 'now i change it back'


def test_doc_setattr():
    from jina import Document

    with Document() as root:
        root.text = 'abc'

    assert root.adjacency == 0

    with Document() as match:
        match.text = 'def'
        m = root.matches.append(match)

    with Document() as chunk:
        chunk.text = 'def'
        c = root.chunks.append(chunk)

    assert len(root.matches) == 1
    assert root.matches[0].granularity == 0
    assert root.matches[0].adjacency == 1

    assert m.granularity == 0
    assert m.adjacency == 1

    assert len(root.chunks) == 1
    assert root.chunks[0].granularity == 1
    assert root.chunks[0].adjacency == 0

    assert c.granularity == 1
    assert c.adjacency == 0


def test_doc_score():
    from jina.types.score import NamedScore

    with Document() as doc:
        doc.text = 'text'

    score = NamedScore(op_name='operation', value=10.0, ref_id=doc.id)
    doc.score = score

    assert doc.score.op_name == 'operation'
    assert doc.score.value == 10.0
    assert doc.score.ref_id == doc.id


def test_content_hash_not_dependent_on_chunks_or_matches():
    doc1 = Document()
    doc1.content = 'one'
    doc1.update_content_hash()

    doc2 = Document()
    doc2.content = 'one'
    doc2.update_content_hash()
    assert doc1.content_hash == doc2.content_hash

    doc3 = Document()
    doc3.content = 'one'
    for _ in range(3):
        with Document() as m:
            m.content = 'some chunk'
        doc3.chunks.append(m)
    doc3.update_content_hash()
    assert doc1.content_hash == doc3.content_hash

    doc4 = Document()
    doc4.content = 'one'
    for _ in range(3):
        with Document() as m:
            m.content = 'some match'
        doc4.matches.append(m)
    doc4.update_content_hash()
    assert doc1.content_hash == doc4.content_hash


def test_include_scalar():
    d1 = Document()
    d1.text = 'hello'
    dd1 = Document()
    d1.chunks.append(dd1)
    d1.update_content_hash(include_fields=('text',), exclude_fields=None)

    d2 = Document()
    d2.text = 'hello'
    d2.update_content_hash(include_fields=('text',), exclude_fields=None)

    assert d1.content_hash == d2.content_hash

    # change text should result in diff hash
    d2.text = 'world'
    d2.update_content_hash(include_fields=('text',), exclude_fields=None)
    assert d1.content_hash != d2.content_hash


def test_include_repeated_fields():
    def build_document(chunk=None):
        d = Document()
        d.chunks.append(chunk)
        d.chunks[0].update_content_hash(
            exclude_fields=('parent_id', 'id', 'content_hash')
        )
        d.chunks[0].parent_id = 0
        d.update_content_hash(include_fields=('chunks',), exclude_fields=None)
        return d

    c = Document()
    d1 = build_document(chunk=c)
    d2 = build_document(chunk=c)

    assert d1.chunks[0].content_hash == d2.chunks[0].content_hash
    assert d1.content_hash == d2.content_hash

    # change text should result in same hash
    d2.text = 'world'
    d2.update_content_hash(include_fields=('chunks',), exclude_fields=None)
    assert d1.content_hash == d2.content_hash

    # change chunks should result in diff hash
    d2.chunks.clear()
    d2.update_content_hash(include_fields=('chunks',), exclude_fields=None)
    assert d1.content_hash != d2.content_hash


@pytest.mark.parametrize('from_str', [True, False])
@pytest.mark.parametrize(
    'd_src',
    [
        {
            'id': '123',
            'mime_type': 'txt',
            'parent_id': '456',
            'tags': {'hello': 'world'},
        },
        {'id': '123', 'mimeType': 'txt', 'parentId': '456', 'tags': {'hello': 'world'}},
        {
            'id': '123',
            'mimeType': 'txt',
            'parent_id': '456',
            'tags': {'hello': 'world'},
        },
    ],
)
def test_doc_from_dict_cases(d_src, from_str):
    # regular case
    if from_str:
        d_src = json.dumps(d_src)
    d = Document(d_src)
    assert d.tags['hello'] == 'world'
    assert d.mime_type == 'txt'
    assert d.id == '123'
    assert d.parent_id == '456'


@pytest.mark.parametrize('from_str', [True, False])
def test_doc_arbitrary_dict(from_str):
    d_src = {'id': '123', 'hello': 'world', 'tags': {'good': 'bye'}}
    if from_str:
        d_src = json.dumps(d_src)
    d = Document(d_src)
    assert d.id == '123'
    assert d.tags['hello'] == 'world'
    assert d.tags['good'] == 'bye'

    d_src = {'hello': 'world', 'good': 'bye'}
    if from_str:
        d_src = json.dumps(d_src)
    d = Document(d_src)
    assert d.tags['hello'] == 'world'
    assert d.tags['good'] == 'bye'


@pytest.mark.parametrize('from_str', [True, False])
def test_doc_field_resolver(from_str):
    d_src = {'music_id': '123', 'hello': 'world', 'tags': {'good': 'bye'}}
    if from_str:
        d_src = json.dumps(d_src)
    d = Document(d_src)
    assert d.id != '123'
    assert d.tags['hello'] == 'world'
    assert d.tags['good'] == 'bye'
    assert d.tags['music_id'] == '123'

    d_src = {'music_id': '123', 'hello': 'world', 'tags': {'good': 'bye'}}
    if from_str:
        d_src = json.dumps(d_src)
    d = Document(d_src, field_resolver={'music_id': 'id'})
    assert d.id == '123'
    assert d.tags['hello'] == 'world'
    assert d.tags['good'] == 'bye'
    assert 'music_id' not in d.tags


def test_doc_plot():
    docs = [
        Document(
            id='🐲',
            embedding=np.array([0, 0]),
            tags={'guardian': 'Azure Dragon', 'position': 'East'},
        ),
        Document(
            id='🐦',
            embedding=np.array([1, 0]),
            tags={'guardian': 'Vermilion Bird', 'position': 'South'},
        ),
        Document(
            id='🐢',
            embedding=np.array([0, 1]),
            tags={'guardian': 'Black Tortoise', 'position': 'North'},
        ),
        Document(
            id='🐯',
            embedding=np.array([1, 1]),
            tags={'guardian': 'White Tiger', 'position': 'West'},
        ),
    ]

    docs[0].chunks.append(docs[1])
    docs[0].chunks[0].chunks.append(docs[2])
    docs[0].matches.append(docs[3])

    assert docs[0]._mermaid_to_url('svg')


def get_test_doc():
    s = Document(
        id='🐲',
        content='hello-world',
        tags={'a': 'b'},
        embedding=np.array([1, 2, 3]),
        chunks=[Document(id='🐢')],
    )
    d = Document(
        id='🐦',
        content='goodbye-world',
        tags={'c': 'd'},
        embedding=np.array([4, 5, 6]),
        chunks=[Document(id='🐯')],
    )
    return s, d


def test_update_include_field():
    s, d = get_test_doc()

    d.update(s, include_fields=('id',))
    assert d.content == 'goodbye-world'
    assert d.id == '🐲'
    assert d.tags['c'] == 'd'
    np.testing.assert_array_equal(d.embedding, np.array([4, 5, 6]))

    # check if s stays the same
    assert s.content == 'hello-world'
    assert s.id == '🐲'
    assert s.tags['a'] == 'b'
    np.testing.assert_array_equal(d.embedding, np.array([4, 5, 6]))

    # check if d is changed when merge_repeat_field turn on
    d.update(s, include_fields=('tags',))
    assert d.content == 'goodbye-world'
    assert d.id == '🐲'
    assert d.tags['a'] == 'b'
    np.testing.assert_array_equal(d.embedding, np.array([4, 5, 6]))

    # check if d is changed when merge_repeat_field turn on
    d.update(s, include_fields=('tags',))
    assert d.content == 'goodbye-world'
    assert d.id == '🐲'
    assert d.tags['a'] == 'b'
    np.testing.assert_array_equal(d.embedding, np.array([4, 5, 6]))

    # check copy behavior
    d.update(s, exclude_fields=None, include_fields=('embedding',))
    assert d.content == 'goodbye-world'
    assert d.id == '🐲'
    assert d.tags['a'] == 'b'
    np.testing.assert_array_equal(d.embedding, np.array([1, 2, 3]))


def test_update_on_no_empty_doc():
    s, d = get_test_doc()
    d0 = d.dict()
    # this will not update anything as d and s are in the same structure
    d.update(s)
    assert d.dict() == d0


def test_update_chunks():
    s, d = get_test_doc()
    d.update(s, include_fields=('chunks',), exclude_fields=None)
    assert len(d.chunks) == 1
    assert d.chunks[0].id == '🐢'


def test_update_embedding():
    s, d = get_test_doc()
    d.update(s, include_fields=('embedding',), exclude_fields=tuple())
    np.testing.assert_array_equal(d.embedding, np.array([1, 2, 3]))


def test_non_empty_fields():
    d_score = Document(score=NamedScore(value=42))
    assert d_score.non_empty_fields == ('id', 'score')

    d = Document()
    assert d.non_empty_fields == ('id',)

    d = Document(id='')
    assert not d.non_empty_fields


def test_update_score_embedding():
    d = Document()
    d_score = Document(score=NamedScore(value=42))

    d.update(d_score)
    assert d.score.value == 42


def test_update_exclude_field():
    s, d = get_test_doc()

    d.update(s, exclude_fields=('id', 'embedding', 'chunks'))
    assert d.content == 'hello-world'
    assert d.id == '🐦'
    assert d.tags['a'] == 'b'
    np.testing.assert_array_equal(d.embedding, np.array([4, 5, 6]))
    assert d.chunks[0].id == '🐯'

    d.update(s, exclude_fields=('chunks',))
    # check if merging on embedding is correct
    np.testing.assert_array_equal(d.embedding, np.array([1, 2, 3]))

    d.update(s, exclude_fields=('embedding',))
    # check if merging on embedding is correct
    assert len(d.chunks) == 1
    assert d.chunks[0].id == '🐢'


def test_get_attr():
    d = Document(
        {
            'id': '123',
            'text': 'document',
            'feature1': 121,
            'name': 'name',
            'tags': {'id': 'identity', 'a': 'b', 'c': 'd'},
        }
    )
    d.score = NamedScore(value=42)

    required_keys = [
        'id',
        'text',
        'tags__name',
        'tags__feature1',
        'score__value',
        'tags__c',
        'tags__id',
        'tags__inexistant',
        'inexistant',
    ]
    res = d.get_attrs(*required_keys)

    assert len(res.keys()) == len(required_keys)
    assert res['id'] == '123'
    assert res['tags__feature1'] == 121
    assert res['tags__name'] == 'name'
    assert res['text'] == 'document'
    assert res['tags__c'] == 'd'
    assert res['tags__id'] == 'identity'
    assert res['score__value'] == 42
    assert res['tags__inexistant'] is None
    assert res['inexistant'] is None

    res2 = d.get_attrs(*['tags', 'text'])
    assert len(res2.keys()) == 2
    assert res2['text'] == 'document'
    assert res2['tags'] == d.tags

    d = Document({'id': '123', 'tags': {'outterkey': {'innerkey': 'real_value'}}})
    res3 = d.get_attrs(*['tags__outterkey__innerkey'])
    assert len(res3.keys()) == 1
    assert res3['tags__outterkey__innerkey'] == 'real_value'

    d = Document(content=np.array([1, 2, 3]))
    res4 = d.get_attrs(*['blob'])
    np.testing.assert_equal(res4['blob'], np.array([1, 2, 3]))


def test_pb_obj2dict():
    document = Document()
    with document:
        document.text = 'this is text'
        document.tags['id'] = 'id in tags'
        document.tags['inner_dict'] = {'id': 'id in inner_dict'}
        with Document() as chunk:
            chunk.text = 'text in chunk'
            chunk.tags['id'] = 'id in chunk tags'
        document.chunks.add(chunk)
    res = document.get_attrs('text', 'tags', 'chunks')
    assert res['text'] == 'this is text'
    assert res['tags']['id'] == 'id in tags'
    assert res['tags']['inner_dict']['id'] == 'id in inner_dict'
    rcs = list(res['chunks'])
    assert len(rcs) == 1
    assert isinstance(rcs[0], Document)
    assert rcs[0].text == 'text in chunk'
    assert rcs[0].tags['id'] == 'id in chunk tags'
