import os

import pytest

from jina import Document, Flow
from jina.types.sets import DocumentSet

'''
User -> Train request -> RankTrainer Train -> RankTrainer Dump Weights/Parameters -> To be loaded in Ranker
price is random and size is related to relevance to see after training, relevance is sorted based on size
2 flows one train and one rank
'''

cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture
def documents():
    queries = []
    for q in range(1, 5):
        query = Document()
        for i in range(1, 5):
            match = Document()
            # large size higher relevance
            match.tags['price'] = q
            match.tags['size'] = i * 10
            match.tags['relevance'] = i
            query.matches.add(match)
        queries.append(query)
    return DocumentSet(queries)


def test_train_offline(documents):
    with Flow.load_config(os.path.join(cur_dir, 'flow_offline_train.yml')) as f:
        f.train(inputs=documents)
