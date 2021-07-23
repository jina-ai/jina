import pytest
import numpy as np

from jina import Document, DocumentArray
from jina.types.arrays.memmap import DocumentArrayMemmap


@pytest.fixture
def list_doc_examples():
    d1 = Document(tags={'city': 'Barcelona', 'phone': 'None'})
    d2 = Document(tags={'city': 'Berlin', 'phone': '648907348'})
    d3 = Document(tags={'city': 'Paris', 'phone': 'None'})
    d4 = Document(tags={'city': 'Brussels', 'phone': 'None'})
    docs = [d1, d2, d3, d4]
    return docs


@pytest.fixture
def docarray_type(list_doc_examples):
    return DocumentArray(list_doc_examples)


@pytest.fixture
def docarray_memmap_type(list_doc_examples, tmpdir):
    doc_array_memmap = DocumentArrayMemmap(tmpdir)
    doc_array_memmap.extend(list_doc_examples)
    return doc_array_memmap


@pytest.mark.parametrize('doc_array', [docarray_type, docarray_memmap_type])
def test_single_regex(doc_array):
    regexes = {'city': r'B.*'}
    filtered_doc_array = doc_array.find(regexes=regexes)

    # Examples with Barcelona, Berlin, Brussels should match
    assert len(filtered_doc_array) == 3


def test_multiple_regex(list_doc_examples, tmpdir):
    regexes = {'city': r'B.*', 'phone': 'Non'}
    doc_array = DocumentArray(list_doc_examples)
    doc_array_memmap = DocumentArrayMemmap(tmpdir)
    doc_array_memmap.extend(list_doc_examples)

    filtered_doc_array = doc_array.find(
        regexes=regexes, traversal_paths=['r'], operator='==', value=2
    )
    filtered_doc_array_memmap = doc_array_memmap.find(
        regexes=regexes, traversal_paths=['r'], operator='==', value=2
    )

    # Examples with Barcelona, Brussels should match
    assert len(filtered_doc_array) == 2
    assert len(filtered_doc_array_memmap) == 2
