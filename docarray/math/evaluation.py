# some implementations are adopted from https://github.com/ncoop57/cute_ranking/blob/main/cute_ranking/core.py
# the original code is licensed under Apache-2.0

from typing import List, Optional

import numpy as np


def _check_k(k):
    if k is not None and k < 1:
        raise ValueError(f'`k` must be >=1 or `None`')


def r_precision(binary_relevance: List[int]) -> float:
    """R Precision after all relevant documents have been retrieved
    Relevance is binary (nonzero is relevant).

    .. seealso::
        https://en.wikipedia.org/wiki/Evaluation_measures_(information_retrieval)#R-precision

    :param binary_relevance: binary relevancy in rank order
    :return: precision
    """
    binary_relevance = np.array(binary_relevance) != 0
    z = binary_relevance.nonzero()[0]
    if not z.size:
        return 0.0
    return float(np.mean(binary_relevance[: z[-1] + 1]))


def precision_at_k(binary_relevance: List[int], k: Optional[int] = None) -> float:
    """Precision @K.

    :param binary_relevance: binary relevancy in rank order
    :param k: measured on top-k
    :return: precision @k
    """
    _check_k(k)
    binary_relevance = np.array(binary_relevance)[:k] != 0
    return float(np.mean(binary_relevance))


def hit_at_k(binary_relevance: List[int], k: Optional[int] = None) -> int:
    """Score is percentage of first relevant item in list that occur

    :param binary_relevance: binary relevancy in rank order
    :param k: measured on top-k
    :return: hit @k if hit return 1 else 0
    """
    _check_k(k)
    return 1 if np.sum(binary_relevance[:k]) > 0 else 0


def average_precision(binary_relevance: List[int]) -> float:
    """Score is average precision (area under PR curve)
    Relevance is binary (nonzero is relevant).

    :param binary_relevance: binary relevancy in rank order
    :return: Average precision
    """
    r = np.array(binary_relevance) != 0
    out = [precision_at_k(r, k + 1) for k in range(r.size) if r[k]]
    if not out:
        return 0.0
    return float(np.mean(out))


def reciprocal_rank(binary_relevance: List[int]) -> float:
    """Score is reciprocal of the rank of the first relevant item

    :param binary_relevance: binary relevancy in rank order
    :return: Average precision
    """
    rs = np.array(binary_relevance).nonzero()[0]
    return 1.0 / (rs[0] + 1) if rs.size else 0.0


def recall_at_k(
    binary_relevance: List[int], max_rel: int, k: Optional[int] = None
) -> float:
    """Score is recall after all relevant documents have been retrieved
    Relevance is binary (nonzero is relevant).

    :param binary_relevance: binary relevancy in rank order
    :param k: measured on top-k
    :param max_rel: Maximum number of documents that can be relevant
    :return: Recall score
    """
    _check_k(k)
    binary_relevance = np.array(binary_relevance[:k]) != 0
    if np.sum(binary_relevance) > max_rel:
        raise ValueError(f'Number of relevant Documents retrieved > {max_rel}')
    return np.sum(binary_relevance) / max_rel


def f1_score_at_k(
    binary_relevance: List[int], max_rel: int, k: Optional[int] = None
) -> float:
    """Score is harmonic mean of precision and recall
    Relevance is binary (nonzero is relevant).

    :param binary_relevance: binary relevancy in rank order
    :param k: measured on top-k
    :param max_rel: Maximum number of documents that can be relevant
    :return: F1 score @ k
    """
    _check_k(k)
    p = precision_at_k(binary_relevance, k)
    r = recall_at_k(binary_relevance, max_rel, k)
    if (p + r) > 0:
        return 2 * p * r / (p + r)
    else:
        return 0.0


def dcg_at_k(relevance: List[float], method: int = 0, k: Optional[int] = None):
    """Score is discounted cumulative gain (dcg)
    Relevance is positive real values. Can use binary
    as the previous methods.

    Example from
    http://www.stanford.edu/class/cs276/handouts/EvaluationNew-handout-6-per.pdf

    :param relevance: Relevance scores (list or numpy) in rank order
            (first element is the first item)
    :param k: measured on top-k
    :param method: If 0 then weights are [1.0, 1.0, 0.6309, 0.5, 0.4307, ...]
                If 1 then weights are [1.0, 0.6309, 0.5, 0.4307, ...]
    :return: Discounted cumulative gain
    """
    _check_k(k)
    r = np.asfarray(relevance)[:k]
    if r.size:
        if method == 0:
            return r[0] + np.sum(r[1:] / np.log2(np.arange(2, r.size + 1)))
        elif method == 1:
            return np.sum(r / np.log2(np.arange(2, r.size + 2)))
        else:
            raise ValueError('method must be 0 or 1.')
    return 0.0


def ndcg_at_k(relevance: List[float], method: int = 0, k: Optional[int] = None):
    """Score is normalized discounted cumulative gain (ndcg)
    Relevance is positive real values.  Can use binary
    as the previous methods.

    Example from
    http://www.stanford.edu/class/cs276/handouts/EvaluationNew-handout-6-per.pdf

    :param relevance: Relevance scores (list or numpy) in rank order
            (first element is the first item)
    :param k: measured on top-k
    :param method: If 0 then weights are [1.0, 1.0, 0.6309, 0.5, 0.4307, ...]
                If 1 then weights are [1.0, 0.6309, 0.5, 0.4307, ...]
    :return: Normalized discounted cumulative gain
    """
    _check_k(k)
    dcg_max = dcg_at_k(sorted(relevance, reverse=True), method=method, k=k)
    if not dcg_max:
        return 0.0
    return dcg_at_k(relevance, method=method, k=k) / dcg_max
