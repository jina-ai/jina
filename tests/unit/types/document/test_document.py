import json
import os
from contextlib import contextmanager

import numpy as np
import pytest
import tensorflow as tf
import torch
from scipy.sparse import coo_matrix, bsr_matrix, csr_matrix, csc_matrix

from jina.proto.jina_pb2 import DocumentProto
from jina.types.document import Document
from jina.types.ndarray.generic import NdArray
from jina.types.request import Request
from jina.types.score import NamedScore
from tests import random_docs


def scipy_sparse_list():
    return [coo_matrix, bsr_matrix, csr_matrix, csc_matrix]


@pytest.fixture
def row():
    return np.array([0, 0, 1, 2, 2, 2])


@pytest.fixture
def column():
    return np.array([0, 2, 2, 0, 1, 2])


@pytest.fixture
def data():
    return np.array([1, 2, 3, 4, 5, 6])


@pytest.fixture(params=scipy_sparse_list())
def scipy_sparse_matrix(request, row, column, data):
    matrix_type = request.param
    return matrix_type((data, (row, column)), shape=(4, 10))


@pytest.fixture
def tf_sparse_matrix(row, column, data):
    indices = [(x, y) for x, y in zip(row, column)]
    return tf.SparseTensor(indices=indices, values=data, dense_shape=[4, 10])


@pytest.fixture
def torch_sparse_matrix(row, column, data):
    shape = [4, 10]
    indices = [list(row), list(column)]
    return torch.sparse_coo_tensor(indices, data, shape)


@pytest.mark.parametrize('field', ['blob', 'embedding', 'content'])
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


def test_sparse_get_set():
    d = Document()
    assert d.content is None
    mat1 = coo_matrix(np.array([1, 2, 3]))
    d.content = mat1
    assert (d.content != mat1).nnz == 0
    mat2 = coo_matrix(np.array([3, 2, 1]))
    assert (d.content != mat2).nnz != 0
    d.blob = mat2
    assert (d.content != mat2).nnz == 0


def test_doc_update_fields():
    a = Document()
    b = np.random.random([10, 10])
    c = {'tags': 'string', 'tag-tag': {'tags': 123.45}}
    d = [12, 34, 56]
    e = 'text-mod'
    w = 2.0
    a.set_attributes(embedding=b, tags=c, location=d, modality=e, weight=w)
    np.testing.assert_equal(a.embedding, b)
    assert list(a.location) == d
    assert a.modality == e
    assert a.tags == c
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
    a.uri = 'abcdefg'
    assert a.uri == 'abcdefg'
    a.content = 'abcdefg'
    assert a.text == 'abcdefg'
    assert not a.uri


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
    r = Request().as_typed_request('data')
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

    for idx, d in enumerate(rpb.data.docs):
        assert isinstance(d, DocumentProto)
        assert d.text == f'look I changed it! {idx}'

    # change again by following the pointers
    for d in doc_pointers:
        d.text = 'now i change it back'

    # iterate it again should see the change
    for idx, d in enumerate(rpb.data.docs):
        assert isinstance(d, DocumentProto)
        assert d.text == 'now i change it back'


def test_request_docs_chunks_mutable_iterator():
    """Test if weak reference work in nested docs"""
    r = Request().as_typed_request('data')
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

    for d in rpb.data.docs:
        assert isinstance(d, DocumentProto)
        for idx, c in enumerate(d.chunks):
            assert isinstance(c, DocumentProto)
            assert c.text == f'look I changed it! {idx}'

    # change again by following the pointers
    for d in doc_pointers:
        d.text = 'now i change it back'

    # iterate it again should see the change
    for d in rpb.data.docs:
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


def test_doc_plot(tmpdir):
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
    docs[0].plot(inline_display=True, output=os.path.join(tmpdir, 'doc.svg'))
    assert os.path.exists(os.path.join(tmpdir, 'doc.svg'))
    docs[0].plot()


@pytest.fixture
def test_docs():
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
    return (s, d)


