from typing import Iterable

from ...rank import Matches2DocRankDriver


class RankerTrainerDriver(Matches2DocRankDriver):
    """"""

    def __init__(self, method: str = 'train', *args, **kwargs):
        super().__init__(method=method, *args, **kwargs)

    def _sort_matches_in_place(
        self, matches: 'MatchArray', match_scores: Iterable[float]
    ) -> None:
        pass
