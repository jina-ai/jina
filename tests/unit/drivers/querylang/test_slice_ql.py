from jina.drivers.querylang.slice import SliceQL
from jina.proto import jina_pb2


def random_docs_with_chunks(num_docs):
    docs = []
    for j in range(num_docs):
        d = jina_pb2.Document()
        d.granularity = 0
        d.tags['id'] = j
        d.text = 'hello world'
        d.uri = 'doc://'
        for c in range(10):
            dc = d.chunks.add()
            dc.text = 'chunk to hello world'
            dc.granularity = 1
            dc.uri = 'doc://chunk'
            dc.tags['id'] = c
            for cc in range(10):
                dcc = dc.chunks.add()
                dcc.text = 'nested chunk to chunk'
                dcc.uri = 'doc://chunk/chunk'
                dcc.tags['id'] = cc
                dcc.granularity = 2
        docs.append(d)
    return docs


def random_docs_with_chunks_and_matches(num_docs):
    # doc |- chunk |- chunk
    #     |        |- chunk
    #     |        |- match | - chunk
    #                       | - chunk
    #     |        |- match
    #     |- chunk
    #     |- chunk
    #     |- match | - chunk
    #              | - chunk
    docs = []
    for j in range(num_docs):
        d = jina_pb2.Document()
        d.granularity = 0
        d.tags['id'] = j
        d.text = 'hello world'
        d.uri = 'doc://'
        for c in range(10):
            dc = d.chunks.add()
            dc.text = 'chunk to hello world'
            dc.granularity = d.granularity + 1
            dc.uri = 'doc://chunk'
            dc.tags['id'] = c
            for cc in range(10):
                dcc = dc.chunks.add()
                dcc.text = 'nested chunk to chunk'
                dcc.uri = 'doc://chunk/chunk'
                dcc.tags['id'] = cc
                dcc.granularity = dc.granularity + 1
            for m in range(10):
                cm = dc.matches.add()
                cm.text = 'match to chunk to hello-world'
                cm.uri = 'doc://chunk/match'
                cm.tags['id'] = m
                cm.granularity = dc.granularity
                for mc in range(10):
                    cmc = cm.chunks.add()
                    cmc.text = 'chunk to match to chunk to hello-world'
                    cmc.uri = 'doc://chunk/match/chunk'
                    cmc.tags['id'] = mc
                    cmc.granularity = cm.granularity + 1
        for m in range(10):
            dm = d.matches.add()
            dm.text = 'match to hello-world'
            dm.uri = 'doc://match'
            dm.tags['id'] = m
            dm.granularity = d.granularity
            for c in range(10):
                dmc = dm.chunks.add()
                dmc.text = 'chunk to match to hello-world'
                dmc.uri = 'doc://match/chunk'
                dmc.tags['id'] = m
                dmc.granularity = dm.granularity + 1

        docs.append(d)
    return docs


def test_slice_ql_on_chunks():
    docs = random_docs_with_chunks(10)
    driver = SliceQL(start=0, end=2, traversal_paths=('cc', 'c', 'r'))
    driver._traverse_apply(docs)
    assert len(docs) == 2
    assert len(docs[0].chunks) == 2  # slice on level 1
    assert len(docs[0].chunks[0].chunks) == 2  # slice on level 2 for chunks
    assert len(docs[0].chunks[-1].chunks) == 2  # slice on level 2 for chunks
    assert len(docs[-1].chunks) == 2  # slice on level 1
    assert len(docs[-1].chunks[0].chunks) == 2  # slice on level 2 for chunks
    assert len(docs[-1].chunks[-1].chunks) == 2  # slice on level 2 for chunks


def test_slice_ql_on_matches_and_chunks():
    docs = random_docs_with_chunks_and_matches(10)
    driver = SliceQL(start=0, end=2, traversal_paths=('cc', 'c', 'r', 'mm', 'm'))
    assert len(docs) == 10
    assert len(docs[0].chunks) == 10
    assert len(docs[-1].chunks) == 10
    assert len(docs[0].matches) == 10
    assert len(docs[-1].matches) == 10
    assert len(docs[0].matches[0].chunks) == 10
    assert len(docs[0].matches[-1].chunks) == 10
    assert len(docs[-1].matches[0].chunks) == 10
    assert len(docs[-1].matches[-1].chunks) == 10
    assert len(docs[0].chunks[0].chunks) == 10
    assert len(docs[0].chunks[0].matches) == 10
    assert len(docs[0].chunks[0].matches[0].chunks) == 10
    assert len(docs[0].chunks[0].matches[-1].chunks) == 10
    assert len(docs[0].chunks[-1].matches[0].chunks) == 10
    assert len(docs[0].chunks[-1].matches[-1].chunks) == 10
    assert len(docs[0].chunks[-1].chunks) == 10
    assert len(docs[0].chunks[-1].matches) == 10
    assert len(docs[-1].chunks[0].chunks) == 10
    assert len(docs[-1].chunks[0].matches) == 10
    assert len(docs[-1].chunks[-1].chunks) == 10
    assert len(docs[-1].chunks[-1].matches) == 10
    driver._traverse_apply(docs)
    assert len(docs) == 2

    assert len(docs[0].chunks) == 2  # slice on level 1
    assert len(docs[0].matches) == 2  # slice on level 1

    assert len(docs[0].chunks[0].chunks) == 2  # slice on level 2 for chunks
    assert len(docs[0].chunks[-1].chunks) == 2  # slice on level 2 for chunks

    assert len(docs[0].chunks[0].matches) == 10  # traverses directly on matches
    assert len(docs[0].chunks[0].matches[0].chunks) == 10
    assert len(docs[0].chunks[0].matches[-1].chunks) == 10
    assert len(docs[0].chunks[-1].matches) == 10  # traverses directly on matches
    assert len(docs[0].chunks[-1].matches[0].chunks) == 10
    assert len(docs[0].chunks[-1].matches[-1].chunks) == 10

    assert len(docs[0].matches[0].chunks) == 10
    assert len(docs[0].matches[-1].chunks) == 10

    assert len(docs[-1].chunks) == 2  # slice on level 1 of chunks
    assert len(docs[-1].matches) == 2  # slice on level 1 of chunks

    assert len(docs[-1].chunks[0].chunks) == 2  # slice on level 2 for matches of chunks
    assert len(docs[-1].chunks[-1].chunks) == 2  # slice on level 2 for matches of chunks

    assert len(docs[-1].chunks[0].matches) == 10  # traverses directly on matches
    assert len(docs[-1].chunks[0].matches[0].chunks) == 10
    assert len(docs[-1].chunks[0].matches[-1].chunks) == 10
    assert len(docs[-1].chunks[-1].matches) == 10  # traverses directly on matches
    assert len(docs[-1].chunks[-1].matches[0].chunks) == 10
    assert len(docs[-1].chunks[-1].matches[-1].chunks) == 10

    assert len(docs[-1].matches[0].chunks) == 10
    assert len(docs[-1].matches[-1].chunks) == 10
