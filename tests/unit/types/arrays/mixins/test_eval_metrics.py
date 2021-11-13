# some of the tested are adopted from https://github.com/ncoop57/cute_ranking/blob/main/nbs/00_core.ipynb
# the original code is licensed under Apache-2.0


from jina.math.evaluation import (
    hit_at_k,
    r_precision,
    precision_at_k,
    average_precision,
    recall_at_k,
    ndcg_at_k,
)


def test_hit_rate_at_k():
    relevancies = [0, 1]
    assert hit_at_k(relevancies, 1) == 0
    assert hit_at_k(relevancies, 2) == 1

    relevancies = [1, 1]
    assert hit_at_k(relevancies, 1) == 1
    assert hit_at_k(relevancies, 2) == 1

    relevancies = [1, 0]
    assert hit_at_k(relevancies, 1) == 1
    assert hit_at_k(relevancies, 2) == 1


def test_r_precision():
    relevancy = [0, 0, 0, 1]
    assert r_precision(relevancy) == 0.25

    relevancy = [0, 1, 0]
    assert r_precision(relevancy) == 0.5

    relevancy = [1, 0, 0]
    assert r_precision(relevancy) == 1.0


def test_precision_at_k():
    PRECISION_K_VAL = 0.0
    relevancy = [0, 0, 0, 1]
    precision_k = precision_at_k(relevancy, 1)

    assert PRECISION_K_VAL == precision_k

    PRECISION_K_VAL = 0.0
    precision_k = precision_at_k(relevancy, 2)

    assert PRECISION_K_VAL == precision_k

    precision_k = precision_at_k(relevancy, 3)

    assert PRECISION_K_VAL == precision_k

    PRECISION_K_VAL = 0.25
    precision_k = precision_at_k(relevancy)

    assert PRECISION_K_VAL == precision_k

    PRECISION_K_VAL = 0.5
    relevancy = [0, 1]
    precision_k = precision_at_k(relevancy, 2)

    assert PRECISION_K_VAL == precision_k


def test_average_precision():
    relevancy = [1, 1, 0, 1, 0, 1, 0, 0, 0, 1]
    delta_r = 1.0 / sum(relevancy)
    AVG_PRECISION_VAL = sum(
        [
            sum(relevancy[: x + 1]) / (x + 1.0) * delta_r
            for x, y in enumerate(relevancy)
            if y
        ]
    )

    avg_precision = average_precision(relevancy)

    assert AVG_PRECISION_VAL == avg_precision


def test_recall_at_k():
    RECALL_VAL = 0.33333333333333331
    relevancy = [0, 0, 1]
    recall_score = recall_at_k(relevancy, 3)

    assert RECALL_VAL == recall_score

    RECALL_VAL = 0.33333333333333331
    relevancy = [0, 0, 1]
    recall_score = recall_at_k(relevancy, 3, 3)

    assert RECALL_VAL == recall_score

    RECALL_VAL = 0.5
    relevancy = [0, 1, 0]
    recall_score = recall_at_k(relevancy, 2)

    assert RECALL_VAL == recall_score

    RECALL_VAL = 0.0
    relevancy = [0, 0, 0]
    recall_score = recall_at_k(relevancy, 3)

    assert RECALL_VAL == recall_score

    RECALL_VAL = 1.0
    relevancy = [1, 0, 0]
    recall_score = recall_at_k(relevancy, 1)

    assert RECALL_VAL == recall_score


def test_ndcg_at_k():
    NDCG_K_VAL = 1.0

    relevance = [3, 2, 3, 0, 0, 1, 2, 2, 3, 0]
    ndcg_k = ndcg_at_k(relevance, k=1)

    assert NDCG_K_VAL == ndcg_k

    NDCG_K_VAL = 0.9203032077642922

    relevance = [2, 1, 2, 0]
    ndcg_k = ndcg_at_k(relevance, k=4)

    assert NDCG_K_VAL == ndcg_k

    NDCG_K_VAL = 0.96519546960144276

    ndcg_k = ndcg_at_k(relevance, k=4, method=1)

    assert NDCG_K_VAL == ndcg_k

    NDCG_K_VAL = 0.0

    ndcg_k = ndcg_at_k([0], k=1)

    assert NDCG_K_VAL == ndcg_k

    NDCG_K_VAL = 1.0

    ndcg_k = ndcg_at_k([1], k=2)

    assert NDCG_K_VAL == ndcg_k
