import pickle
from pathlib import Path
from typing import List, Dict

import numpy as np

from jina.executors.decorators import batching
from jina.executors.rankers import Match2DocRanker


class SGDRegressorRanker(Match2DocRanker):

    MODEL_FILENAME = 'model.pickle'

    def __init__(self, model_path: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = None
        self.model_path = model_path

    def post_init(self):
        super().post_init()
        path = Path(self.model_path)
        model_path = path.joinpath(path, self.MODEL_FILENAME)
        if not model_path.exists():
            raise FileNotFoundError('Ranker file not found.')
        self.model = pickle.load(model_path)

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
        return self.model.predict(dataset.get_data())
