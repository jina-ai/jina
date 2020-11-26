
import pytest
import numpy as np

from jina import Document
from jina.excepts import BadDocType, LengthMismatchException
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
    return chunk

@pytest.fixture(scope='function')
def chunk_2(textual_embedding):
    chunk = Document()
    chunk.modality = 'textual'
    chunk.content = textual_embedding
    return chunk

@pytest.fixture(scope='function')
def chunk_3(textual_embedding):
    chunk = Document()
    chunk.modality = 'textual'
    chunk.embedding = textual_embedding
    return chunk

@pytest.yield_fixture(scope='function')
def multimodal_document(chunk_1, chunk_2):
    with MultimodalDocument() as md:
        md.tags['id'] = 1
        md.text = b'hello world'
        md.embedding = np.random.random([10 + np.random.randint(0, 1)])
        md.chunks.add(chunk_1) # attach a document with embedding and without content
        md.chunks.add(chunk_2) # attach a document with content and without embedding
        yield md

def test_modalities_property(multimodal_document):
    doc_modalities = multimodal_document.modalities
    assert len(doc_modalities) == 2
    assert 'visual' in doc_modalities
    assert 'textual' in doc_modalities

def test_modality_content_mapping_property(multimodal_document, visual_embedding, textual_embedding):
    mapping = multimodal_document.modality_content_mapping
    assert isinstance(mapping, dict)
    np.testing.assert_array_equal(mapping['textual'], textual_embedding)
    np.testing.assert_array_equal(mapping['visual'], visual_embedding)

def test_extract_content_by_modality(multimodal_document, visual_embedding, textual_embedding):
    textual = multimodal_document.extract_content_by_modality(modality='textual')
    np.testing.assert_array_equal(textual, textual_embedding)
    visual = multimodal_document.extract_content_by_modality(modality='visual')
    np.testing.assert_array_equal(visual, visual_embedding)

def test_multimodal_document_fail_bad_doctype(visual_embedding):
    # the multimodal document don't have any chunks
    with pytest.raises(BadDocType):
        md = MultimodalDocument()
        md.tags['id'] = 1
        md.embedding = visual_embedding
        md.modality_content_mapping

def test_multimodal_document_fail_length_mismatch(multimodal_document, chunk_3):
    # the multimodal document has 3 chunks, while 2 types of modalities.
    with pytest.raises(LengthMismatchException):
        multimodal_document.chunks.add(chunk_3)
        multimodal_document.modality_content_mapping

def test_from_chunks_success(chunk_1, chunk_2):
    md = MultimodalDocument.from_chunks(chunks=[chunk_1, chunk_2])
    assert len(md.modalities) == 2
    assert 'visual' and 'textual' in md.modalities

def test_from_chunks_fail(chunk_1, chunk_2, chunk_3):
    with pytest.raises(LengthMismatchException):
        MultimodalDocument.from_chunks(chunks=[chunk_1, chunk_2, chunk_3])
