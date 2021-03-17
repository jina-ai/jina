from typing import Dict, List

from jina.executors.rankers import Match2DocRanker
from jina.executors.decorators import batching_multi_input


class DummyRanker(Match2DocRanker):
    """
    :class:`LevenshteinRanker` Computes the negative Levenshtein distance
        between a query and its matches. The distance is negative, in order to
        achieve a bigger=better sorting in the respective driver.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.match_required_keys = ['tags__dummy_score']

    @batching_multi_input(slice_nargs=3)
    def score(
        self,
        old_match_scores: List[Dict],
        queries_metas: List[Dict],
        matches_metas: List[List[Dict]],
    ) -> List[List[float]]:
        return [
            [m['tags__dummy_score'] for m in match_meta] for match_meta in matches_metas
        ]
