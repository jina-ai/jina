import numpy as np
import os
from ...decorators import batching, require_train

from .. import BaseNumericEncoder

from sklearn.decomposition import PCA


class _BasePCAEncoder(BaseNumericEncoder):
    """Base class for PCA methods.

    Warning: This class should not be used directly.
    Use derived classes instead.
    """
    def __init__(self,
                 output_dim: int,
                 num_features: int = None,
                 whiten: bool = False,
                 *args,
                 **kwargs):
        """

        :param output_dim: the output size.
        :param num_features: the number of input features.  If ``num_features`` is None, then ``num_features`` is
            inferred from the data
        :param whiten: If whiten is false, the data is already considered to be whitened, and no whitening is performed.
        """
        super().__init__(*args, **kwargs)
        self.output_dim = output_dim
        self.whiten = whiten
        self.num_features = num_features
        self.is_trained = False


class IncrementalPCAEncoder(_BasePCAEncoder):
    """
    :class:`IncrementalPCAEncoder` encodes data from an ndarray in size `B x T` into an ndarray in size `B x D`.

    .. note::
        :class:`IncrementalPCAEncoder` must be trained before calling ``encode()``. This encoder can be trained in an
        incremental way.
    """
    def __init__(self,
                 output_dim: int,
                 num_features: int = None,
                 whiten: bool = False,
                 *args,
                 **kwargs):
        """

        :param output_dim: the output size.
        :param num_features: the number of input features.  If ``num_features`` is None, then ``num_features`` is
            inferred from the data
        :param whiten: If whiten is false, the data is already considered to be whitened, and no whitening is performed.
        """
        super().__init__(output_dim, num_features, whiten, *args, **kwargs)
        self.model = None

    def post_init(self):
        from sklearn.decomposition import IncrementalPCA
        if not self.model:
            self.model = IncrementalPCA(
                n_components=self.output_dim,
                whiten=self.whiten)

    @batching
    def train(self, data: 'np.ndarray', *args, **kwargs):
        num_samples, num_features = data.shape
        if not self.num_features:
            self.num_features = num_features
        if num_samples < 5 * num_features:
            self.logger.warning(
                'the batch size (={}) is suggested to be 5 * num_features(={}) to provide a balance between '
                'approximation accuracy and memory consumption.'.format(num_samples, num_features))
        self.model.partial_fit(data)
        self.is_trained = True

    @require_train
    @batching
    def encode(self, data: 'np.ndarray', *args, **kwargs) -> 'np.ndarray':
        """
        :param data: a `B x T` numpy ``ndarray``, `B` is the size of the batch
        :return: a `B x D` numpy ``ndarray``
        """
        _, num_features = data.shape
        return self.model.transform(data)


class PCAEncoder(_BasePCAEncoder):
    """
    :class:`PCAEncoder` encodes data from an ndarray in size `B x T` into an ndarray in size `B x D`.

    .. note::
        :class:`PCAEncoder` must be trained before calling ``encode()``. This encoder can NOT be trained in the batch mode.
    """
    def __init__(self,
                 output_dim: int,
                 num_features: int,
                 whiten: bool = False,
                 model_filename: str = 'pca.bin',
                 *args,
                 **kwargs):
        """

        :param output_dim: the output size.
        :param whiten: If whiten is false, the data is already considered to be whitened, and no whitening is performed.
        :param num_features: the number of input features.  If ``num_features`` is None, then ``num_features`` is
            inferred from the data
        :param encoder_abspath: the absolute saving path of the encoder. If a valid path is given, the encoder will be
            loaded from the given path.
        """
        super().__init__(output_dim, num_features, whiten, *args, **kwargs)
        self.model_filename = model_filename
        self.mean = None
        self.num_samples = None

    def __getstate__(self):
        if os.path.exists(self.model_abspath):
            self.logger.warning(
                'the existed model file will be overrided: {}'.format(self.model_abspath))
        import faiss
        faiss.write_VectorTransform(self.model, self.model_abspath)
        self.logger.info(
            'the model is saved at: {}'.format(self.model_abspath))
        return super().__getstate__()

    @staticmethod
    def _calc_std(data, n_samples):
        return np.sqrt(data ** 2 / (n_samples - 1))

    @property
    def model_abspath(self) -> str:
        return self.get_file_from_workspace(self.model_filename)

    def post_init(self):
        self.model = None
        import faiss
        if os.path.exists(self.model_abspath):
            self.model = faiss.read_VectorTransform(self.model_abspath)
            self.std = self._calc_std(
                faiss.vector_to_array(self.model.eigenvalues)[:self.output_dim], self.num_samples)
            self.logger.info('load existing model from {}'.format(self.model_abspath))
        else:
            self.model = faiss.PCAMatrix(self.num_features, self.output_dim)

    def train(self, data: 'np.ndarray', *args, **kwargs):
        import faiss
        self.num_samples, num_features = data.shape
        if not self.num_features:
            self.num_features = num_features
        self.mean = np.mean(data, axis=0)
        self.model.train((data - self.mean).astype('float32'))
        self.std = self._calc_std(faiss.vector_to_array(self.model.eigenvalues)[:self.output_dim], self.num_samples)
        self.is_trained = True

    @require_train
    @batching
    def encode(self, data: 'np.ndarray', *args, **kwargs) -> 'np.ndarray':
        """
        :param data: a `B x T` numpy ``ndarray``, `B` is the size of the batch
        :return: a `B x D` numpy ``ndarray``
        """
        output = self.model.apply_py((data - self.mean).astype('float32'))
        if self.whiten:
            output /= self.std
        return output
