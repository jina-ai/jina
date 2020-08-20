from jina.drivers.querylang.slice import SliceQL
from jina.proto import jina_pb2
from tests import JinaTestCase


def random_docs_with_matches(num_docs):
    docs = []
    #matches are always in the same level depth as its match
    for j in range(num_docs):
        d = jina_pb2.Document()
        d.level_depth = 0
        d.id = j
        d.text = 'hello world'
        d.uri = 'doc://'
        for m in range(10):
            dm = d.matches.add()
            dm.text = 'match to hello world'
            dm.level_depth = 0
            dm.uri = 'doc://match'
            dm.id = m
            dm.score.ref_id = d.id
            for mm in range(10):
                dmm = dm.matches.add()
                dmm.text = 'nested match to match'
                dmm.uri = 'doc://match/match'
                dmm.id = mm
                dmm.score.ref_id = m
                dmm.level_depth = 0
        docs.append(d)
    return docs


def random_docs_with_chunks(num_docs):
    docs = []
    for j in range(num_docs):
        d = jina_pb2.Document()
        d.level_depth = 0
        d.id = j
        d.text = 'hello world'
        d.uri = 'doc://'
        for c in range(10):
            dc = d.chunks.add()
            dc.text = 'chunk to hello world'
            dc.level_depth = 1
            dc.uri = 'doc://chunk'
            dc.id = c
            for cc in range(10):
                dcc = dc.chunks.add()
                dcc.text = 'nested chunk to chunk'
                dcc.uri = 'doc://chunk/chunk'
                dcc.id = cc
                dcc.level_depth = 2
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
        d.level_depth = 0
        d.id = j
        d.text = 'hello world'
        d.uri = 'doc://'
        for c in range(10):
            dc = d.chunks.add()
            dc.text = 'chunk to hello world'
            dc.level_depth = d.level_depth + 1
            dc.uri = 'doc://chunk'
            dc.id = c
            for cc in range(10):
                dcc = dc.chunks.add()
                dcc.text = 'nested chunk to chunk'
                dcc.uri = 'doc://chunk/chunk'
                dcc.id = cc
                dcc.level_depth = dc.level_depth + 1
            for m in range(10):
                cm = dc.matches.add()
                cm.text = 'match to chunk to hello-world'
                cm.uri = 'doc://chunk/match'
                cm.id = m
                cm.level_depth = dc.level_depth
                cm.score.ref_id = dc.id
                for mc in range(10):
                    cmc = cm.chunks.add()
                    cmc.text = 'chunk to match to chunk to hello-world'
                    cmc.uri = 'doc://chunk/match/chunk'
                    cmc.id = mc
                    cmc.level_depth = cm.level_depth + 1
        for m in range(10):
            dm = d.matches.add()
            dm.text = 'match to hello-world'
            dm.uri = 'doc://match'
            dm.id = m
            dm.level_depth = d.level_depth
            dm.score.ref_id = d.id
            for c in range(10):
                dmc = dm.chunks.add()
                dmc.text = 'chunk to match to hello-world'
                dmc.uri = 'doc://match/chunk'
                dmc.id = m
                dmc.level_depth = dm.level_depth + 1

        docs.append(d)
    return docs


class SliceQLTestCase(JinaTestCase):

    def test_slice_ql_on_matches(self):
        docs = random_docs_with_matches(10)
        driver = SliceQL(start=0, end=2, traverse_on='matches', depth_range=(0, 2))
        driver._traverse_apply(docs)
        assert len(docs) == 10  # traverses directly on matches
        assert len(docs[0].matches) == 2  # slice on level 1
        assert len(docs[0].matches[0].matches) == 2  # slice on level 2 for matches
        assert len(docs[0].matches[-1].matches) == 2  # slice on level 2 for matches
        assert len(docs[-1].matches) == 2  # slice on level 1
        assert len(docs[-1].matches[0].matches) == 2  # slice on level 2 for matches
        assert len(docs[-1].matches[-1].matches) == 2  # slice on level 2 for matches

    def test_slice_ql_on_chunks(self):
        docs = random_docs_with_chunks(10)
        driver = SliceQL(start=0, end=2, traverse_on='chunks', depth_range=(0, 2))
        driver._traverse_apply(docs)
        assert len(docs) == 2
        assert len(docs[0].chunks) == 2  # slice on level 1
        assert len(docs[0].chunks[0].chunks) == 2  # slice on level 2 for chunks
        assert len(docs[0].chunks[-1].chunks) == 2  # slice on level 2 for chunks
        assert len(docs[-1].chunks) == 2  # slice on level 1
        assert len(docs[-1].chunks[0].chunks) == 2  # slice on level 2 for chunks
        assert len(docs[-1].chunks[-1].chunks) == 2  # slice on level 2 for chunks

    def test_slice_ql_on_matches_and_chunks(self):
        docs = random_docs_with_chunks_and_matches(10)
        driver = SliceQL(start=0, end=2, traverse_on=['chunks', 'matches'], depth_range=(0, 2))
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
