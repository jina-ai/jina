import numpy as np
import os
from ...decorators import batching, require_train

from .. import BaseNumericEncoder

from sklearn.decomposition import PCA

class IncrementalPCAEncoder(BaseNumericEncoder):
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
                 save_path: str = '',
                 *args,
                 **kwargs):
        """

        :param output_dim: the output size.
        :param num_features: the number of input features.  If ``num_features`` is None, then ``num_features`` is
            inferred from the data
        :param whiten: If whiten is false, the data is already considered to be whitened, and no whitening is performed.
        :param encoder_abspath: the absolute saving path of the encoder. If a valid path is given, the encoder will be
            loaded from the given path.
        """
        super().__init__(*args, **kwargs)
        self.output_dim = output_dim
        self.whiten = whiten
        self.num_features = num_features
        self.encoder_abspath = save_path
        self.is_trained = False

    def post_init(self):
        from sklearn.decomposition import IncrementalPCA
        if os.path.exists(self.encoder_abspath):
            import pickle
            with open(self.encoder_abspath, 'rb') as f:
                self.model = pickle.load(f)
            self.logger.info('load existing model from {}'.format(self.encoder_abspath))
        else:
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

    def __getstate__(self):
        if not self.encoder_abspath:
            self.encoder_abspath = os.path.join(self.current_workspace, "pca.bin")
        if os.path.exists(self.encoder_abspath):
            self.logger.warning(
                'the existed model file will be overrided: {}".format(save_path)')
        import pickle
        with open(self.encoder_abspath, 'wb') as f:
            pickle.dump(self.model, f)
        self.logger.info(
            'the model is saved at: {}'.format(self.encoder_abspath))
        return super().__getstate__()


class PCAEncoder(BaseNumericEncoder):
    """
    :class:`PCAEncoder` encodes data from an ndarray in size `B x T` into an ndarray in size `B x D`.

    .. note::
        :class:`PCAEncoder` must be trained before calling ``encode()``. This encoder can NOT be trained in the batch mode.
    """
    def __init__(self,
                 output_dim: int,
                 num_features: int,
                 whiten: bool = False,
                 save_path: str = '',
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
        super().__init__(*args, **kwargs)
        self.output_dim = output_dim
        self.whiten = whiten
        self.num_features = num_features
        self.encoder_abspath = save_path
        self.is_trained = False
        self.mean = None
        self._num_samples = None

    def __getstate__(self):
        if not self.encoder_abspath:
            self.encoder_abspath = os.path.join(self.current_workspace, "pca.bin")
        if os.path.exists(self.encoder_abspath):
            self.logger.warning(
                'the existed model file will be overrided: {}".format(save_path)')
        import faiss
        faiss.write_VectorTransform(self.model, self.encoder_abspath)
        self.logger.info(
            'the model is saved at: {}'.format(self.encoder_abspath))
        return super().__getstate__()

    @staticmethod
    def _calc_std(data, n_samples):
        return np.sqrt(data ** 2 / (n_samples - 1))


    def post_init(self):
        self.model = None
        import faiss
        if os.path.exists(self.encoder_abspath):
            self.model = faiss.read_VectorTransform(self.encoder_abspath)
            self.std = self._calc_std(
                faiss.vector_to_array(self.model.eigenvalues)[:self.output_dim], self._num_samples)
            self.logger.info('load existing model from {}'.format(self.encoder_abspath))
        else:
            self.model = faiss.PCAMatrix(self.num_features, self.output_dim)

    def train(self, data: 'np.ndarray', *args, **kwargs):
        import faiss
        self._num_samples, num_features = data.shape
        if not self.num_features:
            self.num_features = num_features
        self.mean = np.mean(data, axis=0)
        self.model.train((data - self.mean).astype('float32'))
        self.std = self._calc_std(faiss.vector_to_array(self.model.eigenvalues)[:self.output_dim], self._num_samples)
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
