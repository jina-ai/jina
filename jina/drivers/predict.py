from typing import List, Any, Union

import numpy as np

from . import BaseExecutableDriver
from ..helper import typename

if False:
    from ..types.sets import DocumentSet


class BasePredictDriver(BaseExecutableDriver):
    """Drivers inherited from this Driver will bind :meth:`predict` by default """

    def __init__(self, executor: str = None, method: str = 'predict', *args, **kwargs):
        super().__init__(executor, method, *args, **kwargs)


class BaseLabelPredictDriver(BasePredictDriver):

    def __init__(self, output_tag: str = 'prediction', *args, **kwargs):
        """

        :param output_tag: output label will be written to ``doc.tags``
        :param args:
        :param kwargs:
        """
        super().__init__(*args, **kwargs)
        self.output_tag = output_tag

    def _apply_all(
            self,
            docs: 'DocumentSet',
            *args,
            **kwargs,
    ) -> None:
        embed_vecs, docs_pts, bad_docs = docs.all_embeddings

        if bad_docs:
            self.runtime.logger.warning(f'these bad docs can not be added: {bad_docs}')

        if docs_pts:
            prediction = self.exec_fn(embed_vecs)
            labels = self.prediction2label(prediction)  # type: List[Union[str, List[str]]]
            for doc, label in zip(docs_pts, labels):
                doc.tags[self.output_tag] = label

    def prediction2label(self, prediction: 'np.ndarray') -> List[Any]:
        """ Converting ndarray prediction into list of readable labels

        .. note::
            ``len(output)`` should be the same as ``prediction.shape[0]``

        :param prediction: the float/int numpy ndarray given by :class:`BaseClassifier`
        :return: the readable label to be stored.
        """
        raise NotImplementedError


class BinaryPredictDriver(BaseLabelPredictDriver):
    """ Converts binary prediction into string label.

    This is often used with binary classifier.
    """

    def __init__(self, one_label: str = 'yes', zero_label: str = 'no', *args, **kwargs):
        """

        :param one_label: label when prediction is one
        :param zero_label: label when prediction is zero
        :param args:
        :param kwargs:
        """
        super().__init__(*args, **kwargs)
        self.one_label = one_label
        self.zero_label = zero_label

    def prediction2label(self, prediction: 'np.ndarray') -> List[str]:
        """

        :param prediction: a (B,) or (B, 1) zero one array
        :return:
        """
        p = np.squeeze(prediction)
        if p.ndim > 1:
            raise ValueError(f'{typename(self)} expects prediction has ndim=1, but receiving ndim={p.ndim}')

        return [self.one_label if v else self.zero_label for v in p.astype(bool)]


class OneHotPredictDriver(BaseLabelPredictDriver):
    """ Mapping prediction to one of the given labels

    Expect prediction to be 2dim array, zero-one valued. Each row corresponds to
    a sample, each column corresponds to a label. Each row can have only one 1.

    This is often used with multi-class classifier.
    """

    def __init__(self, labels: List[str], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.labels = labels

    def validate_labels(self, prediction: 'np.ndarray'):
        if prediction.ndim != 2:
            raise ValueError(f'{typename(self)} expects prediction has ndim=2, but receiving {prediction.ndim}')
        if prediction.shape[1] != len(self.labels):
            raise ValueError(
                f'{typename(self)} expects prediction.shape[1]==len(self.labels), but receiving {prediction.shape}')

    def prediction2label(self, prediction: 'np.ndarray') -> List[str]:
        """

        :param prediction: a (B, C) array where C is the number of classes, only one element can be one
        :return:
        """
        self.validate_labels(prediction)
        p = np.argmax(prediction, axis=1)
        return [self.labels[v] for v in p]


class MultiLabelPredictDriver(OneHotPredictDriver):
    """ Mapping prediction to a list of labels

    Expect prediction to be 2dim array, zero-one valued. Each row corresponds to
    a sample, each column corresponds to a label. Each row can have only multiple 1s.

    This is often used with multi-label classifier, where each instance can have multiple labels
    """

    def prediction2label(self, prediction: 'np.ndarray') -> List[List[str]]:
        self.validate_labels(prediction)
        return [[self.labels[int(pp)] for pp in p.nonzero()[0]] for p in prediction]


class Prediction2DocBlobDriver(BasePredictDriver):
    """ Write the prediction result directly into ``document.blob``.

    .. warning::

        This will erase the content in ``document.text`` and ``document.buffer``.
    """

    def _apply_all(
            self,
            docs: 'DocumentSet',
            *args,
            **kwargs,
    ) -> None:
        embed_vecs, docs_pts, bad_docs = docs.all_embeddings

        if bad_docs:
            self.runtime.logger.warning(f'these bad docs can not be added: {bad_docs}')

        if docs_pts:
            prediction = self.exec_fn(embed_vecs)
            for doc, pred in zip(docs_pts, prediction):
                doc.blob = pred
