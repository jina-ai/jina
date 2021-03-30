from copy import deepcopy

import pytest
import numpy as np

from jina import Document
from jina.types.lists import DocumentList

DOCUMENTS_PER_LEVEL = 1


@pytest.fixture(scope='function')
def document_factory():
    class DocumentFactory(object):
        def create(self, idx, text):
            with Document(id=idx) as d:
                d.tags['id'] = idx
                d.text = text
            return d

    return DocumentFactory()


@pytest.fixture
def docs(document_factory):
    return [
        document_factory.create(1, 'test 1'),
        document_factory.create(2, 'test 1'),
        document_factory.create(3, 'test 3'),
    ]


@pytest.fixture
def doclist(docs):
    return DocumentList(docs)


def test_length(doclist, docs):
    assert len(docs) == len(doclist) == 3


def test_append(doclist, document_factory):
    doc = document_factory.create(4, 'test 4')
    doclist.append(doc)
    assert doclist[-1].id == doc.id


def test_add(doclist, document_factory):
    doc = document_factory.create(4, 'test 4')
    doclist.add(doc)
    assert doclist[-1].id == doc.id


def test_union(doclist, document_factory):
    additional_doclist = DocumentList([])
    for idx in range(4, 10):
        doc = document_factory.create(idx, f'test {idx}')
        additional_doclist.add(doc)
    union = doclist + additional_doclist
    for idx in range(0, 3):
        assert union[idx].id == doclist[idx].id
    for idx in range(0, 6):
        assert union[idx + 3].id == additional_doclist[idx].id


def test_union_inplace(doclist, document_factory):
    additional_doclist = DocumentList([])
    for idx in range(4, 10):
        doc = document_factory.create(idx, f'test {idx}')
        additional_doclist.add(doc)
    union = deepcopy(doclist)
    union += additional_doclist
    for idx in range(0, 3):
        assert union[idx].id == doclist[idx].id
    for idx in range(0, 6):
        assert union[idx + 3].id == additional_doclist[idx].id


def test_extend(doclist, document_factory):
    docs = [document_factory.create(4, 'test 4'), document_factory.create(5, 'test 5')]
    doclist.extend(docs)
    assert len(doclist) == 5
    assert doclist[-1].tags['id'] == 5
    assert doclist[-1].text == 'test 5'


def test_clear(doclist):
    doclist.clear()
    assert len(doclist) == 0


def test_delete(doclist, document_factory):
    doc = document_factory.create(4, 'test 4')
    doclist.append(doc)
    del doclist[-1]
    assert len(doclist) == 3
    assert doclist == doclist


def test_build(doclist):
    doclist.build()


def test_list_get_success(doclist, document_factory):
    doclist.build()
    doc = document_factory.create(4, 'test 4')
    doc_id = 2
    doclist[doc_id] = doc
    assert doclist[doc_id].text == 'test 4'
    doc_0_id = doclist[0].id
    doclist[doc_0_id] = doc
    assert doclist[doc_0_id].text == 'test 4'


def test_list_get_from_slice_success(docs, document_factory):
    doclist = DocumentList(docs)
    assert len(doclist[:1]) == 1
    assert len(doclist[:2]) == 2
    assert len(doclist[:3]) == 3
    assert len(doclist[:100]) == 3

    assert len(doclist[1:]) == 2
    assert len(doclist[2:]) == 1
    assert len(doclist[3:]) == 0
    assert len(doclist[100:]) == 0


def test_list_get_fail(doclist, document_factory):
    doclist.build()
    with pytest.raises(IndexError):
        doclist[0.1] = 1  # Set fail, not a supported type
    with pytest.raises(IndexError):
        doclist[0.1]  # Get fail, not a supported type


def test_doclist_init(docs, doclist):
    # we need low-level protobuf generation for testing
    assert len(docs) == len(doclist)
    for d, od in zip(docs, doclist):
        assert isinstance(d, Document)
        assert d.id == od.id
        assert d.text == od.text