@pytest.fixture
def expected_doc_fields():
    from jina.proto import jina_pb2

    return sorted(set(list(jina_pb2.DocumentProto().DESCRIPTOR.fields_by_name)))


@pytest.fixture
def ignored_doc_fields():
    return ['embedding', 'score', 'blob', 'buffer', 'text', 'tags', 'uri']


def test_document_to_json(expected_doc_fields, ignored_doc_fields):
    doc = Document()
    doc_dict = json.loads(doc.json())
    present_keys = sorted(doc_dict.keys())
    assert present_keys == ['id']


def test_document_to_dict(expected_doc_fields, ignored_doc_fields):
    doc = Document()
    doc_dict = doc.dict()
    present_keys = sorted(doc_dict.keys())
    assert present_keys == ['id']


def test_non_empty_fields():
    d_score = Document(scores={'score': NamedScore(value=42)})
    assert d_score.non_empty_fields == ('id', 'scores')

    d = Document()
    assert d.non_empty_fields == ('id',)

    d = Document(id='')
    assert not d.non_empty_fields


def test_get_attr_values():
    d = Document(
        {
            'id': '123',
            'text': 'document',
            'feature1': 121,
            'name': 'name',
            'tags': {'id': 'identity', 'a': 'b', 'c': 'd', 'e': [0, 1, {'f': 'g'}]},
        }
    )
    d.scores['metric'] = NamedScore(value=42)

    required_keys = [
        'id',
        'text',
        'tags__name',
        'tags__feature1',
        'scores__values__metric__value',
        'tags__c',
        'tags__id',
        'tags__inexistant',
        'tags__e__2__f',
        'inexistant',
    ]
    res = d.get_attributes(*required_keys)
    assert len(res) == len(required_keys)
    assert res[required_keys.index('id')] == '123'
    assert res[required_keys.index('tags__feature1')] == 121
    assert res[required_keys.index('tags__name')] == 'name'
    assert res[required_keys.index('text')] == 'document'
    assert res[required_keys.index('tags__c')] == 'd'
    assert res[required_keys.index('tags__id')] == 'identity'
    assert res[required_keys.index('scores__values__metric__value')] == 42
    assert res[required_keys.index('tags__inexistant')] is None
    assert res[required_keys.index('inexistant')] is None
    assert res[required_keys.index('tags__e__2__f')] == 'g'

    required_keys_2 = ['tags', 'text']
    res2 = d.get_attributes(*required_keys_2)
    assert len(res2) == 2
    assert res2[required_keys_2.index('text')] == 'document'
    assert res2[required_keys_2.index('tags')] == d.tags
    assert res2[required_keys_2.index('tags')].dict() == d.tags.dict()

    d = Document({'id': '123', 'tags': {'outterkey': {'innerkey': 'real_value'}}})
    required_keys_3 = ['tags__outterkey__innerkey']
    res3 = d.get_attributes(*required_keys_3)
    assert res3 == 'real_value'

    d = Document(content=np.array([1, 2, 3]))
    res4 = np.stack(d.get_attributes(*['blob']))
    np.testing.assert_equal(res4, np.array([1, 2, 3]))


def test_document_sparse_attributes_scipy(scipy_sparse_matrix):
    d = Document()
    d.embedding = scipy_sparse_matrix
    d.blob = scipy_sparse_matrix
    np.testing.assert_array_equal(d.embedding.todense(), scipy_sparse_matrix.todense())
    np.testing.assert_array_equal(d.blob.todense(), scipy_sparse_matrix.todense())


def test_document_sparse_attributes_tensorflow(tf_sparse_matrix):
    import tensorflow as tf

    d = Document()
    d.embedding = tf_sparse_matrix
    d.blob = tf_sparse_matrix
    np.testing.assert_array_equal(
        d.embedding.todense(), tf.sparse.to_dense(tf_sparse_matrix)
    )
    np.testing.assert_array_equal(
        d.blob.todense(), tf.sparse.to_dense(tf_sparse_matrix)
    )


