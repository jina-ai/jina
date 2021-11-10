from abc import ABC, abstractmethod
from collections import defaultdict
import itertools

from typing import Optional, Union, List, Tuple, Sequence, Any, Dict
from math import log

from .traverse import TraverseMixin
from jina.types.document import Document


def precision(
    actual: Sequence[Any],
    desired: Sequence[Any],
    eval_at: Optional[int],
    *args,
    **kwargs,
) -> float:
    """
    Compute precision evaluation score
    :param eval_at: the point at which evaluation is computed, if None give, will consider all the input to evaluate
    :param actual: the matched document identifiers from the request as matched by jina indexers and rankers
    :param desired: the expected documents matches ids sorted as they are expected
    :param args:  Additional positional arguments
    :param kwargs: Additional keyword arguments
    :return: the evaluation metric value for the request document
    """
    if eval_at == 0:
        return 0.0
    actual_at_k = actual[:eval_at] if eval_at else actual
    ret = len(set(actual_at_k).intersection(set(desired)))
    sub = len(actual_at_k)
    return ret / sub if sub != 0 else 0.0


def recall(
    actual: Sequence[Any],
    desired: Sequence[Any],
    eval_at: Optional[int],
    *args,
    **kwargs,
) -> float:
    """
    Compute precision evaluation score
    :param eval_at: the point at which evaluation is computed, if None give, will consider all the input to evaluate
    :param actual: the matched document identifiers from the request as matched by jina indexers and rankers
    :param desired: the expected documents matches ids sorted as they are expected
    :param args:  Additional positional arguments
    :param kwargs: Additional keyword arguments
    :return: the evaluation metric value for the request document
    """
    if eval_at == 0:
        return 0.0
    actual_at_k = actual[:eval_at] if eval_at else actual
    ret = len(set(actual_at_k).intersection(set(desired)))
    return ret / len(desired)


def ndcg(
    actual: Sequence[Tuple[Any, Union[int, float]]],
    desired: Sequence[Tuple[Any, Union[int, float]]],
    eval_at: Optional[int],
    power_relevance: bool,
    is_relevance_score: bool,
    *args,
    **kwargs,
) -> float:
    """Evaluate normalized discounted cumulative gain for information retrieval.

    :param actual: The tuple of Ids and Scores predicted by the search system. They will be sorted in descending order.
    :param desired: The expected id and relevance tuples given by user as matching groundtruth.
    :param eval_at: The number of documents in each of the lists to consider in the NDCG computation. If ``None``is given, the complete lists are considered for the evaluation.
    :param power_relevance: The power relevance places stronger emphasis on retrieving relevant documents. For detailed information, please check https://en.wikipedia.org/wiki/Discounted_cumulative_gain
    :param is_relevance_score: Boolean indicating if the actual scores are to be considered relevance. Highest value is better.
        If True, the information coming from the actual system results will
        be sorted in descending order, otherwise in ascending order.
        Since the input of the evaluate method is sorted according to the
        `scores` of both actual and desired input, this parameter is
        useful for instance when the ``matches` come directly from a ``VectorIndexer``
        where score is `distance` and therefore the smaller the better.
    :param args:  Additional positional arguments
    :param kwargs: Additional keyword arguments
    :return: The evaluation metric value for the request document.
    """

    def _compute_dcg(gains):
        ret = 0.0
        if not power_relevance:
            for score, position in zip(gains[1:], range(2, len(gains) + 1)):
                ret += score / log(position, 2)
            return gains[0] + ret
        for score, position in zip(gains, range(1, len(gains) + 1)):
            ret += (pow(2, score) - 1) / log(position + 1, 2)
        return ret

    def _compute_idcg(gains):
        sorted_gains = sorted(gains, reverse=True)
        return _compute_dcg(sorted_gains)

    relevances = dict(desired)
    actual_relevances = list(
        map(
            lambda x: relevances[x[0]] if x[0] in relevances else 0.0,
            sorted(actual, key=lambda x: x[1], reverse=is_relevance_score),
        )
    )
    desired_relevances = list(
        map(lambda x: x[1], sorted(desired, key=lambda x: x[1], reverse=True))
    )

    # Information gain must be greater or equal to 0.
    actual_at_k = actual_relevances[:eval_at] if eval_at else actual
    desired_at_k = desired_relevances[:eval_at] if eval_at else desired
    if not actual_at_k:
        raise ValueError(
            f'Expecting gains at k with minimal length of 1, {len(actual_at_k)} received.'
        )
    if not desired_at_k:
        raise ValueError(
            f'Expecting desired at k with minimal length of 1, {len(desired_at_k)} received.'
        )
    if any(item < 0 for item in actual_at_k) or any(item < 0 for item in desired_at_k):
        raise ValueError('One or multiple score is less than 0.')
    dcg = _compute_dcg(gains=actual_at_k)
    idcg = _compute_idcg(gains=desired_at_k)
    return 0.0 if idcg == 0.0 else dcg / idcg


