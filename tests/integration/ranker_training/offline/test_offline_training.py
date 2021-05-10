import os
import pickle

import pytest

from jina import Document, Flow
from jina.types.sets import DocumentSet

'''
User -> Train request -> RankTrainer Train -> RankTrainer Dump Weights/Parameters/Model ->
Ranker Load Model -> Re-rank
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
    '''
    The objective of this test is to ensure ranker trainer works as expected.
    Our data set consist of 2 features field, `price` and `size`. Label field is named as `relevance`.
    Before using ranker trainer, we manually train a linear model based on `price` field, use a
      Jina search flow to find documents and scores with the `doc_to_query`. Since the `price` of the `doc_to_query`
      has been set to 1, so the pre-trained model will always return the same value and all the scores will be the same.
      so we assert the length of prediction is 1 in `validate_ranking_by_price`.
    Afterwords, we fire a ranker trainer, it will dump a new model. The trainiang set of the new model is based on `size`
      feature, see `docs_to_train`, and the `price` is not going to have any impact on the predictions. When we search the result
      with `doc_to_query`, we expect the relevance score keep increase since the `size` in `doc_to_query` keeps increase.
      see `validate_ranking_by_size`.
    '''
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
            sorted(pred, reverse=True) == pred
        )  # assure predictions are ordered since size increases

    # Before Ranker Trainer, the feature is completely rely on `price` tag, `size` can be seen as a bias.

    from sklearn.linear_model import LinearRegression

    model = LinearRegression()

    X = [[1, 1], [2, 1], [4, 1], [8, 1], [16, 1]]
    y = [1, 2, 3, 4, 5]
    model.fit(X, y)
    with open('model.pickle', mode='wb') as model_file_name:
        pickle.dump(model, model_file_name)

    with Flow.load_config(os.path.join(cur_dir, 'flow_offline_search.yml')) as f:
        f.search(inputs=[doc_to_query], on_done=validate_ranking_by_price)

    # Run Ranker Trainer

    with Flow.load_config(os.path.join(cur_dir, 'flow_offline_train.yml')) as f:
        f.train(inputs=documents_to_train)

    # After Ranker Trainer, the feature should be completely rely on `size` tag.

    with Flow.load_config(os.path.join(cur_dir, 'flow_offline_search.yml')) as f:
        f.search(inputs=[doc_to_query], on_done=validate_ranking_by_size)