def test_doclist_iterate_twice(doclist):
    j = 0
    for _ in doclist:
        for _ in doclist:
            j += 1
    assert j == len(doclist) ** 2


def test_doclist_reverse(docs, doclist):
    ids = [d.id for d in docs]
    doclist.reverse()
    ids2 = [d.id for d in doclist]
    assert list(reversed(ids)) == ids2


def test_match_chunk_list():
    with Document() as d:
        d.content = 'hello world'

    m = d.matches.new()
    assert m.granularity == d.granularity
    assert m.adjacency == d.adjacency + 1
    assert len(d.matches) == 1

    c = d.chunks.new()
    assert c.granularity == d.granularity + 1
    assert c.adjacency == d.adjacency
    assert len(d.chunks) == 1


def add_chunk(doc):
    with Document() as chunk:
        chunk.granularity = doc.granularity + 1
        chunk.adjacency = doc.adjacency
        doc.chunks.append(chunk)
        return chunk


def add_match(doc):
    with Document() as match:
        match.granularity = doc.granularity
        match.adjacency = doc.adjacency + 1
        doc.matches.add(match)
        return match


@pytest.fixture
def documentlist():
    """ Builds up a complete chunk-match structure, with a depth of 2 in both directions recursively. """
    max_granularity = 2
    max_adjacency = 2

    def iterate_build(document, current_granularity, current_adjacency):
        if current_granularity < max_granularity:
            for i in range(DOCUMENTS_PER_LEVEL):
                chunk = add_chunk(document)
                iterate_build(chunk, chunk.granularity, chunk.adjacency)
        if current_adjacency < max_adjacency:
            for i in range(DOCUMENTS_PER_LEVEL):
                match = add_match(document)
                iterate_build(match, match.granularity, match.adjacency)

    docs = []
    for base_id in range(DOCUMENTS_PER_LEVEL):
        with Document() as d:
            d.granularity = 0
            d.adjacency = 0
            docs.append(d)
            iterate_build(d, 0, 0)
    return documentlist(docs)


def callback_fn(docs, *args, **kwargs) -> None:
    for doc in docs:
        add_chunk(doc)
        add_match(doc)
        add_match(doc)


@pytest.mark.parametrize('stack', [False, True])
@pytest.mark.parametrize('num_rows', [1, 2, 3])
@pytest.mark.parametrize('field', ['content', 'blob', 'embedding'])
def test_get_content(stack, num_rows, field):
    batch_size = 10
    embed_size = 20

    kwargs = {field: np.random.random((num_rows, embed_size))}

    docs = DocumentList([Document(**kwargs) for _ in range(batch_size)])
    docs.append(Document())

    contents, pts = docs.extract_docs(field, stack_contents=stack)
    if stack:
        assert isinstance(contents, np.ndarray)
        assert contents.shape == (batch_size, num_rows, embed_size)
    else:
        assert len(contents) == batch_size
        for content in contents:
            assert content.shape == (num_rows, embed_size)


@pytest.mark.parametrize('stack', [False, True])
@pytest.mark.parametrize('field', ['id', 'text'])
def test_get_content_text_fields(stack, field):
    batch_size = 10

    kwargs = {field: 'text'}

    docs = DocumentList([Document(**kwargs) for _ in range(batch_size)])

    contents, pts = docs.extract_docs(field, stack_contents=stack)
    if stack:
        assert isinstance(contents, np.ndarray)
        assert contents.shape == (batch_size,)
    assert len(contents) == batch_size
    for content in contents:
        assert content == 'text'


@pytest.mark.parametrize('stack', [False, True])
@pytest.mark.parametrize('bytes_input', [b'bytes', np.array([0, 0, 0]).tobytes()])
@pytest.mark.parametrize('field', ['content', 'buffer'])
def test_get_content_bytes_fields(stack, bytes_input, field):
    batch_size = 10

    kwargs = {field: bytes_input}

    docs = DocumentList([Document(**kwargs) for _ in range(batch_size)])

    contents, pts = docs.extract_docs(field, stack_contents=stack)

    assert len(contents) == batch_size
    assert isinstance(contents, list)
    for content in contents:
        assert isinstance(content, bytes)
        assert content == bytes_input


