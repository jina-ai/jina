import numpy as np
import pytest
from jina import Document
from jina.excepts import BadDocType
from jina.types.document.multimodal import MultimodalDocument


@pytest.fixture(scope='function')
def visual_embedding():
    np.random.seed(0)
    return np.random.random([10 + np.random.randint(0, 1)])


@pytest.fixture(scope='function')
def textual_embedding():
    np.random.seed(1)
    return np.random.random([10 + np.random.randint(0, 1)])


@pytest.fixture(scope='function')
def chunk_1(visual_embedding):
    chunk = Document()
    chunk.modality = 'visual'
    chunk.embedding = visual_embedding
    chunk.granularity = 0
    return chunk


@pytest.fixture(scope='function')
def chunk_2(textual_embedding):
    chunk = Document()
    chunk.modality = 'textual'
    chunk.content = textual_embedding
    chunk.granularity = 0
    return chunk


@pytest.fixture(scope='function')
def chunk_3(textual_embedding):
    chunk = Document()
    chunk.modality = 'textual'
    chunk.embedding = textual_embedding
    chunk.granularity = 0
    return chunk


@pytest.fixture(scope='function')
def chunk_4(textual_embedding):
    chunk = Document()
    chunk.modality = 'textual'
    chunk.embedding = textual_embedding
    chunk.granularity = 1
    return chunk


@pytest.fixture(scope='function')
def chunk_5(visual_embedding):
    chunk = Document()
    chunk.modality = 'visual'
    chunk.embedding = visual_embedding
    chunk.granularity = 3
    return chunk


@pytest.fixture(scope='function')
def chunk_6(textual_embedding):
    chunk = Document()
    chunk.modality = 'textual'
    chunk.content = textual_embedding
    chunk.granularity = 3
    return chunk


@pytest.fixture(scope='function')
def modality_content_mapping():
    return {
        'visual': 'content visual',
        'textual': 'content textual'
    }


@pytest.yield_fixture(scope='function')
def multimodal_document(chunk_1, chunk_2):
    with MultimodalDocument() as md:
        md.tags['id'] = 1
        md.text = b'hello world'
        md.embedding = np.random.random([10 + np.random.randint(0, 1)])
        md.chunks.add(chunk_1)  # attach a document with embedding and without content
        md.chunks.add(chunk_2)  # attach a document with content and without embedding
        yield md


def test_modalities_property(multimodal_document):
    doc_modalities = multimodal_document.modalities
    assert len(doc_modalities) == 2
    assert 'visual' in doc_modalities
    assert 'textual' in doc_modalities


def test_modality_content_mapping_property(multimodal_document, visual_embedding, textual_embedding):
    mapping = multimodal_document.modality_content_map
    assert isinstance(mapping, dict)
    np.testing.assert_array_equal(mapping['textual'], textual_embedding)
    np.testing.assert_array_equal(mapping['visual'], visual_embedding)


def test_extract_content_from_modality(multimodal_document, visual_embedding, textual_embedding):
    textual = multimodal_document['textual']
    np.testing.assert_array_equal(textual, textual_embedding)
    visual = multimodal_document['visual']
    np.testing.assert_array_equal(visual, visual_embedding)


def test_multimodal_document_fail_bad_doctype(visual_embedding):
    # the multimodal document don't have any chunks
    md = MultimodalDocument()
    md.tags['id'] = 1
    md.embedding = visual_embedding
    assert not md.is_valid


def test_multimodal_document_fail_length_mismatch(multimodal_document, chunk_3):
    # the multimodal document has 3 chunks, while 2 types of modalities.
    multimodal_document.chunks.add(chunk_3)
    assert not multimodal_document.is_valid


def test_from_chunks_success(chunk_1, chunk_2):
    md = MultimodalDocument(chunks=[chunk_1, chunk_2])
    assert len(md.modalities) == 2
    assert 'visual' and 'textual' in md.modalities
    assert len(md.chunks) == 2
    assert md.granularity == md.chunks[0].granularity - 1
    assert md.chunks[0].granularity == 1


def test_from_chunks_granularity_2(chunk_5, chunk_6):
    md = MultimodalDocument(chunks=[chunk_5, chunk_6])
    assert len(md.modalities) == 2
    assert 'visual' and 'textual' in md.modalities
    assert len(md.chunks) == 2
    assert md.granularity == md.chunks[0].granularity - 1
    assert md.chunks[0].granularity == 3


def test_assert_granularity(chunk_1, chunk_6):
    with pytest.raises(BadDocType):
        md = MultimodalDocument(chunks=[chunk_1, chunk_6])


def test_from_chunks_fail_length_mismatch(chunk_1, chunk_2, chunk_3):
    """Initialize a :class:`MultimodalDocument` expect to fail which has 3 chunks
    with 2 modalities.
    """
    assert not MultimodalDocument(chunks=[chunk_1, chunk_2, chunk_3]).is_valid


def test_from_chunks_fail_multiple_granularity(chunk_1, chunk_2, chunk_4):
    """Initialize a :class:`MultimodalDocument` expect to fail which has 3 chunks with different
    granularity value, expect all chunks has the same granularity value.
    """
    with pytest.raises(BadDocType):
        MultimodalDocument(chunks=[chunk_1, chunk_2, chunk_4])


def test_from_content_category_mapping(modality_content_mapping):
    md = MultimodalDocument(modality_content_map=modality_content_mapping)
    assert len(md.modalities) == 2
    assert 'visual' and 'textual' in md.modalities
    assert len(md.chunks) == 2
    assert md.granularity == md.chunks[0].granularity - 1
