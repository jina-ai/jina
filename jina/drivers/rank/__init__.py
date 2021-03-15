from typing import Tuple, Optional, Iterable

from .. import BaseExecutableDriver, FlatRecursiveMixin
from ...types.sets import MatchSet
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
        return getattr(
            self.exec, 'match_required_keys', getattr(self.exec, 'required_keys', None)
        )

    @property
    def _exec_query_keys(self):
        """Property to provide backward compatibility to executors relying in `required_keys`

        :return: keys for attribute lookup in matches
        """
        return getattr(
            self.exec, 'query_required_keys', getattr(self.exec, 'required_keys', None)
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
        reverse: bool = True,
        traversal_paths: Tuple[str] = ('r',),
        *args,
        **kwargs,
    ):
        super().__init__(traversal_paths=traversal_paths, *args, **kwargs)
        self.reverse = reverse

    def _apply_all(self, docs: 'DocumentSet', *args, **kwargs) -> None:
        """

        :param docs: the matches of the ``context_doc``, they are at granularity ``k``
        :param args: not used (kept to maintain interface)
        :param kwargs: not used (kept to maintain interface)

        .. note::
            - This driver will change in place the ordering of ``matches`` of the ``context_doc`.
            - Set the ``traversal_paths`` of this driver such that it traverses along the ``matches`` of the ``chunks`` at the level desired.
        """
        old_scores = []
        queries_metas = []
        matches_metas = []
        for doc in docs:
            query_meta = (
                doc.get_attrs(*self._exec_query_keys) if self._exec_query_keys else None
            )

            matches = doc.matches
            old_match_scores = []
            needs_match_meta = self._exec_match_keys is not None
            match_meta = [] if needs_match_meta else None
            for match in matches:
                old_match_scores.append(match.score.value)
                if needs_match_meta:
                    match_meta.append(match.get_attrs(*self._exec_match_keys))

            # if there are no matches, no need to sort them
            old_scores.append(old_match_scores)
            queries_metas.append(query_meta)
            matches_metas.append(match_meta)

        new_scores = self.exec_fn(old_scores, queries_metas, matches_metas)
        if len(new_scores) != len(docs):
            msg = f'The number of scores {len(new_scores)} does not match the number of queries {len(docs)}'
            self.logger.error(msg)
            raise ValueError(msg)

        for doc, scores in zip(docs, new_scores):
            matches = doc.matches
            if len(doc.matches) != len(scores):
                msg = (
                    f'The number of matches to be scored {len(doc.matches)} do not match the number of scores returned '
                    f'by the ranker {self.exec.__name__} for doc: {doc.id} '
                )
                self.logger.error(msg)
                raise ValueError(msg)
            self._sort_matches_in_place(matches, scores)

    def _sort_matches_in_place(
        self, matches: 'MatchSet', match_scores: Iterable[float]
    ) -> None:
        op_name = self.exec.__class__.__name__
        ref_doc_id = matches._ref_doc.id

        for match, score in zip(matches, match_scores):
            match.score = NamedScore(value=score, op_name=op_name, ref_id=ref_doc_id)

        matches.sort(key=lambda x: x.score.value, reverse=self.reverse)
