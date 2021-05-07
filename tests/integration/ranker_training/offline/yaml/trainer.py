import pickle
from pathlib import Path

import numpy as np

from jina.executors.rankers.trainer import RankerTrainer


class SGDRegressorRankerTrainer(RankerTrainer):

    MODEL_FILENAME = 'model.pickle'

    def __init__(self, model_path: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model_path = model_path
        self.match_required_keys = {'tags__size', 'tags__price', 'tags__relevance'}
        self.query_required_keys = None

    def post_init(self):
        from sklearn.linear_model import SGDRegressor

        self.regressor = SGDRegressor(warm_start=True)

    def train(self, query_metas, matches_metas, *args, **kwargs):
        sizes = []
        prices = []
        relevance = []
        for match_meta in matches_metas:
            for m in match_meta:
                sizes.append(m['tags__size'])
                prices.append(m['tags__price'])
                relevance.append(m['tags__relevance'])
        X = np.column_stack((sizes, prices))
        y = np.asarray(relevance)
        self.regressor.partial_fit(X, y)

    def save(self):
        """
        Save the weights of the ranker model.
        """
        path = Path(self.model_path)
        model_path = path.joinpath(self.MODEL_FILENAME)

        if not path.exists():
            path.mkdir(parents=True)

        with open(model_path, mode='wb') as model_file_name:
            pickle.dump(self.regressor, model_file_name)
