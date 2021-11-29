from jina import DocumentArray, Document
from jina.reducer import merge, merge_doc


def test_merge_doc():
    doc1 = Document(
        matches=[Document(id='m0'), Document(id='m2')],
        chunks=[Document(id='c0'), Document(id='c1')],
    )

    doc2 = Document(
        matches=[Document(id='m0'), Document(id='m1')],
        chunks=[Document(id='c0'), Document(id='c2')],
    )

    merge_doc(doc1, doc2)
    for i in range(3):
        assert f'c{i}' in doc1.chunks
        assert f'm{i}' in doc1.matches


def test_merge():
    da1, da2 = (
        DocumentArray(
            [
                Document(
                    id='r0',
                    matches=[
                        Document(id='r0m0'),
                        Document(id='r0m2'),
                        Document(id='r0m1'),
                    ],
                ),
                Document(
                    id='r2',
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
                    matches=[
                        Document(id='r0m0'),
                        Document(id='r0m1'),
                        Document(id='r0m3'),
                    ],
                ),
                Document(
                    id='r1',
                    matches=[
                        Document(id='r1m0'),
                        Document(id='r1m1'),
                        Document(id='r1m2'),
                        Document(id='r1m3'),
                    ],
                ),
                Document(
                    id='r2',
                    matches=[
                        Document(id='r2m3'),
                    ],
                ),
            ]
        ),
    )

    merge(da1, da2)

    for i in range(3):
        assert f'r{i}' in da1
        for j in range(4):
            assert f'r{i}m{j}' in da1[f'r{i}'].matches
