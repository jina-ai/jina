from copy import deepcopy

import numpy as np

from docarray import DocumentArray, Document


def test_reduce_doc():
    doc1 = Document(
        text='doc1',
        matches=[Document(id='m0'), Document(id='m2')],
        chunks=[Document(id='c0'), Document(id='c1')],
    )

    doc2 = Document(
        text='doc2',
        embedding=np.zeros(3),
        matches=[Document(id='m0'), Document(id='m1')],
        chunks=[Document(id='c0'), Document(id='c2')],
    )

    DocumentArray._reduce_doc(doc1, doc2)

    assert doc1.text == 'doc1'
    assert (doc1.embedding == np.zeros(3)).all()
    for i in range(3):
        assert f'c{i}' in doc1.chunks
        assert f'm{i}' in doc1.matches


def test_reduce():
    da1, da2 = (
        DocumentArray(
            [
                Document(
                    id='r0',
                    text='da1',
                    matches=[
                        Document(id='r0m0'),
                        Document(id='r0m2'),
                        Document(id='r0m1'),
                    ],
                ),
                Document(
                    id='r2',
                    text='da1',
                    matches=[
                        Document(id='r2m0'),
                        Document(id='r2m2'),
                        Document(id='r2m1'),
                    ],
                ),
            ]
        ),
        DocumentArray(
            [
                Document(
                    id='r0',
                    text='da2',
                    matches=[
                        Document(id='r0m0'),
                        Document(id='r0m1'),
                        Document(id='r0m3'),
                    ],
                ),
                Document(
                    id='r1',
                    text='da2',
                    matches=[
                        Document(id='r1m0'),
                        Document(id='r1m1'),
                        Document(id='r1m2'),
                        Document(id='r1m3'),
                    ],
                ),
                Document(
                    id='r2',
                    text='da2',
                    matches=[
                        Document(id='r2m3'),
                    ],
                ),
            ]
        ),
    )

    da1.reduce(da2)

    for i in range(3):
        assert f'r{i}' in da1
        for j in range(4):
            assert f'r{i}m{j}' in da1[f'r{i}'].matches

    assert da1['r0'].text == 'da1'
    assert da1['r1'].text == 'da2'
    assert da1['r2'].text == 'da1'


def test_reduce_nested():
    da1, da2 = (
        DocumentArray(
            [
                Document(
                    id='r1',
                    chunks=[
                        Document(
                            id='c1',
                            chunks=[Document(id='c1c2')],
                            matches=[Document(id='c1m2')],
                        ),
                    ],
                    matches=[
                        Document(
                            id='m1', chunks=[Document(id='m1c1'), Document(id='m1c2')]
                        ),
                        Document(id='m2'),
                    ],
                ),
            ]
        ),
        DocumentArray(
            [
                Document(
                    id='r1',
                    chunks=[
                        Document(
                            id='c1',
                            chunks=[Document(id='c1c1')],
                            matches=[Document(id='c1m1')],
                        ),
                        Document(
                            id='c2',
                            chunks=[Document(id='c2c1'), Document(id='c2c2')],
                            matches=[Document(id='c2m1'), Document(id='c2m2')],
                        ),
                    ],
                    matches=[
                        Document(
                            id='m1', matches=[Document(id='m1m1'), Document(id='m1m2')]
                        ),
                        Document(
                            id='m2',
                            chunks=[Document(id='m2c1'), Document(id='m2c2')],
                            matches=[Document(id='m2m1'), Document(id='m2m2')],
                        ),
                    ],
                ),
            ]
        ),
    )

    da1.reduce(da2)
    for i in range(1, 3):
        assert f'c{i}' in da1[0].chunks
        assert f'm{i}' in da1[0].matches
        for j in range(1, 3):
            assert f'c{i}c{j}' in da1[0].chunks[f'c{i}'].chunks
            assert f'c{i}m{j}' in da1[0].chunks[f'c{i}'].matches

            assert f'm{i}c{j}' in da1[0].matches[f'm{i}'].chunks
            assert f'm{i}m{j}' in da1[0].matches[f'm{i}'].matches


def test_reduce_mat():
    docs = DocumentArray([Document(id=f'r{i}') for i in range(10)])
    doc_matrix = [deepcopy(docs) for _ in range(10)]
    for i, da in enumerate(doc_matrix):
        for doc in da:
            doc.matches.append(Document(id=str(i)))

    reduced_da = doc_matrix[0].reduce_all(doc_matrix[1:])
    for doc in reduced_da:
        for i in range(10):
            assert str(i) in doc.matches


def test_reduce_data_props():
    da1, da2, da3 = (
        DocumentArray([Document(id='r', text='doc1', chunks=[Document(id='c1')])]),
        DocumentArray(
            [
                Document(
                    id='r',
                    text='doc2',
                    embedding=np.zeros(3),
                    chunks=[Document(id='c2')],
                )
            ]
        ),
        DocumentArray(
            [
                Document(
                    id='r',
                    text='doc3',
                    tags={'a': 'b'},
                    matches=[Document(id='m3')],
                )
            ]
        ),
    )
    da1.reduce_all([da2, da3])
    assert da1[0].text == 'doc1'
    assert da1[0].id == 'r'

    # chunks and matches merged, not overridden
    assert da1[0].chunks[0].id == 'c1'
    assert da1[0].chunks[1].id == 'c2'
    assert da1[0].matches[0].id == 'm3'
    assert da1[0].tags == {'a': 'b'}
