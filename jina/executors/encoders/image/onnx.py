__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import os
import re

import numpy as np

from .. import BaseImageEncoder
from ...decorators import batching, as_ndarray


class OnnxImageEncoder(BaseImageEncoder):
    """
    :class:`OnnxImageEncoder` encodes data from a ndarray, potentially B x (Channel x Height x Width) into a
        ndarray of `B x D`.
    Internally, :class:`OnnxImageEncoder` wraps the models from `onnxruntime`.
    """

    def __init__(self,
                 output_feature: str = 'mobilenetv20_features_relu1_fwd',
                 model_path: str =
                 'https://s3.amazonaws.com/onnx-model-zoo/mobilenet/mobilenetv2-1.0/mobilenetv2-1.0.onnx',
                 pool_strategy: str = 'mean',
                 *args, **kwargs):
        """

        :param output_feature: the name of the layer for feature extraction.
        :param model_path: the path/URL of the model in the format of `.onnx`. Check a list of available pretrained
            models at https://github.com/onnx/models#image_classification
        :param pool_strategy: the pooling strategy
            - `None` means that the output of the model will be the 4D tensor output of the last convolutional block.
            - `mean` means that global average pooling will be applied to the output of the last convolutional block,
            and thus the output of the model will be a 2D tensor.
            - `max` means that global max pooling will be applied.
        """
        super().__init__(*args, **kwargs)
        self.pool_strategy = pool_strategy
        if pool_strategy not in ('mean', 'max', None):
            raise NotImplementedError('unknown pool_strategy: {}'.format(self.pool_strategy))
        self.outputs_name = output_feature
        self.raw_model_path = model_path
        self.model_name = ""

    def post_init(self):
        import onnxruntime
        self.model_name = self.raw_model_path.split('/')[-1]
        self.tmp_model_path = self.get_file_from_workspace(f'{self.model_name}.tmp')
        if self._is_url(self.raw_model_path):
            import urllib.request
            download_path, *_ = urllib.request.urlretrieve(self.raw_model_path)
            self.raw_model_path = download_path
            self.logger.info('download the model at {}'.format(self.raw_model_path))
        if not os.path.exists(self.tmp_model_path):
            self._append_outputs(self.raw_model_path, self.outputs_name, self.tmp_model_path)
            self.logger.info('save the model with outputs [{}] at {}'.format(self.outputs_name, self.tmp_model_path))
        self.model = onnxruntime.InferenceSession(self.tmp_model_path, None)
        self.inputs_name = self.model.get_inputs()[0].name

    @staticmethod
    def _append_outputs(input_fn, outputs_name_to_append, output_fn):
        import onnx
        model = onnx.load(input_fn)
        feature_map = onnx.helper.ValueInfoProto()
        feature_map.name = outputs_name_to_append
        model.graph.output.append(feature_map)
        onnx.save(model, output_fn)

    @batching
    @as_ndarray
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
