import itertools
import types

import numpy as np
import pytest

from docarray import Document, DocumentArray, DocumentArrayMemmap
from docarray.proto.docarray_pb2 import DocumentArrayProto
from tests import random_docs

# some random prime number for sanity check
num_docs = 7
num_chunks_per_doc = 11
num_matches_per_doc = 3
num_matches_per_chunk = 5


@pytest.fixture
def doc_req():
    """Build a dummy request that has docs"""
    ds = list(random_docs(num_docs, num_chunks_per_doc))
    # add some random matches
    for d in ds:
        for _ in range(num_matches_per_doc):
            d.matches.append(Document(content='hello'))
        for c in d.chunks:
            for _ in range(num_matches_per_chunk):
                c.matches.append(Document(content='world'))
    yield DocumentArray(ds)


@pytest.mark.parametrize('filter_fn', [(lambda d: True), None])
def test_traverse_type(doc_req, filter_fn):
    ds = doc_req.traverse('r', filter_fn=filter_fn)
    assert isinstance(ds, types.GeneratorType)
    assert isinstance(list(ds)[0], DocumentArray)


@pytest.mark.parametrize('filter_fn', [(lambda d: True), None])
def test_traverse_root(doc_req, filter_fn):
    ds = list(doc_req.traverse('r', filter_fn=filter_fn))
    assert len(ds) == 1
    assert len(ds[0]) == num_docs


@pytest.mark.parametrize('filter_fn', [(lambda d: True), None])
def test_traverse_chunk(doc_req, filter_fn):
    ds = list(doc_req.traverse('c', filter_fn=filter_fn))
    assert len(ds) == num_docs
    assert len(ds[0]) == num_chunks_per_doc


@pytest.mark.parametrize('filter_fn', [(lambda d: True), None])
def test_traverse_root_plus_chunk(doc_req, filter_fn):
    ds = list(doc_req.traverse('c,r', filter_fn=filter_fn))
    assert len(ds) == num_docs + 1
    assert len(ds[0]) == num_chunks_per_doc
    assert len(ds[-1]) == num_docs


@pytest.mark.parametrize('filter_fn', [(lambda d: True), None])
def test_traverse_chunk_plus_root(doc_req, filter_fn):
    ds = list(doc_req.traverse('r,c', filter_fn=filter_fn))
    assert len(ds) == 1 + num_docs
    assert len(ds[-1]) == num_chunks_per_doc
    assert len(ds[0]) == num_docs


@pytest.mark.parametrize('filter_fn', [(lambda d: True), None])
def test_traverse_match(doc_req, filter_fn):
    ds = list(doc_req.traverse('m', filter_fn=filter_fn))
    assert len(ds) == num_docs
    assert len(ds[0]) == num_matches_per_doc


@pytest.mark.parametrize('filter_fn', [(lambda d: True), None])
def test_traverse_match_chunk(doc_req, filter_fn):
    ds = list(doc_req.traverse('cm', filter_fn=filter_fn))
    assert len(ds) == num_docs * num_chunks_per_doc
    assert len(ds[0]) == num_matches_per_chunk


@pytest.mark.parametrize('filter_fn', [(lambda d: True), None])
def test_traverse_root_match_chunk(doc_req, filter_fn):
    ds = list(doc_req.traverse('r,c,m,cm', filter_fn=filter_fn))
    assert len(ds) == 1 + num_docs + num_docs + num_docs * num_chunks_per_doc


@pytest.mark.parametrize('filter_fn', [(lambda d: True), None])
def test_traverse_flatten_embedding(doc_req, filter_fn):
    flattened_results = doc_req.traverse_flat('r,c', filter_fn=filter_fn)
    ds = np.stack(flattened_results.get_attributes('embedding'))
    assert ds.shape == (num_docs + num_chunks_per_doc * num_docs, 10)