def reciprocal_rank(
    actual: Sequence[Any], desired: Sequence[Any], *args, **kwargs
) -> float:
    """
    Evaluate score as per reciprocal rank metric.
    :param actual: Sequence of sorted document IDs.
    :param desired: Sequence of sorted relevant document IDs
        (the first is the most relevant) and the one to be considered.
    :param args:  Additional positional arguments
    :param kwargs: Additional keyword arguments
    :return: Reciprocal rank score
    """
    if len(actual) == 0 or len(desired) == 0:
        return 0.0
    try:
        return 1.0 / (actual.index(desired[0]) + 1)
    except Exception:
        return 0.0


def average_precision(
    actual: Sequence[Any], desired: Sequence[Any], *args, **kwargs
) -> float:
    """ "
    Evaluate the Average Precision of the search.
    :param actual: the matched document identifiers from the request
        as matched by Indexers and Rankers
    :param desired: A list of all the relevant IDs. All documents
        identified in this list are considered to be relevant
    :param args:  Additional positional arguments
    :param kwargs: Additional keyword arguments
    :return: the evaluation metric value for the request document
    """

    if len(desired) == 0 or len(actual) == 0:
        return 0.0

    desired_set = set(desired)

    def _precision(eval_at: int):
        if actual[eval_at - 1] not in desired_set:
            return 0.0
        actual_at_k = actual[:eval_at]
        ret = len(set(actual_at_k).intersection(desired_set))
        sub = len(actual_at_k)
        return ret / sub if sub != 0 else 0.0

    precisions = list(
        map(lambda eval_at: _precision(eval_at=eval_at), range(1, len(actual) + 1))
    )
    return sum(precisions) / len(desired)


def fscore(
    actual: Sequence[Any],
    desired: Sequence[Any],
    eval_at: Optional[int],
    beta: float,
    *args,
    **kwargs,
) -> float:
    """ "
    Evaluate the f-score of the search.
    :param eval_at: The point at which precision and recall are computed,
        if ``None`` is given, all input will be considered to evaluate.
    :param actual: The matched document identifiers from the request
        as matched by jina indexers and rankers
    :param desired: The expected documents matches
    :param beta: Parameter to weight differently precision and recall.
        When ``beta` is 1, the fScore corresponds to the harmonic mean
        of precision and recall
    :param args: Additional positional arguments
    :param kwargs: Additional keyword arguments
    :return: the evaluation metric value for the request document
    """
    assert beta != 0, 'fScore is not defined for beta 0'
    weight = beta ** 2
    if not desired or eval_at == 0:
        return 0.0

    actual_at_k = actual[:eval_at] if eval_at else actual
    common_count = len(set(actual_at_k).intersection(set(desired)))
    recall = common_count / len(desired)

    divisor = min(eval_at or len(desired), len(desired))

    if divisor != 0.0:
        precision = common_count / divisor
    else:
        precision = 0

    if precision + recall == 0:
        return 0

    return ((1 + weight) * precision * recall) / ((weight * precision) + recall)


