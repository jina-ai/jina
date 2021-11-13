import warnings
from typing import Optional, Union, TYPE_CHECKING, Callable

import numpy as np

if TYPE_CHECKING:
    from ...document import Document


class EvaluationMixin:
    """ A mixin that provides ranking evaluation functionality to DocumentArrayLike objects"""

    def evaluate(
        self,
        other,
        metric: Union[str, Callable[..., float]],
        hash_fn: Optional[Callable[['Document'], str]] = None,
        metric_name: Optional[str] = None,
        **kwargs,
    ) -> float:
        """Compute ranking evaluation metrics for a given `DocumentArray` when compared with a groundtruth.

        This implementation expects to provide a `groundtruth` DocumentArray that is structurally identical to `self`. It is based
        on comparing the `matches` of `documents` inside the `DocumentArray.

        This method will fill the `evaluations` field of Documents inside this `DocumentArray` and will return the average of the computations

        :param other: The groundtruth DocumentArray` that the `DocumentArray` compares to.
        :param metric: The name of the metric, or multiple metrics to be computed
        :param hash_fn: The function used for identifying the uniqueness of Documents. If not given, then ``Document.id`` is used.
        :param metric_name: If provided, the results of the metrics computation will be stored in the `evaluations` field of each Document. If not provided, the name will be computed based on the metrics name.

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

        if hash_fn is None:
            hash_fn = lambda d: d.id

        if callable(metric):
            metric_fn = metric
        elif isinstance(metric, str):
            from ....math import evaluation

            metric_fn = getattr(evaluation, metric)

        metric_name = metric_name or metric_fn.__name__
        results = []
        for d, gd in zip(self, other):
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
