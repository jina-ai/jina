from ...rank import Matches2DocRankDriver
from ....types.sets import DocumentSet


class RankerTrainerDriver(Matches2DocRankDriver):
    """Ranker trainer driver."""

    def __init__(self, method: str = 'train', *args, **kwargs):
        super().__init__(method=method, *args, **kwargs)

    def _apply_all(self, docs: 'DocumentSet', *args, **kwargs) -> None:
        """

        :param docs: the matches of the ``context_doc``, they are at granularity ``k``
        :param args: not used (kept to maintain interface)
        :param kwargs: not used (kept to maintain interface)

        .. note::
            - This driver will change in place the ordering of ``matches`` of the ``context_doc`.
            - Set the ``traversal_paths`` of this driver such that it traverses along the ``matches`` of the ``chunks`` at the level desired.
        """
        queries_metas = []
        matches_metas = []
        for doc in docs:
            query_meta = (
                doc.get_attrs(*self._exec_query_keys) if self._exec_query_keys else None
            )

            matches = doc.matches
            needs_match_meta = self._exec_match_keys is not None
            match_meta = [] if needs_match_meta else None
            for match in matches:
                if needs_match_meta:
                    match_meta.append(match.get_attrs(*self._exec_match_keys))

            # if there are no matches, no need to sort them
            queries_metas.append(query_meta)
            matches_metas.append(match_meta)

        self.exec_fn(queries_metas, matches_metas)
