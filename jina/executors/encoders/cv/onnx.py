import os
import numpy as np

import re
from .. import BaseImageEncoder


class OnnxImageEncoder(BaseImageEncoder):
    """
    :class:`OnnxImageEncoder` encodes data from a ndarray, potentially B x (Channel x Height x Width) into a
        ndarray of `B x D`.
    Internally, :class:`OnnxImageEncoder` wraps the models from `onnxruntime`.
    """
    def __init__(self,
                 model_name: str = 'mobilenetv2-1.0',
                 output_feature: str = 'mobilenetv20_features_relu1_fwd',
                 model_fn: str = 'https://s3.amazonaws.com/onnx-model-zoo/mobilenet/mobilenetv2-1.0/mobilenetv2-1.0.onnx',
                 pool_strategy: str = 'mean',
                 *args, **kwargs):
        """

        :param model_name: the name of the model. Supported models are listed at
            https://github.com/onnx/models#image_classification
        :param output_feature: the name of the layer for feature extraction.
        :param model_fn: the path/URL of the model in the format of `.onnx`.
        :param pool_strategy: the pooling strategy
            - `None` means that the output of the model will be the 4D tensor output of the last convolutional block.
            - `mean` means that global average pooling will be applied to the output of the last convolutional block, and
                thus the output of the model will be a 2D tensor.
            - `max` means that global max pooling will be applied.
        """
        super().__init__(*args, **kwargs)
        self.model_name = model_name
        self.pool_strategy = pool_strategy
        self.model_folder = 'onnx'
        if pool_strategy not in ('mean', 'max', None):
            raise NotImplementedError('unknown pool_strategy: {}'.format(self.pool_strategy))
        self.outputs_name = output_feature
        self.model_url = None
        self.raw_model_fn = None
        if self._is_url(model_fn):
            self.model_url = model_fn
        elif os.path.exists(model_fn):
            self.raw_model_fn = model_fn
        else:
            raise ValueError('invalid model_fn: {}'.format(model_fn))

    def post_init(self):
        import onnx
        import onnxruntime
        import urllib.request
        tmp_folder = os.path.join(self.current_workspace, self.model_folder)
        if not os.path.exists(tmp_folder):
            os.mkdir(tmp_folder)
        if self.raw_model_fn is None:
            self.raw_model_fn = os.path.join(tmp_folder, '{}.raw'.format(self.model_name))
        self.model_fn = os.path.join(tmp_folder, '{}.onnx'.format(self.model_name))
        if not os.path.exists(self.model_fn):
            if self.model_url is not None and not os.path.exists(self.raw_model_fn):
                urllib.request.urlretrieve(self.model_url, filename=self.raw_model_fn)
            model = onnx.load(self.raw_model_fn)
            feature_map = onnx.helper.ValueInfoProto()
            feature_map.name = self.outputs_name
            model.graph.output.append(feature_map)
            onnx.save(model, self.model_fn)
        self.model = onnxruntime.InferenceSession(self.model_fn, None)
        self.inputs_name = self.model.get_inputs()[0].name

    def encode(self, data: 'np.ndarray', *args, **kwargs) -> 'np.ndarray':
        """

        :param data: a `B x (Channel x Height x Width)` numpy ``ndarray``, `B` is the size of the batch
        :return: a `B x D` numpy ``ndarray``, `D` is the output dimension
        """
        results = []
        for idx in range(data.shape[0]):
            img = np.expand_dims(data[idx, :, :, :], axis=0).astype('float32')
            data_encoded, *_ = self.model.run([self.outputs_name, ], {self.inputs_name: img})
            results.append(data_encoded)
        feature_map = np.concatenate(results, axis=0)
        if feature_map.ndim == 2 or self.pool_strategy is None:
            return feature_map
        return getattr(np, self.pool_strategy)(feature_map, axis=(2, 3))

    @staticmethod
    def _is_url(text):
        url_pat = re.compile(
            r'^(?:http|ftp)s?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return url_pat.match(text) is not None

