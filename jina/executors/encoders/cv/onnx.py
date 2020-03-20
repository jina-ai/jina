import os
import numpy as np

from .. import BaseImageEncoder


class OnnxImageEncoder(BaseImageEncoder):
    def __init__(self, model_name: str = 'mobilenetv2-1.0', pool_strategy: str = 'mean', *args, **kwargs):
        super().__init__(*args, **kwargs)
        model_dict = {
            'mobilenetv2-1.0': (
                'mobilenetv20_features_relu1_fwd',
                'https://s3.amazonaws.com/onnx-model-zoo/mobilenet/mobilenetv2-1.0/mobilenetv2-1.0.onnx'),
            'squeezenet1.1': (
                'squeezenet0_relu25_fwd',
                'https://s3.amazonaws.com/onnx-model-zoo/squeezenet/squeezenet1.1/squeezenet1.1.onnx')
            # 'shufflenet_v2': (
            #   'squeezenet0_relu25_fwd',
            #   'https://github.com/onnx/models/blob/master/vision/classification/shufflenet_v2/model/model.onnx')
        }
        self.model_name = model_name
        if self.model_name not in model_dict:
            raise NotImplementedError('unknown model: {}. supported models include: {}'.format(
                self.model_name, ','.join(model_dict.keys())))
        self.pool_strategy = pool_strategy
        self.model_folder = 'onnx'
        if pool_strategy not in ('mean', 'max', None):
            raise NotImplementedError('unknown pool_strategy: {}'.format(self.pool_strategy))
        self.outputs_name, self.model_url = model_dict.get(self.model_name)

    def post_init(self):
        import onnx
        import onnxruntime
        import urllib.request
        tmp_folder = os.path.join(self.current_workspace, self.model_folder)
        if not os.path.exists(tmp_folder):
            os.mkdir(tmp_folder)
        self.raw_model_fn = os.path.join(tmp_folder, '{}.raw'.format(self.model_name))
        self.model_fn = os.path.join(tmp_folder, '{}.onnx'.format(self.model_name))
        if not os.path.exists(self.model_fn):
            if not os.path.exists(self.raw_model_fn):
                urllib.request.urlretrieve(self.model_url, filename=self.raw_model_fn)
            model = onnx.load(self.raw_model_fn)
            feature_map = onnx.helper.ValueInfoProto()
            feature_map.name = self.outputs_name
            model.graph.output.append(feature_map)
            onnx.save(model, self.model_fn)
        self.model = onnxruntime.InferenceSession(self.model_fn, None)
        self.inputs_name = self.model.get_inputs()[0].name

    def encode(self, data: 'np.ndarray', *args, **kwargs) -> 'np.ndarray':
        results = []
        for idx in range(data.shape[0]):
            img = np.expand_dims(data[idx, :, :, :], axis=0).astype('float32')
            data_encoded, *_ = self.model.run([self.outputs_name, ], {self.inputs_name: img})
            results.append(data_encoded)
        feature_map = np.concatenate(results, axis=0)
        if feature_map.ndim == 2 or self.pool_strategy is None:
            return feature_map
        return getattr(np, self.pool_strategy)(feature_map, axis=(2, 3))