def test_document_sparse_attributes_pytorch(torch_sparse_matrix):
    d = Document()
    d.embedding = torch_sparse_matrix
    d.blob = torch_sparse_matrix

    np.testing.assert_array_equal(
        d.embedding.todense(), torch_sparse_matrix.to_dense().numpy()
    )
    np.testing.assert_array_equal(
        d.blob.todense(), torch_sparse_matrix.to_dense().numpy()
    )


@pytest.mark.parametrize(
    'return_sparse_ndarray_cls_type, return_scipy_class_type, return_expected_type',
    [
        ('scipy', 'coo', coo_matrix),
        ('scipy', 'csr', csr_matrix),
        ('scipy', 'csc', csc_matrix),
        ('scipy', 'bsr', bsr_matrix),
        ('torch', None, torch.Tensor),
        ('tf', None, tf.SparseTensor),
    ],
)
@pytest.mark.parametrize('field', ['embedding', 'blob'])
def test_document_sparse_embedding(
    scipy_sparse_matrix,
    return_sparse_ndarray_cls_type,
    return_scipy_class_type,
    return_expected_type,
    field,
):
    d = Document()
    setattr(d, field, scipy_sparse_matrix)
    cls_type = None
    sparse_kwargs = {}
    if return_sparse_ndarray_cls_type == 'scipy':
        from jina.types.ndarray.sparse.scipy import SparseNdArray

        cls_type = SparseNdArray
        sparse_kwargs['sp_format'] = return_scipy_class_type
    elif return_sparse_ndarray_cls_type == 'torch':
        from jina.types.ndarray.sparse.pytorch import SparseNdArray

        cls_type = SparseNdArray
    elif return_sparse_ndarray_cls_type == 'tf':
        from jina.types.ndarray.sparse.tensorflow import SparseNdArray

        cls_type = SparseNdArray

    if field == 'blob':
        field_sparse = d.get_sparse_blob(
            sparse_ndarray_cls_type=cls_type, **sparse_kwargs
        )
    elif field == 'embedding':
        field_sparse = d.get_sparse_embedding(
            sparse_ndarray_cls_type=cls_type, **sparse_kwargs
        )

    assert field_sparse is not None
    assert isinstance(field_sparse, return_expected_type)
    if return_sparse_ndarray_cls_type == 'torch':
        assert field_sparse.is_sparse

    if return_sparse_ndarray_cls_type == 'scipy':
        np.testing.assert_equal(field_sparse.todense(), scipy_sparse_matrix.todense())
    elif return_sparse_ndarray_cls_type == 'torch':
        np.testing.assert_equal(
            field_sparse.to_dense().numpy(), scipy_sparse_matrix.todense()
        )
    elif return_scipy_class_type == 'tf':
        np.testing.assert_equal(
            tf.sparse.to_dense(field_sparse).numpy(), scipy_sparse_matrix.todense()
        )


def test_evaluations():
    document = Document()
    document.evaluations['operation'] = 10.0
    document.evaluations['operation'].op_name = 'operation'
    assert document.evaluations['operation'].value == 10.0
    assert document.evaluations['operation'].op_name == 'operation'


@contextmanager
def does_not_raise():
    yield


@pytest.mark.parametrize(
    'doccontent, expectation',
    [
        ({'content': 'hello', 'uri': 'https://jina.ai'}, pytest.raises(ValueError)),
        ({'content': 'hello', 'text': 'world'}, pytest.raises(ValueError)),
        ({'content': 'hello', 'blob': np.array([1, 2, 3])}, pytest.raises(ValueError)),
        ({'content': 'hello', 'buffer': b'hello'}, pytest.raises(ValueError)),
        ({'buffer': b'hello', 'text': 'world'}, pytest.raises(ValueError)),
        ({'content': 'hello', 'id': 1}, does_not_raise()),
    ],
)
def test_conflicting_doccontent(doccontent, expectation):
    with expectation:
        document = Document(**doccontent)
        assert document.content is not None


@pytest.mark.parametrize('val', [1, 1.0, np.float64(1.0)])
def test_doc_different_score_value_type(val):
    d = Document()
    d.scores['score'] = val
    assert int(d.scores['score'].value) == 1


