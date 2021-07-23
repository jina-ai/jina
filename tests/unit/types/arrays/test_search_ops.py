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
    D = DocumentArray(list_doc_examples)
    Dmemmap = DocumentArrayMemmap(tmpdir)
    Dmemmap.extend(list_doc_examples)

    Dfiltered = D.find(regexes=regexes)
    Dfiltered_memmap = Dmemmap.find(regexes=regexes)

    # Examples with Barcelona, Berlin, Brussels should match
    assert len(Dfiltered) == 3
    assert len(Dfiltered_memmap) == 3
    assert Dfiltered_memmap == Dfiltered


def test_multiple_regex(list_doc_examples, tmpdir):
    regexes = {'city': r'B.*', 'phone': 'Non'}
    D = DocumentArray(list_doc_examples)
    Dmemmap = DocumentArrayMemmap(tmpdir)
    Dmemmap.extend(list_doc_examples)

    Dfiltered = D.find(regexes=regexes, traversal_paths=['r'], operator='all')
    Dfiltered_memmap = Dmemmap.find(regexes=regexes)

    # Examples with Barcelona, Brussesls should match
    assert len(Dfiltered) == 2
    assert len(Dfiltered_memmap) == 2
    assert Dfiltered_memmap == Dfiltered
