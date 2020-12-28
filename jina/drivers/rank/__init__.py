from typing import Tuple

import numpy as np

from .. import BaseExecutableDriver
from ...types.document import Document
from ...types.document.uid import UniqueId
from ...types.score import NamedScore


if False:
    from ...types.sets import DocumentSet


class BaseRankDriver(BaseExecutableDriver):
    """Drivers inherited from this Driver will bind :meth:`rank` by default """

    def __init__(self, executor: str = None, method: str = 'score', *args, **kwargs):
        super().__init__(executor, method, *args, **kwargs)


class Matches2DocRankDriver(BaseRankDriver):
    """ This driver is intended to only resort the given matches on the 0 level granularity for a document.
    It gets the scores from a Ranking Executor, which does only change the scores of matches.
    Afterwards, the Matches2DocRankDriver resorts all matches for a document.
    Input-Output ::
        Input:
        document: {granularity: 0, adjacency: k}
            |- matches: {granularity: 0, adjacency: k+1}
        Output:
        document: {granularity: 0, adjacency: k}
            |- matches: {granularity: 0, adjacency: k+1} (Sorted according to scores from Ranker Executor)
    """

    def __init__(self, reverse: bool = False, traversal_paths: Tuple[str] = ('m',), *args, **kwargs):
        super().__init__(traversal_paths=traversal_paths, *args, **kwargs)
        self.reverse = reverse

    def _apply_all(self, docs: 'DocumentSet', context_doc: 'Document', *args,
                   **kwargs) -> None:
        """

        :param docs: the matches of the ``context_doc``, they are at granularity ``k``
        :param context_doc: the query document having ``docs`` as its matches, it is at granularity ``k``
        :return:

        .. note::
            - This driver will change in place the ordering of ``matches`` of the ``context_doc`.
            - Set the ``traversal_paths`` of this driver such that it traverses along the ``matches`` of the ``chunks`` at the level desired.
        """

        # if at the top-level already, no need to aggregate further
        query_meta = context_doc.get_attrs(*self.exec.required_keys)

        old_match_scores = {match.id: match.score.value for match in docs}
        match_meta = {match.id: match.get_attrs(*self.exec.required_keys) for match in docs}
        # if there are no matches, no need to sort them
        if not old_match_scores:
            return

        new_match_scores = self.exec_fn(query_meta, old_match_scores, match_meta)
        self._sort_matches_in_place(context_doc, new_match_scores)

    def _sort_matches_in_place(self, context_doc: 'Document', match_scores: 'np.ndarray') -> None:
        op_name = self.exec.__class__.__name__
        cm = context_doc.matches
        cm.build()
        for str_match_id, score in match_scores:
            match_id = UniqueId(str_match_id)
            cm[match_id].score = NamedScore(value=score, op_name=op_name, ref_id=context_doc.id)

        cm.sort(key=lambda x: x.score.value, reverse=True)
