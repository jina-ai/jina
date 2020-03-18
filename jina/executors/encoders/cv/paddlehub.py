import os
import numpy as np

from .. import BaseImageEncoder


class XCeptionPaddleImageEncoder(BaseImageEncoder):
    def __init__(self, model_name='xception71_imagenet', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model_name = model_name
        self.dim = 2048

    def post_init(self):
        import paddlehub as hub
        import paddle.fluid as fluid
        module = hub.Module(name=self.model_name)
        self.inputs, self.outputs, self.model = module.context(trainable=False)
        place = fluid.CUDAPlace(int(os.getenv('FLAGS_selected_gpus', '0'))) if self.on_gpu else fluid.CPUPlace()
        self.exe = fluid.Executor(place)

    def encode(self, data: 'np.ndarray', *args, **kwargs) -> 'np.ndarray':
        feature_map, *_ = self.exe.run(
            program=self.model,
            fetch_list=[self.outputs["feature_map"].name],
            feed={self.inputs["image"].name: data.astype('float32')},
            return_numpy=False
        )
        return np.array(feature_map).squeeze()

    def close(self):
        self.exe.close()