@pytest.mark.parametrize('filter_fn', [(lambda d: True), None])
def test_traverse_flatten_root(doc_req, filter_fn):
    ds = list(doc_req.traverse_flat('r', filter_fn=filter_fn))
    assert len(ds) == num_docs


@pytest.mark.parametrize('filter_fn', [(lambda d: True), None])
def test_traverse_flatten_chunk(doc_req, filter_fn):
    ds = list(doc_req.traverse_flat('c', filter_fn=filter_fn))
    assert len(ds) == num_docs * num_chunks_per_doc


@pytest.mark.parametrize('filter_fn', [(lambda d: True), None])
def test_traverse_flatten_root_plus_chunk(doc_req, filter_fn):
    ds = list(doc_req.traverse_flat(['c', 'r'], filter_fn=filter_fn))
    assert len(ds) == num_docs + num_docs * num_chunks_per_doc


@pytest.mark.parametrize('filter_fn', [(lambda d: True), None])
def test_traverse_flatten_match(doc_req, filter_fn):
    ds = list(doc_req.traverse_flat(['m'], filter_fn=filter_fn))
    assert len(ds) == num_docs * num_matches_per_doc


@pytest.mark.parametrize('filter_fn', [(lambda d: True), None])
def test_traverse_flatten_match_chunk(doc_req, filter_fn):
    ds = list(doc_req.traverse_flat(['cm'], filter_fn=filter_fn))
    assert len(ds) == num_docs * num_chunks_per_doc * num_matches_per_chunk


@pytest.mark.parametrize('filter_fn', [(lambda d: True), None])
def test_traverse_flatten_root_match_chunk(doc_req, filter_fn):
    ds = list(doc_req.traverse_flat(['r', 'c', 'm', 'cm'], filter_fn=filter_fn))
    assert (
        len(ds)
        == num_docs
        + num_chunks_per_doc * num_docs
        + num_matches_per_doc * num_docs
        + num_docs * num_chunks_per_doc * num_matches_per_chunk
    )


@pytest.mark.parametrize('filter_fn', [(lambda d: True), None])
def test_traverse_flattened_per_path_embedding(doc_req, filter_fn):
    flattened_results = list(
        doc_req.traverse_flat_per_path(['r', 'c'], filter_fn=filter_fn)
    )
    ds = np.stack(flattened_results[0].get_attributes('embedding'))
    assert ds.shape == (num_docs, 10)

    ds = np.stack(flattened_results[1].get_attributes('embedding'))
    assert ds.shape == (num_docs * num_chunks_per_doc, 10)


@pytest.mark.parametrize('filter_fn', [(lambda d: True), None])
def test_traverse_flattened_per_path_root(doc_req, filter_fn):
    ds = list(doc_req.traverse_flat_per_path('r', filter_fn=filter_fn))
    assert len(ds[0]) == num_docs


@pytest.mark.parametrize('filter_fn', [(lambda d: True), None])
def test_traverse_flattened_per_path_chunk(doc_req, filter_fn):
    ds = list(doc_req.traverse_flat_per_path('c', filter_fn=filter_fn))
    assert len(ds[0]) == num_docs * num_chunks_per_doc


@pytest.mark.parametrize('filter_fn', [(lambda d: True), None])
def test_traverse_flattened_per_path_root_plus_chunk(doc_req, filter_fn):
    ds = list(doc_req.traverse_flat_per_path('c,r', filter_fn=filter_fn))
    assert len(ds[0]) == num_docs * num_chunks_per_doc
    assert len(ds[1]) == num_docs


@pytest.mark.parametrize('filter_fn', [(lambda d: True), None])
def test_traverse_flattened_per_path_match(doc_req, filter_fn):
    ds = list(doc_req.traverse_flat_per_path('m', filter_fn=filter_fn))
    assert len(ds[0]) == num_docs * num_matches_per_doc