@pytest.mark.parametrize('stack', [False, True])
@pytest.mark.parametrize('fields', [['id', 'text'], ['content_hash', 'modality']])
def test_get_content_multiple_fields_text(stack, fields):
    batch_size = 10

    kwargs = {field: f'text-{field}' for field in fields}

    docs = DocumentList([Document(**kwargs) for _ in range(batch_size)])

    contents, pts = docs.extract_docs(*fields, stack_contents=stack)

    assert len(contents) == len(fields)
    assert isinstance(contents, list)
    if stack:
        assert isinstance(contents[0], np.ndarray)
        assert isinstance(contents[1], np.ndarray)

    for content in contents:
        assert len(content) == batch_size
        if stack:
            assert content.shape == (batch_size,)


@pytest.mark.parametrize('stack', [False, True])
@pytest.mark.parametrize('bytes_input', [b'bytes', np.array([0, 0, 0]).tobytes()])
def test_get_content_multiple_fields_text_buffer(stack, bytes_input):
    batch_size = 10
    fields = ['id', 'buffer']
    kwargs = {'id': 'text', 'buffer': bytes_input}

    docs = DocumentList([Document(**kwargs) for _ in range(batch_size)])

    contents, pts = docs.extract_docs(*fields, stack_contents=stack)

    assert len(contents) == len(fields)
    assert isinstance(contents, list)
    assert len(contents[0]) == batch_size
    if stack:
        assert isinstance(contents[0], np.ndarray)
        assert contents[0].shape == (batch_size,)
    assert isinstance(contents[1], list)
    assert isinstance(contents[1][0], bytes)

    for content in contents:
        assert len(content) == batch_size


@pytest.mark.parametrize('stack', [False, True])
@pytest.mark.parametrize('num_rows', [1, 2, 3])
def test_get_content_multiple_fields_arrays(stack, num_rows):
    fields = ['blob', 'embedding']

    batch_size = 10
    embed_size = 20

    kwargs = {field: np.random.random((num_rows, embed_size)) for field in fields}
    docs = DocumentList([Document(**kwargs) for _ in range(batch_size)])

    contents, pts = docs.extract_docs(*fields, stack_contents=stack)

    assert len(contents) == len(fields)
    assert isinstance(contents, list)
    if stack:
        assert isinstance(contents[0], np.ndarray)
        assert isinstance(contents[1], np.ndarray)

    for content in contents:
        assert len(content) == batch_size
        if stack:
            assert content.shape == (batch_size, num_rows, embed_size)
        else:
            for c in content:
                assert c.shape == (num_rows, embed_size)


@pytest.mark.parametrize('stack', [False, True])
@pytest.mark.parametrize('num_rows', [1, 2, 3])
def test_get_content_multiple_fields_merge(stack, num_rows):
    fields = ['embedding', 'text']

    batch_size = 10
    embed_size = 20

    kwargs = {
        field: np.random.random((num_rows, embed_size))
        if field == 'embedding'
        else 'text'
        for field in fields
    }
    docs = DocumentList([Document(**kwargs) for _ in range(batch_size)])

    contents, pts = docs.extract_docs(*fields, stack_contents=stack)

    assert len(contents) == len(fields)
    assert isinstance(contents, list)
    if stack:
        assert isinstance(contents[0], np.ndarray)
        assert isinstance(contents[1], np.ndarray)

    for content in contents:
        assert len(content) == batch_size

    if stack:
        assert contents[0].shape == (batch_size, num_rows, embed_size)
        assert contents[1].shape == (batch_size,)
    else:
        assert len(contents[0]) == batch_size
        assert len(contents[1]) == batch_size
        for c in contents[0]:
            assert c.shape == (num_rows, embed_size)
