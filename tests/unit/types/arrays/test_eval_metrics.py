import pytest
import random

from jina.types.arrays.mixins.ranking_evaluation import (
    precision,
    recall,
    reciprocal_rank,
    ndcg,
    fscore,
    average_precision,
)


@pytest.mark.parametrize(
    'eval_at, expected',
    [(None, 0.4), (0, 0.0), (2, 1.0), (4, 0.5), (5, 0.4), (100, 0.4)],
)
def test_precision(eval_at, expected):
    matches_ids = [0, 1, 2, 3, 4]

    desired_ids = [1, 0, 20, 30, 40]

    assert (
        precision(actual=matches_ids, desired=desired_ids, eval_at=eval_at) == expected
    )


def test_precision_no_groundtruth():
    matches_ids = [0, 1, 2, 3, 4]

    desired_ids = []

    assert precision(actual=matches_ids, desired=desired_ids, eval_at=2) == 0.0


@pytest.mark.parametrize(
    'eval_at, expected',
    [(None, 0.4), (0, 0.0), (1, 0.2), (2, 0.4), (3, 0.4), (5, 0.4), (100, 0.4)],
)
def test_recall(eval_at, expected):
    matches_ids = [0, 1, 2, 3, 4]

    desired_ids = [1, 0, 20, 30, 40]

    assert recall(actual=matches_ids, desired=desired_ids, eval_at=eval_at) == expected


def test_recall_no_matches():
    matches_ids = []

    desired_ids = [1, 0, 20, 30, 40]

    assert recall(actual=matches_ids, desired=desired_ids, eval_at=2) == 0.0


@pytest.mark.parametrize(
    'actual, desired, score',
    [
        ([], [], 0.0),
        ([1, 2, 3, 4], [], 0.0),
        ([], [1, 2, 3, 4], 0.0),
        ([1, 2, 3, 4], [1, 2, 3, 4], 1.0),
        ([1, 2, 3, 4], [2, 1, 3, 4], 0.5),
        ([1, 2, 3, 4], [11, 1, 2, 3], 0.0),
        ([4, 2, 3, 1], [1, 2, 3, 4], 0.25),
        ([2, 1, 3, 4, 5, 6, 7, 8, 9, 10], [1, 3, 6, 9, 10], 0.5),
    ],
)
def test_reciprocalrank(actual, desired, score):
    assert reciprocal_rank(actual, desired) == score


@pytest.mark.repeat(10)
@pytest.mark.parametrize('string_keys', [False, True])
@pytest.mark.parametrize(
    'actual, power_relevance, is_relevance_score, expected',
    [
        ([(1, 0.9), (3, 0.8), (4, 0.7), (2, 0.0)], False, True, 1.0),
        ([(1, 0.9), (3, 0.8), (4, 0.7), (2, 0.0)], True, True, 1.0),
        ([(10, 0.9), (30, 0.8), (40, 0.7), (20, 0.0)], False, True, 0.0),
        ([(10, 0.9), (30, 0.8), (40, 0.7), (20, 0.0)], True, True, 0.0),
        ([(1, 0.9), (3, 0.8), (4, 0.7), (2, 0.0)], False, False, 0.278),
        ([(1, 0.9), (3, 0.8), (4, 0.7), (2, 0.0)], True, False, 0.209),
        ([(1, 0.0), (3, 0.1), (4, 0.2), (2, 0.3)], False, True, 0.278),
        ([(1, 0.0), (3, 0.1), (4, 0.2), (2, 0.3)], True, True, 0.209),
        ([(1, 0.0), (3, 0.1), (4, 0.2), (2, 0.3)], False, False, 1.0),
        ([(1, 0.0), (3, 0.1), (4, 0.2), (2, 0.3)], True, False, 1.0),
    ],
)
def test_ndcg(actual, power_relevance, is_relevance_score, expected, string_keys):
    def _key_to_str(x):
        return str(x[0]), x[1]

    desired = [(1, 0.8), (3, 0.4), (4, 0.1), (2, 0.0)]
    if string_keys:
        desired = list(map(_key_to_str, desired))
        actual = list(map(_key_to_str, actual))
    random.shuffle(actual)
    random.shuffle(desired)
    assert (
        ndcg(
            actual=actual,
            desired=desired,
            eval_at=3,
            power_relevance=power_relevance,
            is_relevance_score=is_relevance_score,
        )
        == pytest.approx(expected, 0.01)
    )


@pytest.mark.parametrize(
    'actual, desired',
    [
        ([], [(1, 0.8), (2, 0.4), (3, 0.1), (4, 0)]),  # actual is empty
        ([(1, 0.4), (2, 0.1), (3, 0.8)], []),  # desired is empty
        (
            [(1, 0.4), (2, 0.1), (3, 0.8)],
            [(1, 0.4), (2, 0.1), (3, -5)],
        ),  # desired has negative value
    ],
)
def test_ndcg_fail(actual, desired):
    with pytest.raises(ValueError):
        ndcg(
            actual=actual,
            desired=desired,
            eval_at=3,
            power_relevance=True,
            is_relevance_score=True,
        )


@pytest.mark.parametrize(
    'eval_at, beta, expected',
    [
        (None, 1.0, 0.4),
        (0, 1.0, 0.0),
        (2, 1.0, 0.5714),
        (2, 0.32, 0.8777),
        (5, 1.0, 0.4),
        (100, 1.0, 0.4),
        (5, 0.5, 0.4),
        (100, 4.0, 0.4),
    ],
)
def test_fscore(eval_at, beta, expected):
    matches_ids = ['0', '1', '2', '3', '4']

    desired_ids = ['1', '0', '20', '30', '40']

    assert fscore(
        actual=matches_ids, desired=desired_ids, eval_at=eval_at, beta=beta
    ) == pytest.approx(expected, 0.001)


def test_fscore_evaluator_invalid_beta():
    matches_ids = ['0', '1', '2', '3', '4']

    desired_ids = ['1', '0', '20', '30', '40']

    with pytest.raises(AssertionError):
        fscore(actual=matches_ids, desired=desired_ids, eval_at=10, beta=0)


@pytest.mark.parametrize(
    'matches_ids, desired_ids, expected',
    [
        ([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], [1, 3, 6, 9, 10], 0.6222),
        ([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], [7, 5, 2], 0.4428),
        ([0, 1, 2, 3], [0, 1, 2, 3], 1.0),
        ([0, 1], [0, 1, 2, 3], 0.5),
        ([0, 1, 4, 5], [0, 1, 2, 3], 0.5),
        ([4, 5, 6, 7], [0, 1, 2, 3], 0.0),
        ([0, 1, 4, 2], [0, 1, 2, 3], 0.6875),
        ([0, 1, 3], [0, 1, 2, 3], 0.75),
        ([0, 1, 3, 2], [0, 1, 2, 3], 1.0),
    ],
)
def test_average_precision(matches_ids, desired_ids, expected):
    assert average_precision(actual=matches_ids, desired=desired_ids) == pytest.approx(
        expected, 0.001
    )


def test_average_precision_no_groundtruth():
    matches_ids = [0, 1, 2, 3, 4]
    desired_ids = []

    assert average_precision(actual=matches_ids, desired=desired_ids) == 0.0


def test_average_precision_no_actuals():
    matches_ids = []
    desired_ids = [1, 2]

    assert average_precision(actual=matches_ids, desired=desired_ids) == 0.0