@pytest.mark.parametrize('filter_fn', [(lambda d: True), None])
def test_traverse_flattened_per_path_match_chunk(doc_req, filter_fn):
    ds = list(doc_req.traverse_flat_per_path('cm', filter_fn=filter_fn))
    assert len(ds[0]) == num_docs * num_chunks_per_doc * num_matches_per_chunk


@pytest.mark.parametrize('filter_fn', [(lambda d: True), None])
def test_traverse_flattened_per_path_root_match_chunk(doc_req, filter_fn):
    ds = list(doc_req.traverse_flat_per_path('r,c,m,cm', filter_fn=filter_fn))
    assert len(ds[0]) == num_docs
    assert len(ds[1]) == num_chunks_per_doc * num_docs
    assert len(ds[2]) == num_matches_per_doc * num_docs
    assert len(ds[3]) == num_docs * num_chunks_per_doc * num_matches_per_chunk


@pytest.mark.parametrize('filter_fn', [(lambda d: True), None])
def test_docuset_traverse_over_iterator_HACKY(filter_fn):
    # HACKY USAGE DO NOT RECOMMEND: can also traverse over "runtime"-documentarray
    ds = DocumentArray(random_docs(num_docs, num_chunks_per_doc)).traverse(
        'r', filter_fn=filter_fn
    )
    assert len(list(list(ds)[0])) == num_docs

    ds = DocumentArray(random_docs(num_docs, num_chunks_per_doc)).traverse(
        'c', filter_fn=filter_fn
    )
    ds = list(ds)
    assert len(ds) == num_docs
    assert len(ds[0]) == num_chunks_per_doc


@pytest.mark.parametrize('filter_fn', [(lambda d: True), None])
def test_docuset_traverse_over_iterator_CAVEAT(filter_fn):
    # HACKY USAGE's CAVEAT: but it can not iterate over an iterator twice
    ds = DocumentArray(random_docs(num_docs, num_chunks_per_doc)).traverse(
        'r,c', filter_fn=filter_fn
    )
    # note that random_docs is a generator and can be only used once,
    # therefore whoever comes first wil get iterated, and then it becomes empty
    assert len(list(ds)) == 1 + num_docs

    ds = DocumentArray(random_docs(num_docs, num_chunks_per_doc)).traverse(
        'c,r', filter_fn=filter_fn
    )
    assert len(list(ds)) == num_docs + 1


@pytest.mark.parametrize('filter_fn', [(lambda d: True), None])
def test_doc_iter_method(filter_fn):
    ds = list(random_docs(10))

    for d in DocumentArray(ds):
        assert d.text == 'hello world'

    for d in DocumentArray(ds).traverse_flat('c,r', filter_fn=filter_fn):
        d.text = 'modified'

    for d in DocumentArray(ds):
        assert d.text == 'modified'


@pytest.mark.parametrize('filter_fn', [(lambda d: True), None])
def test_traverse_matcharray(filter_fn):
    doc = Document(
        matches=[
            Document(id=f'm{i}', chunks=[Document(id=f'm{i}c{j}') for j in range(3)])
            for i in range(3)
        ]
    )
    flat_docs = doc.matches.traverse_flat('r,c', filter_fn=filter_fn)
    assert isinstance(flat_docs, DocumentArray)
    assert len(flat_docs) == 12


@pytest.mark.parametrize('filter_fn', [(lambda d: True), None])
def test_traverse_chunkarray(filter_fn):
    doc = Document(
        chunks=[
            Document(id=f'c{i}', matches=[Document(id=f'c{i}m{j}') for j in range(3)])
            for i in range(3)
        ]
    )
    flat_docs = doc.chunks.traverse_flat('r,m', filter_fn=filter_fn)
    assert isinstance(flat_docs, DocumentArray)
    assert len(flat_docs) == 12


