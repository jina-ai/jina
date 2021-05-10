import pickle
from typing import List, Dict

import numpy as np

from jina.executors.decorators import single
from jina.executors.rankers import Match2DocRanker


class SGDRegressorRanker(Match2DocRanker):
    """The :class:`SGDRegressorRanker` loads an :class:`SGDRegressor` and make use of the trained model
    to predict relevance score."""

    MODEL_FILENAME = 'model.pickle'

    def __init__(self, model_path: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = None
        self.model_path = model_path
        self.match_required_keys = {'tags__size', 'tags__price'}
        self.query_required_keys = None

    def post_init(self):
        super().post_init()
        with open(self.model_path + '/' + self.MODEL_FILENAME, 'rb') as pickle_file:
            self.model = pickle.load(pickle_file)

    @single
    def score(
        self,
        old_match_scores: List[List[float]],
        queries_metas: List[Dict],
        matches_metas: List[List[Dict]],
    ) -> 'np.ndarray':
        """
        Scoring function of the ranker.

        This method extract features, i.e. `size` and `price` from `Document` tags,
        make prediction based on the loaded model and return the score.
        """
        sizes = []
        prices = []
        for match_meta in matches_metas:
            for m in match_meta:
                sizes.append(m['tags__size'])
                prices.append(m['tags__price'])
        X = np.column_stack((prices, sizes))
        print("======")
        print(X)
        print(self.model.predict(X))
        print("======")
        return self.model.predict(X)
