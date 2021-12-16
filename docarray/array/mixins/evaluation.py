import warnings
from typing import Optional, Union, TYPE_CHECKING, Callable

import numpy as np

if TYPE_CHECKING:
    from ... import Document, DocumentArray, DocumentArrayMemmap


class EvaluationMixin:
    """A mixin that provides ranking evaluation functionality to DocumentArrayLike objects"""

    def evaluate(
        self,
        other: Union['DocumentArray', 'DocumentArrayMemmap'],
        metric: Union[str, Callable[..., float]],
        hash_fn: Optional[Callable[['Document'], str]] = None,
        metric_name: Optional[str] = None,
        strict: bool = True,
        **kwargs,
    ) -> Optional[float]:
        """Compute ranking evaluation metrics for a given `DocumentArray` when compared with a groundtruth.

        This implementation expects to provide a `groundtruth` DocumentArray that is structurally identical to `self`. It is based
        on comparing the `matches` of `documents` inside the `DocumentArray.

        This method will fill the `evaluations` field of Documents inside this `DocumentArray` and will return the average of the computations

        :param other: The groundtruth DocumentArray` that the `DocumentArray` compares to.
        :param metric: The name of the metric, or multiple metrics to be computed
        :param hash_fn: The function used for identifying the uniqueness of Documents. If not given, then ``Document.id`` is used.
        :param metric_name: If provided, the results of the metrics computation will be stored in the `evaluations` field of each Document. If not provided, the name will be computed based on the metrics name.
        :param strict: If set, then left and right sides are required to be fully aligned: on the length, and on the semantic of length. These are preventing
            you to evaluate on irrelevant matches accidentally.
        :param kwargs: Additional keyword arguments to be passed to `metric_fn`
        :return: The average evaluation computed or a list of them if multiple metrics are required
        """
        if strict:
            self._check_length(len(other))

        if hash_fn is None:
            hash_fn = lambda d: d.id

        if callable(metric):
            metric_fn = metric
        elif isinstance(metric, str):
            from ...math import evaluation

            metric_fn = getattr(evaluation, metric)

        metric_name = metric_name or metric_fn.__name__
        results = []
        for d, gd in zip(self, other):
            if not strict or hash_fn(d) != hash_fn(gd):
                raise ValueError(
                    f'Document {d} from the left-hand side and '
                    f'{gd} from the right-hand are not hashed to the same value. '
                    f'This means your left and right DocumentArray may not be aligned; or it means your '
                    f'`hash_fn` is badly designed.'
                )
            if not d.matches or not gd.matches:
                raise ValueError(
                    f'Document {d!r} or {gd!r} has no matches, please check your Document'
                )

            desired = {hash_fn(m) for m in gd.matches}
            if len(desired) != len(gd.matches):
                warnings.warn(
                    f'{hash_fn!r} may not be valid, as it maps multiple Documents into the same hash. '
                    f'Evaluation results may be affected'
                )

            binary_relevance = [1 if hash_fn(m) in desired else 0 for m in d.matches]

            r = metric_fn(binary_relevance, **kwargs)
            d.evaluations[metric_name] = r
            results.append(r)
        if results:
            return float(np.mean(results))
