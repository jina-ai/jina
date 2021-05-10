import os
import pickle

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
def documents_to_train():
    """The relevance is correlated to the size feature."""
    queries = []
    for q in range(1, 100):
        query = Document()
        for i in range(1, 50):
            match = Document()
            # large size higher relevance
            match.tags['price'] = 1
            match.tags['size'] = i * 2
            match.tags['relevance'] = i
            query.matches.add(match)
        queries.append(query)
    return DocumentSet(queries)


@pytest.fixture
def doc_to_query():
    doc = Document()
    for i in range(1, 5):
        match = Document()
        match.tags['price'] = 1
        match.tags['size'] = i * 2
        doc.matches.add(match)
    return doc


def test_train_offline(documents_to_train, doc_to_query):
    def validate_ranking_by_price(req):
        pred = set()
        for match in req.docs[0].matches:
            pred.add(match.score.value)
        assert len(pred) == 1  # since price tag never changes, all scores are the same.

    def validate_ranking_by_size(req):
        pred = []
        for match in req.docs[0].matches:
            pred.append(match.score.value)
        assert (
            sorted(pred) == pred
        )  # assure predictions are ordered since size increases

    # Before Ranker Trainer, the feature is completely rely on `price` tag, `size` can be seen as a bias.

    from sklearn.linear_model import LinearRegression

    model = LinearRegression()

    X = [[1, 1], [2, 1], [4, 1], [8, 1], [16, 1]]
    y = [1, 2, 3, 4, 5]
    model.fit(X, y)
    path = '/Users/bo/Documents/work/jina'
    with open(str(path) + '/model.pickle', mode='wb') as model_file_name:
        pickle.dump(model, model_file_name)

    pred = model.predict([[1, 1], [2, 1], [5, 1], [7, 1]]).tolist()

    with Flow.load_config(os.path.join(cur_dir, 'flow_offline_search.yml')) as f:
        f.search(inputs=[doc_to_query], on_done=validate_ranking_by_price)

    # Run Ranker Trainer

    with Flow.load_config(os.path.join(cur_dir, 'flow_offline_train.yml')) as f:
        f.train(inputs=documents_to_train)

    # After Ranker Trainer, the feature should be completely rely on `size` tag.

    with Flow.load_config(os.path.join(cur_dir, 'flow_offline_search.yml')) as f:
        f.search(inputs=[doc_to_query], on_done=validate_ranking_by_size)
