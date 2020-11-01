from jina.executors import BaseExecutor

if False:
    import numpy as np


class BaseClassifier(BaseExecutor):
    """
    The base class of Classifier Executor. Classifier Executor allows one to
    perform classification and regression on given input and output the predicted
    hard/soft label.

    This class should not be used directly. Subclasses should be used.
    """

    def predict(self, data: 'np.ndarray', *args, **kwargs) -> 'np.ndarray':
        """ Perform hard/soft classification on ``data``, the predicted value for each sample in X is returned.

        The output value can be zero/one, for one-hot label; or float for soft-label or regression label.
        Use the corresponding driver to interpret these labels

        The size and type of output can be one of the follows, ``B`` is ``data.shape[0]``:
            - (B,) or (B, 1); zero/one or float
            - (B, L): zero/one one-hot or soft label for L-class multi-class classification

        :param data: the input data to be classified, can be a ndim array.
            where axis=0 represents the batch size, i.e. data[0] is the first sample, data[1] is the second sample, ...
        :param args:
        :param kwargs:
        :return: the predicted value of each sample.
        """
        raise NotImplementedError
