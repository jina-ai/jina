from typing import List, Any, Union, Optional

import numpy as np

from . import BaseExecutableDriver, FlatRecursiveMixin, DocsExtractUpdateMixin
from ..helper import typename

if False:
    from ..types.sets import DocumentSet
    from ..types.document import Document


class BasePredictDriver(
    DocsExtractUpdateMixin, FlatRecursiveMixin, BaseExecutableDriver
):
    """Drivers inherited from :class:`BasePredictDriver` will bind :meth:`predict` by default

    :param fields: name of fields to be used to predict tags, default "embeddings"
    :param args: additional positional arguments which are just used for the parent initialization
    :param kwargs: additional key value arguments which are just used for the parent initialization
    """

    def __init__(
        self,
        executor: Optional[str] = None,
        method: str = 'predict',
        *args,
        **kwargs,
    ):
        super().__init__(executor, method, *args, **kwargs)


class BaseLabelPredictDriver(BasePredictDriver):
    """Base class of a Driver for label prediction.

    :param output_tag: output label will be written to ``doc.tags``
    :param args: additional positional arguments which are just used for the parent initialization
    :param kwargs: additional key value arguments which are just used for the parent initialization
    """

    def __init__(self, output_tag: str = 'prediction', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.output_tag = output_tag

    def update_docs(self, docs_pts: 'DocumentSet', exec_results: Any):
        """Update doc tags attribute with executor's return

        :param: docs_pts: the set of document to be updated
        :param: exec_results: the results from :meth:`exec_fn`
        """
        labels = self.prediction2label(
            exec_results
        )  # type: List[Union[str, List[str]]]
        for doc, label in zip(docs_pts, labels):
            doc.tags[self.output_tag] = label

    def prediction2label(self, prediction: 'np.ndarray') -> List[Any]:
        """Converting ndarray prediction into list of readable labels

        .. note::
            ``len(output)`` should be the same as ``prediction.shape[0]``

        :param prediction: the float/int numpy ndarray given by :class:`BaseClassifier`
        :return: the readable label to be stored.



        .. # noqa: DAR401


        .. # noqa: DAR202
        """
        raise NotImplementedError


class BinaryPredictDriver(BaseLabelPredictDriver):
    """Converts binary prediction into string label. This is often used with binary classifier.

    :param one_label: label when prediction is one
    :param zero_label: label when prediction is zero
    :param args: additional positional arguments which are just used for the parent initialization
    :param kwargs: additional key value arguments which are just used for the parent initialization
    """

    def __init__(self, one_label: str = 'yes', zero_label: str = 'no', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.one_label = one_label
        self.zero_label = zero_label

    def prediction2label(self, prediction: 'np.ndarray') -> List[str]:
        """

        :param prediction: a (B,) or (B, 1) zero one array
        :return: the labels as either ``self.one_label`` or ``self.zero_label``


        .. # noqa: DAR401
        """
        p = np.squeeze(prediction)
        if p.ndim > 1:
            raise ValueError(
                f'{typename(self)} expects prediction has ndim=1, but receiving ndim={p.ndim}'
            )

        return [self.one_label if v else self.zero_label for v in p.astype(bool)]


class OneHotPredictDriver(BaseLabelPredictDriver):
    """Mapping prediction to one of the given labels

    Expect prediction to be 2dim array, zero-one valued. Each row corresponds to
    a sample, each column corresponds to a label. Each row can have only one 1.

    This is often used with multi-class classifier.
    """

    def __init__(self, labels: List[str], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.labels = labels

    def validate_labels(self, prediction: 'np.ndarray'):
        """Validate the labels.

        :param prediction: the predictions


        .. # noqa: DAR401
        """
        if prediction.ndim != 2:
            raise ValueError(
                f'{typename(self)} expects prediction to have ndim=2, but received {prediction.ndim}'
            )
        if prediction.shape[1] != len(self.labels):
            raise ValueError(
                f'{typename(self)} expects prediction.shape[1]==len(self.labels), but received {prediction.shape}'
            )

    def prediction2label(self, prediction: 'np.ndarray') -> List[str]:
        """

        :param prediction: a (B, C) array where C is the number of classes, only one element can be one
        :return: the list of labels
        """
        self.validate_labels(prediction)
        p = np.argmax(prediction, axis=1)
        return [self.labels[v] for v in p]


class MultiLabelPredictDriver(OneHotPredictDriver):
    """Mapping prediction to a list of labels

    Expect prediction to be 2dim array, zero-one valued. Each row corresponds to
    a sample, each column corresponds to a label. Each row can have only multiple 1s.

    This is often used with multi-label classifier, where each instance can have multiple labels
    """

    def prediction2label(self, prediction: 'np.ndarray') -> List[List[str]]:
        """Transform the prediction into labels.

        :param prediction: the array of predictions
        :return: nested list of labels
        """
        self.validate_labels(prediction)
        return [[self.labels[int(pp)] for pp in p.nonzero()[0]] for p in prediction]


class Prediction2DocBlobDriver(BasePredictDriver):
    """Write the prediction result directly into ``document.blob``.

    .. warning::

        This will erase the content in ``document.text`` and ``document.buffer``.
    """

    def update_single_doc(self, doc: 'Document', exec_result: Any) -> None:
        """Update doc blob with executor's return.

        :param doc: the Document object
        :param exec_result: the single result from :meth:`exec_fn`
        """
        doc.blob = exec_result
