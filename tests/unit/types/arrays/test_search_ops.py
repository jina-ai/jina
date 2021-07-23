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


def docarray_type(list_doc_examples, tmpdir):
    return DocumentArray(list_doc_examples)


def docarray_memmap_type(list_doc_examples, tmpdir):
    doc_array_memmap = DocumentArrayMemmap(tmpdir)
    doc_array_memmap.extend(list_doc_examples)
    return doc_array_memmap


@pytest.mark.parametrize('doc_array_creator', [docarray_type, docarray_memmap_type])
def test_single_regex(doc_array_creator, list_doc_examples, tmpdir):
    regexes = {'city': r'B.*'}
    doc_array = doc_array_creator(list_doc_examples, tmpdir)
    filtered_doc_array = doc_array.find(regexes=regexes)

    # Examples with Barcelona, Berlin, Brussels should match
    assert len(filtered_doc_array) == 3

    for d in filtered_doc_array:
        assert d.tags['city'].startswith('B')


@pytest.mark.parametrize('doc_array_creator', [docarray_type, docarray_memmap_type])
def test_multiple_regex(doc_array_creator, list_doc_examples, tmpdir):
    regexes = {'city': r'B.*', 'phone': 'Non'}
    doc_array = doc_array_creator(list_doc_examples, tmpdir)

    filtered_doc_array = doc_array.find(
        regexes=regexes, traversal_paths=['r'], operator='==', threshold=2
    )

    # Examples with Barcelona, Brussels should match
    assert len(filtered_doc_array) == 2

    for d in filtered_doc_array:
        assert d.tags['city'].startswith('B') and 'Non' in d.tags['phone']