def test_doc_match_score_assign():
    d = Document(id='hello')
    d1 = Document(d, copy=True, scores={'score': 123})
    d.matches = [d1]
    assert d.matches[0].scores['score'].value == 123
    assert d.matches[0].scores['score'].ref_id == d.id


def test_doc_update_given_empty_fields_and_attributes_identical(test_docs):
    # doc1 and doc2 has the same fields, id, content, tags, embedding and chunks.
    doc1, doc2 = test_docs
    doc1.update(source=doc2)
    assert doc1.id == doc2.id
    assert doc1.content == doc2.content
    assert doc1.tags == {'a': 'b', 'c': 'd'}  # tags will be merged.
    assert (doc1.embedding == doc2.embedding).all()
    assert doc1.chunks == doc2.chunks


def test_doc_update_given_empty_fields_and_destination_has_more_attributes(test_docs):
    # doc1 and doc2 has the same fields, id, content, tags, embedding and chunks.
    doc1, doc2 = test_docs
    # remove doc2 content field
    doc2._pb_body.ClearField(
        'content'
    )  # content of source "goodbye-world" was removed, not update this field.
    assert doc2.content is None
    doc1.update(source=doc2)
    assert doc1.id == doc2.id
    assert doc1.content == 'hello-world'  # doc1 content remains the same.
    assert doc1.tags == {'a': 'b', 'c': 'd'}  # tags will be merged.
    assert (doc1.embedding == doc2.embedding).all()
    assert doc1.chunks == doc2.chunks


def test_doc_update_given_empty_fields_and_source_has_more_attributes(test_docs):
    # doc1 and doc2 has the same fields, id, content, tags, embedding and chunks.
    doc1, doc2 = test_docs
    # remove doc2 content field
    doc1._pb_body.ClearField('content')  # content of destination was removed.
    assert doc1.content is None
    doc1.update(source=doc2)
    assert doc1.id == doc2.id
    assert (
        doc1.content == doc2.content
    )  # destination content `None` was updated by source's content.
    assert doc1.tags == {'a': 'b', 'c': 'd'}  # tags will be merged.
    assert (doc1.embedding == doc2.embedding).all()
    assert doc1.chunks == doc2.chunks


def test_doc_update_given_singular_fields_and_attributes_identical(test_docs):
    # doc1 and doc2 has the same fields, id, content, tags, embedding and chunks.
    doc1, doc2 = test_docs
    # After update, only specified fields are updated.
    doc1.update(source=doc2, fields=['id', 'text'])
    assert doc1.id == doc2.id
    assert doc1.content == doc2.content  # None was updated by source's content.
    assert doc1.tags != doc2.tags
    assert doc1.tags == {'a': 'b'}
    assert (doc1.embedding != doc2.embedding).all()
    assert doc1.chunks != doc2.chunks


def test_doc_update_given_nested_fields_and_attributes_identical(test_docs):
    # doc1 and doc2 has the same fields, id, content, tags, embedding and chunks.
    doc1, doc2 = test_docs
    # After update, only specified nested fields are updated.
    doc1.update(source=doc2, fields=['tags', 'embedding', 'chunks'])
    assert doc1.id != doc2.id
    assert doc1.content != doc2.content  # None was updated by source's content.
    assert doc1.tags == {'a': 'b', 'c': 'd'}  # tags will be merged.
    assert (doc1.embedding == doc2.embedding).all()
    assert (
        doc1.chunks[0].parent_id != doc2.chunks[0].parent_id
    )  # parent id didn't change since id field not updated.
    assert doc1.chunks[0].id == doc2.chunks[0].id
    assert doc1.chunks[0].content_hash == doc2.chunks[0].content_hash


def test_doc_update_given_fields_and_destination_has_more_attributes(test_docs):
    # doc1 and doc2 has the same fields, id, content, tags, embedding and chunks.
    # After update, the specified fields will be cleared.
    doc1, doc2 = test_docs
    # remove doc2 text field
    doc2._pb_body.ClearField('text')
    assert doc2.text == ''
    assert doc2.content is None
    doc1.update(source=doc2, fields=['text'])
    assert doc1.text == ''
    assert doc1.tags != doc2.tags
    assert doc1.tags == {'a': 'b'}
    assert (doc1.embedding != doc2.embedding).all()
    assert doc1.chunks != doc2.chunks


