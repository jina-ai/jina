import unittest
import numpy as np

from jina.executors.rankers.bi_match import BiMatchRanker
from tests import JinaTestCase


class MyTestCase(JinaTestCase):
    def test_single_query(self):
        query_chunk2match_chunk = {
            100: [
                {'doc_id': 1, 'chunk_id': 10, 'score': 0.4, 'length': 200},
            ],
            110: [
                {'doc_id': 1, 'chunk_id': 10, 'score': 0.3, 'length': 300},
                {'doc_id': 1, 'chunk_id': 11, 'score': 0.2, 'length': 300},
                {'doc_id': 2, 'chunk_id': 20, 'score': 0.1, 'length': 300},
            ]
        }
        query_chunk_meta = {}
        match_chunk_meta = {}
        match_idx = []
        for query_chunk_id in (100, 110):
            query_chunk_meta[query_chunk_id] = {'length': 2}
            for match_chunk in query_chunk2match_chunk[query_chunk_id]:
                match_chunk_meta[match_chunk['chunk_id']] = {'length': match_chunk['length']}
                match_idx.append([
                    match_chunk['doc_id'],
                    match_chunk['chunk_id'],
                    query_chunk_id,
                    match_chunk['score'],
                ])
        ranker = BiMatchRanker()
        doc_idx = ranker.score(np.array(match_idx), query_chunk_meta, match_chunk_meta)
        # check the matched docs are in descending order of the scores
        self.assertGreater(doc_idx[0][1], doc_idx[1][1])
        self.assertEqual(doc_idx[0][0], 1)
        self.assertEqual(doc_idx[1][0], 2)
        # check the number of matched docs
        self.assertEqual(len(doc_idx), 2)


if __name__ == '__main__':
    unittest.main()
