from jina.executors.rankers import Chunk2DocRanker


class WeightedRanker(Chunk2DocRanker):
    """
    Ranker for multimodal example.

    Will give the scores to chunk data according to weight.
    """

    match_required_keys = None
    query_required_keys = {'weight'}

    def score(self, match_idx, query_chunk_meta, match_chunk_meta, *args, **kwargs):
        """
        Given a set of queries (that may correspond to the chunks of a root level query) and a set of matches
        corresponding to the same parent id, compute the matching score of the common parent of the set of matches.
        Returns a score corresponding to the score of the parent document of the matches in `match_idx`

        :param match_idx: A [N x 4] numpy ``ndarray``, column-wise:
                - ``match_idx[:, 0]``: ``parent_id`` of the matched docs, integer
                - ``match_idx[:, 1]``: ``id`` of the matched chunks, integer
                - ``match_idx[:, 2]``: ``id`` of the query chunks, integer
                - ``match_idx[:, 3]``: distance/metric/score between the query and matched chunks, float.
                All the matches belong to the same `parent`
        :param query_chunk_meta: The meta information of the query chunks, where the key is query chunks' ``chunk_id``,
            the value is extracted by the ``query_required_keys``.
        :param match_chunk_meta: The meta information of the matched chunks, where the key is matched chunks'
            ``chunk_id``, the value is extracted by the ``match_required_keys``.
        :param args: Extra positional arguments
        :param kwargs: Extra keyword arguments
        :return: Return the score associated to the parent id of the matches
        """

        scores = match_idx[[self.COL_QUERY_CHUNK_ID, self.COL_SCORE]]

        weight_score = 0.0
        for k, v in scores:
            vv = 1 / (1 + v)
            weight_score += query_chunk_meta[k]['weight'] * vv

        return weight_score