def test_doc_update_given_fields_and_source_has_more_attributes(test_docs):
    # doc1 and doc2 has the same fields, id, content, tags, embedding and chunks.
    # After update, the specified fields will be replaced by source attribuet value.
    doc1, doc2 = test_docs
    # remove doc2 text field
    doc1._pb_body.ClearField('text')
    assert doc1.text == ''
    assert doc1.content is None
    doc1.update(source=doc2, fields=['text'])
    assert doc1.id != doc2.id
    assert doc1.content == doc2.content  # None was updated by source's content
    assert doc1.tags != doc2.tags
    assert doc1.tags == {'a': 'b'}
    assert (doc1.embedding != doc2.embedding).all()
    assert doc1.chunks != doc2.chunks


def test_doc_update_given_content_hash_updated(test_docs):
    doc1, doc2 = test_docs
    doc1.update_content_hash()
    doc2.update(doc1)
    assert doc1.content_hash == doc2.content_hash


def test_document_pretty_dict():
    doc = Document(
        blob=np.array([[0, 1, 2], [2, 1, 0]]),
        embedding=np.array([1.0, 2.0, 3.0]),
        tags={'hello': 'world'},
    )
    chunk = Document(doc, copy=True)
    chunk.blob = np.array([[3, 4, 5], [5, 4, 3]])
    chunk.embedding = np.array([4.0, 5.0, 6.0])
    match = Document(doc, copy=True)
    match.blob = np.array([[6, 7, 8], [8, 7, 6]])
    match.embedding = np.array([7.0, 8.0, 9.0])
    doc.chunks.append(chunk)
    doc.matches.append(match)
    assert doc.tags == {'hello': 'world'}
    assert doc.blob.tolist() == [[0, 1, 2], [2, 1, 0]]
    assert doc.embedding.tolist() == [1.0, 2.0, 3.0]
    assert doc.chunks[0].tags == {'hello': 'world'}
    assert doc.chunks[0].blob.tolist() == [[3, 4, 5], [5, 4, 3]]
    assert doc.chunks[0].embedding.tolist() == [4.0, 5.0, 6.0]
    assert doc.matches[0].tags == {'hello': 'world'}
    assert doc.matches[0].blob.tolist() == [[6, 7, 8], [8, 7, 6]]
    assert doc.matches[0].embedding.tolist() == [7.0, 8.0, 9.0]

    d = doc.dict(prettify_ndarrays=True)
    assert d['blob'] == [[0, 1, 2], [2, 1, 0]]
    assert d['embedding'] == [1.0, 2.0, 3.0]
    assert d['tags'] == {'hello': 'world'}
    assert d['chunks'][0]['blob'] == [[3, 4, 5], [5, 4, 3]]
    assert d['chunks'][0]['embedding'] == [4.0, 5.0, 6.0]
    assert d['chunks'][0]['tags'] == {'hello': 'world'}
    assert d['matches'][0]['blob'] == [[6, 7, 8], [8, 7, 6]]
    assert d['matches'][0]['embedding'] == [7.0, 8.0, 9.0]
    assert d['matches'][0]['tags'] == {'hello': 'world'}

    d_reconstructed = Document(d)
    assert d_reconstructed.tags == {'hello': 'world'}
    assert d_reconstructed.blob.tolist() == [[0, 1, 2], [2, 1, 0]]
    assert d_reconstructed.embedding.tolist() == [1.0, 2.0, 3.0]
    assert d_reconstructed.chunks[0].tags == {'hello': 'world'}
    assert d_reconstructed.chunks[0].blob.tolist() == [[3, 4, 5], [5, 4, 3]]
    assert d_reconstructed.chunks[0].embedding.tolist() == [4.0, 5.0, 6.0]
    assert d_reconstructed.matches[0].tags == {'hello': 'world'}
    assert d_reconstructed.matches[0].blob.tolist() == [[6, 7, 8], [8, 7, 6]]
    assert d_reconstructed.matches[0].embedding.tolist() == [7.0, 8.0, 9.0]