class RankingEvaluationMixin(ABC):
    """ A mixin that provides ranking evaluation functionality to DocumentArrayLike objects"""

    funcs = {
        'precision': precision,
        'recall': recall,
        'ndcg': ndcg,
        'reciprocal_rank': reciprocal_rank,
        'average_precision': average_precision,
        'fscore': fscore,
    }

    @abstractmethod
    def __iter__(self):
        ...

    class _DocGroundtruthPair:
        def __init__(self, doc: 'Document', groundtruth: 'Document'):
            self.pair = (doc, groundtruth)

        def __getitem__(self, item):
            return self.pair[item]

        @property
        def doc(self):
            return self[0]

        @property
        def groundtruth(self):
            return self[1]

        @property
        def matches(self):
            pairs = []
            for doc, groundtruth in zip(self.doc.matches, self.groundtruth.matches):
                pairs.append(
                    RankingEvaluationMixin._DocGroundtruthPair(doc, groundtruth)
                )
            return RankingEvaluationMixin._DocGroundtruthArray(pairs)

        @property
        def chunks(self):
            assert len(self.doc.chunks) == len(self.groundtruth.chunks)
            pairs = []
            for doc, groundtruth in zip(self.doc.chunks, self.groundtruth.chunks):
                pairs.append(
                    RankingEvaluationMixin._DocGroundtruthPair(doc, groundtruth)
                )
            return RankingEvaluationMixin._DocGroundtruthArray(pairs)

    class _DocGroundtruthArray(TraverseMixin):
        def __init__(self, pairs):
            self._pairs = pairs

        @property
        def matches(self):
            pairs = []
            for doc, groundtruth in zip(self.doc.matches, self.groundtruth.matches):
                pairs.append(
                    RankingEvaluationMixin._DocGroundtruthPair(doc, groundtruth)
                )
            return RankingEvaluationMixin._DocGroundtruthArray(pairs)

        @property
        def chunks(self):
            assert len(self.doc.chunks) == len(self.groundtruth.chunks)
            pairs = []
            for doc, groundtruth in zip(self.doc.chunks, self.groundtruth.chunks):
                pairs.append(
                    RankingEvaluationMixin._DocGroundtruthPair(doc, groundtruth)
                )
            return RankingEvaluationMixin._DocGroundtruthArray(pairs)

        def __iter__(self):
            for pair in self._pairs:
                yield pair

        @staticmethod
        def _flatten(sequence):
            return RankingEvaluationMixin._DocGroundtruthArray(
                list(itertools.chain.from_iterable(sequence))
            )

    def evaluate(
        self,
        groundtruth: TraverseMixin,
        metrics: Union[str, List[str]],
        attribute_fields: List[Union[str, Tuple[str]]] = ('tags__id',),
        eval_at: Optional[Union[int, List[Optional[int]]]] = None,
        evaluation_names: Optional[List[Optional[str]]] = None,
        traversal_paths: List[str] = ['r'],
        **kwargs,
    ) -> Dict[str, float]:

        """Compute ranking evaluation metrics for a given `DocumentArray` when compared with a groundtruth.

        This implementation expects to provide a `groundtruth` DocumentArray that is structurally identical to `self`. It is based
        on comparing the `matches` of `documents` inside the `DocumentArray.

        This method will fill the `evaluations` field of Documents inside this `DocumentArray` and will return the average of the computations

        .. note::
            .. highlight:: python
            .. code-block:: python

                from jina import Document, DocumentArray

                doc = Document(text='query')
                doc.matches.append(Document(text='answer1', tags={'document_id': 0})
                doc.matches.append(Document(text='answer1', tags={'document_id': 10})

                groundtruth = Document() # content irrelevant, evaluation is based on identifiers
                groundtruth.matches.append(tags={'document_id': 0})
                groundtruth.matches.append(tags={'document_id': 1})

                # In this case, Document matches the following ids [0, 10, -1] while from the groundtruth we expect to match [0, 1]
                d_array = DocumentArray([doc])
                gt_array = DocumentArray([groundtruth])
                d_array.evaluate(gt_array, metrics=['precision', 'recall'], attribute_fields=('tags__document_id'), eval_at=[1, 2])

        :param groundtruth: The groundtruth DocumentArray` that the `DocumentArray` compares to.
        :param metrics: The name of the metric, or multiple metrics to be computed
        :param attribute_fields: The list of attribute fields needed for each of the metrics to be computed.
        :param eval_at: The threshold at which the metrics are computed. Useful to compute metrics such as precision@1.
        :param evaluation_names: If provided, the results of the metrics computation will be stored in the `evaluations` field of each Document. If not provided, the name will be computed based on the metrics name.
        :param traversal_paths: The traversal path that will be applied to both `self` and `groundtruth`. In order to compute the ranking evaluation. Useful to evaluate solutions returning matches for `chunks` and other levels.

        .. note::
            .. highlight:: python
            .. code-block:: python

                from jina import Document, DocumentArray

                doc = Document(blob=...) # image blob
                doc.chunks[0] = Document(blob=...) # image patch 1
                doc.chunks[1] = Document(blob=...) # image patch 2
                doc.chunks[0].matches.append(Document(..., tags={'document_id': 0})
                doc.chunks[0].matches.append(Document(..., tags={'document_id': 10})
                doc.chunks[1].matches.append(Document(..., tags={'document_id': 10})
                doc.chunks[1].matches.append(Document(..., tags={'document_id': 0})

                groundtruth = Document() # content irrelevant, evaluation is based on identifiers
                doc.chunks[0] = Document(blob=...) # content irrelevant, evaluation is based on identifiers
                doc.chunks[1] = Document(blob=...) # content irrelevant, evaluation is based on identifiers
                doc.chunks[0].matches.append(Document(..., tags={'document_id': 0})
                doc.chunks[0].matches.append(Document(..., tags={'document_id': 1})
                doc.chunks[1].matches.append(Document(..., tags={'document_id': 1})
                doc.chunks[1].matches.append(Document(..., tags={'document_id': 0})

                # In this case, Document matches the following ids [0, 10, -1] while from the groundtruth we expect to match [0, 1]
                d_array = DocumentArray([doc])
                gt_array = DocumentArray([groundtruth])
                d_array.evaluate(gt_array, metrics=['precision', 'recall'], attribute_fields=('tags__document_id'), eval_at=[1, 2], traversal_paths=['c'])

        :param kwargs: Additional keyword arguments to be passed to each specific `evaluation function`
        :return: The average evaluation computed or a list of them if multiple metrics are required
        """
        docs_groundtruths = RankingEvaluationMixin._DocGroundtruthArray(
            [
                RankingEvaluationMixin._DocGroundtruthPair(doc, groundtruth)
                for doc, groundtruth in zip(self, groundtruth)
            ]
        )

        if isinstance(attribute_fields[0], str):
            attribute_fields = [attribute_fields]

        metrics_list = metrics if isinstance(metrics, list) else [metrics]
        results = defaultdict(float)

        num = 0
        for doc, groundtruth in docs_groundtruths.traverse_flat(traversal_paths):
            if eval_at is not None:
                if isinstance(eval_at, int):
                    eval_at_iter = [eval_at] * len(metrics_list)
                else:
                    eval_at_iter = eval_at
            else:
                eval_at_iter = [None] * len(metrics_list)

            if evaluation_names is not None:
                evaluation_names_iter = evaluation_names
            else:
                evaluation_names_iter = [None] * len(metrics_list)

            for i, (metric, k, evaluation_name, attr_fields) in enumerate(
                zip(metrics_list, eval_at_iter, evaluation_names_iter, attribute_fields)
            ):
                eval_name = evaluation_name
                if eval_name is None:
                    eval_name = f'{metric}@{k}' if k is not None else metric

                actual = [match.get_attributes(*attr_fields) for match in doc.matches]
                desired = [
                    match.get_attributes(*attr_fields) for match in groundtruth.matches
                ]
                kwargs['eval_at'] = k
                evaluation = RankingEvaluationMixin.funcs[metric](
                    actual=actual, desired=desired, **kwargs
                )
                results[eval_name] += evaluation
                doc.evaluations[eval_name] = evaluation
            num += 1

        return dict(map(lambda item: (item[0], item[1] / num), results.items()))
