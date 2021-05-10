import pickle
from pathlib import Path

import numpy as np

from jina.executors.rankers.trainer import RankerTrainer


class SGDRegressorRankerTrainer(RankerTrainer):
    """The :class:`SGDRegressorRankerTrainer` trains an :class:`SGDRegressor` and save the trained model
    to the expected directory. To be loaded into :class:`SGDRegressorRanker`."""

    MODEL_FILENAME = 'model.pickle'

    def __init__(self, model_path: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = None
        self.model_path = model_path
        self.match_required_keys = {'tags__size', 'tags__price', 'tags__relevance'}
        self.query_required_keys = None

    def post_init(self):
        from sklearn.linear_model import LinearRegression

        self.model = LinearRegression()

    def train(self, query_metas, matches_metas, *args, **kwargs):
        """
        Train the ranker, the core function of trainer.

        This method extract `size` and `price` features from ``Document`` tags,
        serve as the features for model training. And extract `relevance` from ``Document``,
        serve as the labels for model training.
        """
        sizes = []
        prices = []
        relevance = []
        for match_meta in matches_metas:
            for m in match_meta:
                sizes.append(m['tags__size'])
                prices.append(m['tags__price'])
                relevance.append(m['tags__relevance'])
        X = np.column_stack((prices, sizes))
        print(X)
        y = np.asarray(relevance)
        print(y)
        self.model.fit(X, y)

    def save(self):
        """Save the updated the ranker model."""
        path = Path(self.model_path)

        if not path.exists():
            path.mkdir(parents=True)

        with open(str(path) + '/' + self.MODEL_FILENAME, mode='wb') as model_file_name:
            pickle.dump(self.model, model_file_name)
