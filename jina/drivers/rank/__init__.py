from typing import Tuple, Optional

import numpy as np

from .. import BaseExecutableDriver, FlatRecursiveMixin
from ...types.document import Document
from ...types.score import NamedScore

if False:
    from ...types.sets import DocumentSet


class BaseRankDriver(FlatRecursiveMixin, BaseExecutableDriver):
    """Drivers inherited from this Driver will bind :meth:`rank` by default """

    def __init__(
        self, executor: Optional[str] = None, method: str = 'score', *args, **kwargs
    ):
        super().__init__(executor, method, *args, **kwargs)

    @property
    def _exec_match_keys(self):
        """Property to provide backward compatibility to executors relying in `required_keys`
        :return: keys for attribute lookup in matches
        """
        return (
            self.exec.match_required_keys
            if hasattr(self.exec, 'match_required_keys')
            else getattr(self.exec, 'required_keys', None)
        )

    @property
    def _exec_query_keys(self):
        """Property to provide backward compatibility to executors relying in `required_keys`

        :return: keys for attribute lookup in matches
        """
        return (
            self.exec.query_required_keys
            if hasattr(self.exec, 'query_required_keys')
            else getattr(self.exec, 'required_keys', None)
        )


class Matches2DocRankDriver(BaseRankDriver):
    """This driver is intended to only resort the given matches on the 0 level granularity for a document.
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

    def __init__(
        self,
        reverse: bool = False,
        traversal_paths: Tuple[str] = ('r',),
        *args,
        **kwargs
    ):
        super().__init__(traversal_paths=traversal_paths, *args, **kwargs)
        self.reverse = reverse

    def _apply_all(self, docs: 'DocumentSet', *args, **kwargs) -> None:
        """

        :param docs: the matches of the ``context_doc``, they are at granularity ``k``
        :param *args: not used (kept to maintain interface)
        :param **kwargs: not used (kept to maintain interface)

        .. note::
            - This driver will change in place the ordering of ``matches`` of the ``context_doc`.
            - Set the ``traversal_paths`` of this driver such that it traverses along the ``matches`` of the ``chunks`` at the level desired.
        """
        for doc in docs:
            query_meta = (
                doc.get_attrs(*self._exec_query_keys) if self._exec_query_keys else None
            )

            matches = doc.matches
            old_match_scores = {match.id: match.score.value for match in matches}
            match_meta = (
                {match.id: match.get_attrs(*self._exec_match_keys) for match in matches}
                if self._exec_match_keys
                else None
            )

            # if there are no matches, no need to sort them
            if not old_match_scores:
                continue

            new_match_scores = self.exec_fn(query_meta, old_match_scores, match_meta)
            self._sort_matches_in_place(doc, new_match_scores)

    def _sort_matches_in_place(
        self, context_doc: 'Document', match_scores: 'np.ndarray'
    ) -> None:
        op_name = self.exec.__class__.__name__
        cm = context_doc.matches
        cm.build()
        for match_id, score in match_scores:
            cm[match_id].score = NamedScore(
                value=score, op_name=op_name, ref_id=context_doc.id
            )

        cm.sort(key=lambda x: x.score.value, reverse=True)
