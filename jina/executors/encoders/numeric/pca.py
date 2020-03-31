import numpy as np
import os
from ...decorators import batching, require_train

from .. import BaseNumericEncoder


class IncrementalPCAEncoder(BaseNumericEncoder):
    """
    :class:`IncrementalPCAEncoder` encodes data from an ndarray in size `B x T` into an ndarray in size `B x D`.

    .. note::
        :class:`IncrementalPCAEncoder` must be trained before calling ``encode()``. This encoder can be trained in an
        incremental way.
    """
    def __init__(self,
                 output_dim: int,
                 whiten: bool = False,
                 num_features: int = None,
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
        self._check_num_features(num_features)
        if num_samples < 5 * num_features:
            self.logger.warning(
                'the batch size (={}) is suggested to be 5 * num_features(={}) to provide a balance between '
                'approximation accuracy and memory consumption.'.format(num_samples, num_features))
        self.model.partial_fit(data)
        self.is_trained = True

    @require_train
    @batching
    def encode(self, data: 'np.ndarray', *args, **kwargs) -> 'np.ndarray':
        _, num_features = data.shape
        self._check_num_features(num_features)
        return self.model.transform(data)

    def _check_num_features(self, num_features):
        if self.num_features != num_features:
            raise ValueError(
                'the number of features must be consistent. ({} != {})'.format(num_features, self.num_features)
            )

    def __getstate__(self):
        if not self.encoder_abspath:
            self.encoder_abspath = os.path.join(self.current_workspace, "pca.bin")
        if os.path.exists(self.encoder_abspath):
            self.logger.warning(
                'the existed model file will be overrided: {}".format(save_path)')
        self.logger.info(
            'the model is saved at: {}'.format(self.encoder_abspath))
        import pickle
        with open(self.encoder_abspath, 'wb') as f:
            pickle.dump(self.model, f)
        return super().__getstate__()

