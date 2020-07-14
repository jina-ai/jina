import numpy as np

from tests import JinaTestCase


class RankerTestCase(JinaTestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ranker = None

    def create_data(self):
        query_chunk2match_chunk = {
            100: [
                {'doc_id': 1, 'chunk_id': 10, 'score': 0.4, 'length': 200},
            ],
            110: [
                {'doc_id': 1, 'chunk_id': 10, 'score': 0.3, 'length': 200},
                {'doc_id': 1, 'chunk_id': 11, 'score': 0.2, 'length': 200},
                {'doc_id': 4294967294, 'chunk_id': 20, 'score': 0.1, 'length': 300},
            ]
        }
        query_chunk_meta = {}
        match_chunk_meta = {}
        match_idx = []
        num_query_chunks = len(query_chunk2match_chunk)
        for query_chunk_id, match_chunks in query_chunk2match_chunk.items():
            query_chunk_meta[query_chunk_id] = {'length': num_query_chunks}
            for c in match_chunks:
                match_chunk_meta[c['chunk_id']] = {'length': c['length']}
                match_idx.append([
                    c['doc_id'],
                    c['chunk_id'],
                    query_chunk_id,
                    c['score'],
                ])
        return np.array(match_idx), query_chunk_meta, match_chunk_meta

    def test_ranker(self):
        if self.ranker is None:
            return
        match_idx, query_chunk_meta, match_chunk_meta = self.create_data()
        doc_idx = self.ranker.score(np.array(match_idx), query_chunk_meta, match_chunk_meta)
        # check the matched docs are in descending order of the scores
        # check the matched docs are in descending order of the scores
        self.assertGreater(doc_idx[0][1], doc_idx[1][1])
        self.assertEqual(doc_idx[0][0], 1)
        self.assertEqual(doc_idx[1][0], 4294967294)
        # check the number of matched docs
        self.assertEqual(len(doc_idx), 2)
