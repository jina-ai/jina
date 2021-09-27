# test the batching module
from typing import Any, List

import numpy as np
import pytest
from jina import DocumentArray, Document
from pytest_lazyfixture import lazy_fixture

NUM_DOCS = 15


@pytest.fixture()
def doc_array() -> DocumentArray:
    return DocumentArray([Document(text='test') for _ in range(NUM_DOCS)])


@pytest.fixture()
def docs_root(doc_array: DocumentArray) -> DocumentArray:
    return doc_array


@pytest.fixture()
def docs_chunk(doc_array: DocumentArray) -> DocumentArray:
    return DocumentArray([Document(chunks=doc_array)])


@pytest.fixture()
def docs_chunk_chunk(doc_array) -> DocumentArray:
    return DocumentArray([Document(chunks=[Document(chunks=doc_array)])])


@pytest.mark.parametrize(
    ['docs', 'batch_size', 'filter_attr', 'expected_sizes', 'traversal_path'],
    [
        (lazy_fixture('docs_root'), 10, 'text', [10, 5], ['r']),
        (lazy_fixture('docs_root'), 20, 'text', [15], ['r']),
        (lazy_fixture('docs_root'), 5, 'text', [5, 5, 5], ['r']),
        (lazy_fixture('docs_root'), 5, 'text', [-1], ['c']),
        (lazy_fixture('docs_root'), 5, 'blob', [-1], ['r']),
        (lazy_fixture('docs_chunk'), 10, 'text', [10, 5], ['c']),
        (lazy_fixture('docs_chunk'), 20, 'text', [15], ['c']),
        (lazy_fixture('docs_chunk'), 5, 'text', [5, 5, 5], ['c']),
        (lazy_fixture('docs_chunk'), 5, 'text', [1], ['r']),
        (lazy_fixture('docs_chunk'), 5, 'blob', [-1], ['c']),
        (lazy_fixture('docs_chunk_chunk'), 10, 'text', [10, 5], ['cc']),
        (lazy_fixture('docs_chunk_chunk'), 20, 'text', [15], ['cc']),
        (lazy_fixture('docs_chunk_chunk'), 5, 'text', [5, 5, 5], ['cc']),
        (lazy_fixture('docs_chunk_chunk'), 5, 'text', [1], ['c']),
        (lazy_fixture('docs_chunk_chunk'), 5, 'blob', [-1], ['cc']),
    ],
)
def test_batching(
    docs: DocumentArray,
    batch_size: int,
    filter_attr: str,
    expected_sizes: List[int],
    traversal_path: List[str],
):
    generator = docs.batch(
        traversal_paths=traversal_path,
        batch_size=batch_size,
        require_attr=filter_attr,
    )
    for batch, expected_size in zip(generator, expected_sizes):
        assert (
            len(batch) == expected_size
        ), f'Expected size {expected_size} but got {len(batch)}'


@pytest.mark.parametrize(
    ['attr_name', 'attr_value'],
    [
        ('text', 'text'),
        ('buffer', b'text'),
        ('blob', np.array([1])),
        ('blob', np.array([1, 2])),
        ('uri', 'https://uri'),
        ('content', 'text'),
        ('embedding', np.array([1])),
        ('embedding', np.array([1, 2])),
    ],
)
def test_needs_attr_empty(attr_name: str, attr_value: Any):
    """
    Test that filtering by attribute works properly for empty documents
    """

    docs = DocumentArray([Document(), Document()])
    setattr(docs[1], attr_name, attr_value)
    generator = docs.batch(batch_size=1, require_attr=attr_name)
    filtered_docs = list(generator)

    assert len(filtered_docs) == 1 and len(filtered_docs[0]) == 1

    if attr_name in ['blob', 'embedding']:
        np.testing.assert_array_equal(
            getattr(filtered_docs[0][0], attr_name), attr_value
        )
    else:
        assert getattr(filtered_docs[0][0], attr_name) == attr_value
