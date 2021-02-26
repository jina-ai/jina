from jina.executors.rankers import Chunk2DocRanker


class WeightedRanker(Chunk2DocRanker):
    """
    Ranker for multimodal example.

    Will give the scores to chunk data according to weight.
    """
    required_keys = {'weight'}

    def _get_score(self, match_idx, query_chunk_meta, match_chunk_meta, *args, **kwargs):
        scores = match_idx[[self.COL_QUERY_CHUNK_ID, self.COL_SCORE]]

        weight_score = 0.
        for k, v in scores:
            vv = 1 / (1 + v)
            weight_score += query_chunk_meta[k]['weight'] * vv

        return self.get_doc_id(match_idx), weight_score
