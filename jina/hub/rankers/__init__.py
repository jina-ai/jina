__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from jina.executors.rankers import Chunk2DocRanker


class MaxRanker(Chunk2DocRanker):
    """
    :class:`MaxRanker` calculates the score of the matched doc form the matched chunks. For each matched doc, the score
        is the maximal score from all the matched chunks belonging to this doc.

    .. warning: Here we suppose that the larger chunk score means the more similar.
    """

    def _get_score(self, match_idx, query_chunk_meta, match_chunk_meta, *args, **kwargs):
        return self.get_doc_id(match_idx), match_idx[:, self.col_score].max()


class MinRanker(Chunk2DocRanker):
    """
    :class:`MinRanker` calculates the score of the matched doc form the matched chunks. For each matched doc, the score
        is `1 / (1 + s)`, where `s` is the minimal score from all the matched chunks belonging to this doc.

    .. warning:: Here we suppose that the smaller chunk score means the more similar.
    """

    def _get_score(self, match_idx, query_chunk_meta, match_chunk_meta, *args, **kwargs):
        _doc_id = match_idx[0, self.col_doc_id]
        return self.get_doc_id(match_idx), 1. / (1. + match_idx[:, self.col_score].min())