def test_document_pretty_json():
    doc = Document(
        blob=np.array([[0, 1, 2], [2, 1, 0]]),
        embedding=np.array([1.0, 2.0, 3.0]),
        tags={'hello': 'world'},
    )
    doc.chunks.append(Document(doc, copy=True))
    doc.matches.append(Document(doc, copy=True))
    assert doc.tags == {'hello': 'world'}
    assert doc.blob.tolist() == [[0, 1, 2], [2, 1, 0]]
    assert doc.embedding.tolist() == [1.0, 2.0, 3.0]
    assert doc.chunks[0].tags == {'hello': 'world'}
    assert doc.chunks[0].blob.tolist() == [[0, 1, 2], [2, 1, 0]]
    assert doc.chunks[0].embedding.tolist() == [1.0, 2.0, 3.0]
    assert doc.matches[0].tags == {'hello': 'world'}
    assert doc.matches[0].blob.tolist() == [[0, 1, 2], [2, 1, 0]]
    assert doc.matches[0].embedding.tolist() == [1.0, 2.0, 3.0]
    doc_json = doc.json(prettify_ndarrays=True)
    d = json.loads(doc_json)
    assert d['blob'] == [[0, 1, 2], [2, 1, 0]]
    assert d['embedding'] == [1.0, 2.0, 3.0]
    assert d['tags'] == {'hello': 'world'}
    assert d['chunks'][0]['blob'] == [[0, 1, 2], [2, 1, 0]]
    assert d['chunks'][0]['embedding'] == [1.0, 2.0, 3.0]
    assert d['chunks'][0]['tags'] == {'hello': 'world'}
    assert d['matches'][0]['blob'] == [[0, 1, 2], [2, 1, 0]]
    assert d['matches'][0]['embedding'] == [1.0, 2.0, 3.0]
    assert d['matches'][0]['tags'] == {'hello': 'world'}

    d_reconstructed = Document(doc_json)
    assert d_reconstructed.tags == {'hello': 'world'}
    assert d_reconstructed.blob.tolist() == [[0, 1, 2], [2, 1, 0]]
    assert d_reconstructed.embedding.tolist() == [1.0, 2.0, 3.0]
    assert d_reconstructed.chunks[0].tags == {'hello': 'world'}
    assert d_reconstructed.chunks[0].blob.tolist() == [[0, 1, 2], [2, 1, 0]]
    assert d_reconstructed.chunks[0].embedding.tolist() == [1.0, 2.0, 3.0]
    assert d_reconstructed.matches[0].tags == {'hello': 'world'}
    assert d_reconstructed.matches[0].blob.tolist() == [[0, 1, 2], [2, 1, 0]]
    assert d_reconstructed.matches[0].embedding.tolist() == [1.0, 2.0, 3.0]


def test_document_init_with_scores_and_evaluations():
    d = Document(
        scores={
            'euclidean': 50,
            'cosine': NamedScore(value=1.0),
            'score1': NamedScore(value=2.0).proto,
            'score2': np.int(5),
        },
        evaluations={
            'precision': 50,
            'recall': NamedScore(value=1.0),
            'eval1': NamedScore(value=2.0).proto,
            'eval2': np.int(5),
        },
    )
    assert d.scores['euclidean'].value == 50
    assert d.scores['cosine'].value == 1.0
    assert d.scores['score1'].value == 2.0
    assert d.scores['score2'].value == 5

    assert d.evaluations['precision'].value == 50
    assert d.evaluations['recall'].value == 1.0
    assert d.evaluations['eval1'].value == 2.0
    assert d.evaluations['eval2'].value == 5