@pytest.mark.parametrize('use_dam', [True, False])
@pytest.mark.parametrize(
    ('filter_fn', 'docs_len'),
    [
        (lambda d: False, 0),
        (lambda d: d.text == 'hello', num_docs * num_matches_per_doc),
        (
            lambda d: d.text == 'world',
            num_docs * num_chunks_per_doc * num_matches_per_chunk,
        ),
        (
            lambda d: True,
            num_docs
            + num_docs * num_chunks_per_doc
            + num_docs * num_matches_per_doc
            + num_docs * num_chunks_per_doc * num_matches_per_chunk,
        ),
        (
            None,
            num_docs
            + num_docs * num_matches_per_doc
            + num_docs * num_chunks_per_doc
            + num_docs * num_chunks_per_doc * num_matches_per_chunk,
        ),
    ],
)
def test_filter_fn_traverse_flat(filter_fn, docs_len, doc_req, use_dam, tmp_path):
    if use_dam:
        docs = DocumentArrayMemmap(tmp_path)
        docs.extend(doc_req)
    else:
        docs = doc_req
    ds = list(docs.traverse_flat('r,c,m,cm', filter_fn=filter_fn))
    assert len(ds) == docs_len
    assert all(isinstance(d, Document) for d in ds)


@pytest.mark.parametrize('use_dam', [True, False])
@pytest.mark.parametrize(
    ('filter_fn', 'docs_len'),
    [
        (lambda d: False, [0, 0, 0, 0]),
        (lambda d: d.text == 'hello', [0, 0, num_docs * num_matches_per_doc, 0]),
        (
            lambda d: d.text == 'world',
            [0, 0, 0, num_docs * num_chunks_per_doc * num_matches_per_chunk],
        ),
        (
            lambda d: True,
            [
                num_docs,
                num_docs * num_chunks_per_doc,
                num_docs * num_matches_per_doc,
                num_docs * num_chunks_per_doc * num_matches_per_chunk,
            ],
        ),
        (
            None,
            [
                num_docs,
                num_docs * num_chunks_per_doc,
                num_docs * num_matches_per_doc,
                num_docs * num_chunks_per_doc * num_matches_per_chunk,
            ],
        ),
    ],
)
def test_filter_fn_traverse_flat_per_path(
    filter_fn, doc_req, docs_len, use_dam, tmp_path
):
    if use_dam:
        docs = DocumentArrayMemmap(tmp_path)
        docs.extend(doc_req)
    else:
        docs = doc_req
    ds = list(docs.traverse_flat_per_path('r,c,m,cm', filter_fn=filter_fn))
    assert len(ds) == 4
    for seq, length in zip(ds, docs_len):
        assert isinstance(seq, DocumentArray if not use_dam else itertools.chain)
        assert len(list(seq)) == length


def test_traversal_path():
    da = DocumentArray([Document() for _ in range(6)])
    assert len(da) == 6

    da.traverse_flat('r')

    with pytest.warns(DeprecationWarning):
        da.traverse_flat(['r'])

    da.traverse('r')
    with pytest.warns(DeprecationWarning):
        for _ in da.traverse(['r']):
            pass

    da.traverse('r')
    with pytest.warns(DeprecationWarning):
        for _ in da.traverse(['r']):
            pass


def test_traverse_flat_root_itself():
    da = DocumentArray([Document() for _ in range(100)])
    res = da.traverse_flat('r')
    assert id(res) == id(da)


def da_and_dam(N):
    da = DocumentArray(random_docs(N))
    dam = DocumentArrayMemmap()
    dam.extend(da)
    return da, dam


@pytest.mark.parametrize('da', da_and_dam(100))
def test_flatten(da):
    daf = da.flatten()
    assert len(daf) == 600
    assert isinstance(daf, DocumentArray)
    assert len(set(d.id for d in daf)) == 600

    # flattened DA can not be flattened again
    daf = daf.flatten()
    assert len(daf) == 600


def test_flatten_no_copy():
    da = da_and_dam(100)[0]
    daf = da.flatten(copy=False)
    new_text = 'hi i changed it!'
    daf[53].text = new_text
    assert da[daf[53].id].text == new_text
