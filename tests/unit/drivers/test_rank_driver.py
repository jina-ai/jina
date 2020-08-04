from tests import JinaTestCase
from jina.drivers.rank import Chunk2DocRankDriver
from jina.proto import jina_pb2
from jina.executors.rankers import BaseRanker
from jina.peapods.pea import BasePea
from jina.main.parser import set_pea_parser
import numpy as np



def create_document_to_rank():
    # query doc
    # {id: 100, level_depth=0,
    #  chunks=[
    #      {id: 101, level_depth=1},
    #      {id: 102, level_depth=1}]}
    # {id: 101, level_depth=1} matches
    # {id: 11, parent_id: 1, score: 1.0, level_depth=1}
    # {id: 12, parent_id: 1, score: 0.9, level_depth=1}
    # {id: 13, parent_id: 1, score: 0.8, level_depth=1}
    #
    # {id: 102, level_depth=1} matches
    # {id: 21, parent_id: 2, score: 1.0, level_depth=1}
    # {id: 22, parent_id: 2, score: 0.9, level_depth=1}
    # {id: 23, parent_id: 2, score: 0.8, level_depth=1}
    #
    # expected results
    # {id: 100, level_depth=0,
    #  chunks=[
    #      {id: 101, level_depth=1},
    #      {id: 102, level_depth=1}],
    #  matches=[
    #      {id: 1, score=1.0, level_depth=0},
    #      {id: 2, score=1.0, level_depth=0}]}
    doc = jina_pb2.Document()
    doc.id = 100
    doc.level_depth = 0
    for _idx in range(2):
        c_id = _idx + 1
        chunk = doc.chunks.add()
        chunk.id = doc.id + c_id
        chunk.level_depth = 1
        for _idx_2 in range(3):
            m_id = _idx_2 + 1
            match = chunk.matches.add()
            match.score.value = (10 - _idx_2) * 0.1
            match.parent_id = c_id
            match.id = c_id * 10 + m_id
            match.level_depth = 1
    return doc


class MockRanker(BaseRanker):
    required_keys = {}

    def score(self, match_idx, query_chunk_meta, match_chunk_meta):
        # match_idx
        # [[1, 11, 100, 1.0],
        #  [1, 12, 100, 0.9],
        #  [1, 13, 100, 0.8],
        #  [2, 11, 100, 1.0],
        #  [2, 12, 100, 0.9],
        #  [2, 13, 100, 0.8]]
        # take the highest score for each doc
        _cols = [0, -1]
        return np.vstack([match_idx[0, _cols], match_idx[3, _cols]])


def create_message():
    msg = jina_pb2.Message()
    msg.envelope.status.code = jina_pb2.Status.SUCCESS
    return msg


class MockPea(BasePea):
    def __init__(self, args):
        super().__init__(args)
        self._message = jina_pb2.Message()
        self._message.envelope.status.code = jina_pb2.Status.SUCCESS


class Chunk2DocRankDriverTestCase(JinaTestCase):
    def test_chunk2doc_driver_mock_indexer(self):
        doc = create_document_to_rank()
        print(doc)
        driver = Chunk2DocRankDriver()
        executor = MockRanker()
        args = set_pea_parser().parse_args(['--runtime', 'process'])
        pea = MockPea(args)

        driver.attach(executor=executor, pea=pea)
        executor.attach(pea)
        driver._apply_all(doc.chunks, doc)
        self.assertEqual(len(doc.matches), 2)
        for idx, m in enumerate(doc.matches):
            self.assertEqual(m.id, idx + 1)
            self.assertEqual(m.score.value, 1.0)