def test_document_scores_delete():
    d = Document(
        scores={
            'euclidean': 50,
            'cosine': NamedScore(value=1.0),
            'score1': NamedScore(value=2.0).proto,
            'score2': np.int(5),
        },
        evaluations={
            'precision': 50,
            'recall': NamedScore(value=1.0),
            'eval1': NamedScore(value=2.0).proto,
            'eval2': np.int(5),
        },
    )
    assert d.scores['euclidean'].value == 50
    assert d.scores['cosine'].value == 1.0
    assert d.scores['score1'].value == 2.0
    assert d.scores['score2'].value == 5

    assert d.evaluations['precision'].value == 50
    assert d.evaluations['recall'].value == 1.0
    assert d.evaluations['eval1'].value == 2.0
    assert d.evaluations['eval2'].value == 5

    assert 'precision' in d.evaluations
    del d.evaluations['precision']
    assert 'precision' not in d.evaluations
    assert 'cosine' in d.scores
    del d.scores['cosine']
    assert 'cosine' not in d.scores


def test_manipulated_tags():
    t = {
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
    doc = Document(tags=t)
    assert len(doc.tags) == 5
    assert len(doc.tags.keys()) == 5
    assert len(doc.tags.values()) == 5
    assert len(doc.tags.items()) == 5
    assert 'key_int' in doc.tags
    assert 'key_float' in doc.tags
    assert 'key_string' in doc.tags
    assert 'key_array' in doc.tags
    assert 'key_nested' in doc.tags

    assert 0 in doc.tags.values()
    assert 1.5 in doc.tags.values()
    assert 'string_value' in doc.tags.values()

    assert doc.tags['key_int'] == 0
    assert doc.tags['key_float'] == 1.5
    assert doc.tags['key_string'] == 'string_value'
    assert len(doc.tags['key_array']) == 2
    assert doc.tags['key_array'][0] == 0
    assert doc.tags['key_array'][1] == 1
    assert len(doc.tags['key_nested'].keys()) == 3
    assert doc.tags['key_nested']['key_nested_int'] == 2
    assert doc.tags['key_nested']['key_nested_string'] == 'string_nested_value'
    assert len(doc.tags['key_nested']['key_nested_nested'].keys()) == 1
    assert len(doc.tags['key_nested']['key_nested_nested']['empty']) == 0


def test_tags_update_nested():
    d = Document()
    d.tags = {'hey': {'bye': 4}}
    assert d.tags['hey']['bye'] == 4
    d.tags['hey']['bye'] = 5
    assert d.tags['hey']['bye'] == 5


def test_tag_compare_dict():
    d = Document()
    d.tags = {'hey': {'bye': 4}}
    assert d.tags == {'hey': {'bye': 4}}
    assert d.tags.dict() == {'hey': {'bye': 4}}

    d.tags = {'hey': [1, 2]}
    assert d.tags == {'hey': [1, 2]}
    assert d.tags.dict() == {'hey': [1, 2]}


def test_tags_update_nested_lists():
    from jina import Document
    from jina.types.list import ListView
    from jina.types.struct import StructView

    d = Document()
    d.tags = {
        'hey': {'nested': True, 'list': ['elem1', 'elem2', {'inlist': 'here'}]},
        'hoy': [0, 1],
    }
    assert d.tags.dict() == {
        'hey': {'nested': True, 'list': ['elem1', 'elem2', {'inlist': 'here'}]},
        'hoy': [0, 1],
    }
    assert d.tags == {
        'hey': {'nested': True, 'list': ['elem1', 'elem2', {'inlist': 'here'}]},
        'hoy': [0, 1],
    }
    assert isinstance(d.tags['hoy'], ListView)
    assert isinstance(d.tags['hey']['list'], ListView)
    assert isinstance(d.tags['hey']['list'][2], StructView)
    d.tags['hey']['nested'] = False
    d.tags['hey']['list'][1] = True
    d.tags['hey']['list'][2]['inlist'] = 'not here'
    d.tags['hoy'][0] = 1

    assert d.tags['hey']['nested'] is False
    assert d.tags['hey']['list'][1] is True
    assert d.tags['hey']['list'][2]['inlist'] == 'not here'
    assert d.tags['hoy'][0] == 1
