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


def test_single_regex(list_doc_examples, tmpdir):
    regexes = {'city': r'B.*'}
    doc_array = DocumentArray(list_doc_examples)
    doc_array_memmap = DocumentArrayMemmap(tmpdir)
    doc_array_memmap.extend(list_doc_examples)

    filtered_doc_array = doc_array.find(regexes=regexes)
    filtered_doc_array_memmap = doc_array_memmap.find(regexes=regexes)

    # Examples with Barcelona, Berlin, Brussels should match
    assert len(filtered_doc_array) == 3
    assert len(filtered_doc_array_memmap) == 3


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
