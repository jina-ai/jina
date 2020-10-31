from typing import Dict

import numpy as np

from jina.executors.rankers import Match2DocRanker


class DummyRanker(Match2DocRanker):
    """
    :class:`LevenshteinRanker` Computes the negative Levenshtein distance
        between a query and its matches. The distance is negative, in order to
        achieve a bigger=better sorting in the respective driver.
    """

    required_keys = {'tags'}

    def score(
            self, query_meta: Dict, old_match_scores: Dict, match_meta: Dict
    ) -> "np.ndarray":
        new_scores = [
            (
                match_id,
                match_meta[match_id]['tags']['dummy_score']
            )
            for match_id, old_score in old_match_scores.items()
        ]
        return np.array(new_scores, dtype=[
            (self.COL_MATCH_HASH, np.int64),
            (self.COL_SCORE, np.float64)])
