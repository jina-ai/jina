
import pytest
import numpy as np

from jina.types.document import Document
from jina.types.document.multimodal import MultimodalDocument

@pytest.fixture(scope='function')
def visual_embedding():
    np.random.seed(0)
    return np.random.random([10 + np.random.randint(0, 1)])

@pytest.fixture(scope='function')
def textual_embedding():
    np.random.seed(1)
    return np.random.random([10 + np.random.randint(0, 1)])

@pytest.yield_fixture(scope='function')
def multimodal_document(visual_embedding, textual_embedding):
    with MultimodalDocument() as md:
        md.tags['id'] = 1
        md.text = b'hello world'
        md.embedding = np.random.random([10 + np.random.randint(0, 1)])
        with Document() as chunk_1: # attach a document with embedding and without content
            chunk_1.modality = 'visual'
            chunk_1.embedding = visual_embedding
            md.chunks.add(chunk_1)
        with Document() as chunk_2: # attach a document with content and without embedding
            chunk_2.modality = 'textual'
            chunk_2.content = textual_embedding
            md.chunks.add(chunk_2)
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
