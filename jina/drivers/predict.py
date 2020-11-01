from typing import Iterable, List, Any

import numpy as np

from . import BaseExecutableDriver
from .helper import extract_docs

if False:
    from ..proto import jina_pb2


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
            docs: Iterable['jina_pb2.Document'],
            context_doc: 'jina_pb2.Document',
            field: str,
            *args,
            **kwargs,
    ) -> None:
        embed_vecs, docs_pts, bad_doc_ids = extract_docs(docs, embedding=True)

        if bad_doc_ids:
            self.pea.logger.warning(f'these bad docs can not be added: {bad_doc_ids}')

        if docs_pts:
            prediction = self.exec_fn(np.stack(embed_vecs))
            labels = self.prediction2label(prediction)
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
    """ Converts binary prediction into string label
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

    def prediction2label(self, prediction: 'np.ndarray') -> List[Any]:
        p = np.squeeze(prediction)
        if p.ndim > 1:
            raise ValueError(f'{self.__class__} expects prediction has ndim=1, but receiving ndim={p.ndim}')

        return [self.one_label if v else self.zero_label for v in p.astype(bool)]


class MultiClassPredictDriver(BaseLabelPredictDriver):
    pass


class MultiLabelPredictDriver(BaseLabelPredictDriver):
    pass
