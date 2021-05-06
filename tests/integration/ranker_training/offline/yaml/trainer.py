import pickle
from pathlib import Path
from typing import List, Dict

import numpy as np

from jina.executors.decorators import batching
from jina.executors.rankers import Match2DocRanker
from jina.executors.rankers.trainer import RankerTrainer


class SGDRegressorRanker(Match2DocRanker):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def post_init(self):
        super().post_init()
        self.regressor = pickle.load('model.pickle')

    @batching(slice_nargs=3)
    def score(
        self,
        old_match_scores: List[List[float]],
        query_meta: List[Dict],
        match_meta: List[List[Dict]],
    ) -> 'np.ndarray':
        # build X
        dataset = self._get_features_dataset(
            query_meta=query_meta, match_meta=match_meta
        )
        return self.booster.predict(dataset.get_data())


class SGDRegressorRankerTrainer(RankerTrainer):

    MODEL_FILENAME = 'model.pickle'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def post_init(self):
        from sklearn.linear_model import SGDRegressor

        self.regressor = SGDRegressor(warm_start=True)

    def train(self, matches_metas, *args, **kwargs):
        sizes = []
        prices = []
        relevance = []
        for match_meta in matches_metas:
            for m in match_meta:
                sizes.append(m['tags__size'])
                prices.append(m['tags__price'])
                relevance.append(m['tags_relevance'])
        X = np.column_stack((sizes, prices))
        y = np.asarray(relevance)
        self.regressor.partial_fit(X, y)

    def save(self, filename: str):
        """
        Save the weights of the ranker model.
        """
        path = Path(filename)
        model_path = path.joinpath(self.MODEL_FILENAME)

        if not path.exists():
            path.mkdir(parents=True)
        else:
            raise FileExistsError(f'{path} already exist, fail to save.')

        with open(model_path, mode='wb') as model_file_name:
            pickle.dump(self.regressor, model_file_name)
