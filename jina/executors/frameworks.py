__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from . import BaseExecutor


class BaseFrameworkExecutor(BaseExecutor):
    """
    :class:`BaseFrameworkExecutor` is the base class for the executors using other frameworks internally, including
        `tensorflow`, `pytorch`, `onnx`, and, `paddlepaddle`.

    """
    framework = None

    def __init__(self, model_name: str = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model_name = model_name

    @property
    def device(self):
        """Set the device on which the exectuor will be running.

        ..notes:
            In the case of using GPUs, we only use the first gpu from the visible gpus. To specify which gpu to use,
            please use the environment variable `CUDA_VISIBLE_DEVICES`.
        """
        try:
            if self.framework == 'tensorflow':
                import tensorflow as tf
                cpus = tf.config.experimental.list_physical_devices(device_type='CPU')
                gpus = tf.config.experimental.list_physical_devices(device_type='GPU')
                if self.on_gpu and len(gpus) > 0:
                    cpus.append(gpus[0])
                return cpus
            elif self.framework == 'paddlepaddle':
                import paddle.fluid as fluid
                return fluid.CUDAPlace(0) if self.on_gpu else fluid.CPUPlace()
            elif self.framework == 'pytorch':
                import torch
                return torch.device('cuda:0') if self.on_gpu else torch.device('cpu')
            elif self.framework == 'onnx':
                return ['CUDAExecutionProvider'] if self.on_gpu else ['CPUExecutionProvider']
        except Exception:
            self.logger.error(f'error when setting devices "on_gpu={self.on_gpu}"')
            raise

    def to_device(self, *args, **kwargs):
        """Put the model on specified device (``on_gpu``) and returns the device context"""
        raise NotImplementedError


class BaseTorchExecutor(BaseFrameworkExecutor):
    """
    :class:`BaseTorchExecutor` implements the base class for the executors using :mod:`torch` library. The common setups
         go into this class.

    To implement your own executor with the :mod:`torch` library,

    .. highlight:: python
    .. code-block:: python

        class MyAwesomeTorchEncoder(BaseTorchExecutor):
            def post_init(self):
                # load your awesome model
                import torchvision.models as models
                self.model = models.mobilenet_v2().features.eval()
                self.to_device(self.model)

            def encode(self, data, *args, **kwargs):
                # use your awesome model to encode/craft/score
                import torch
                _input = torch.from_numpy(data)
                if self.on_gpu:
                    _input = _input.cuda()
                _output = self.model(_input).detach()
                if self.on_gpu:
                    _output = _output.cpu()
                return _output.numpy()

    """

    framework = 'pytorch'

    def to_device(self, model, *args, **kwargs):
        model.to(self.device)


class BasePaddleExecutor(BaseFrameworkExecutor):
    """
    :class:`BasePaddleExecutor` implements the base class for the executors using :mod:`paddlepaddle` library. The
        common setups go into this class.

    To implement your own executor with the :mod:`paddlepaddle` library,

    .. highlight:: python
    .. code-block:: python

        class MyAwesomePaddleEncoder(BasePaddleExecutor):
            def post_init(self):
                # load your awesome model
                import paddlehub as hub
                module = hub.Module(name='mobilenet_v2_imagenet')
                inputs, outputs, self.model = module.context(trainable=False)
                self.inputs_name = input_dict['image'].name
                self.outputs_name = output_dict['feature_map'].name
                self.exe = self.to_device()

            def encode(self, data, *args, **kwargs):
                # use your awesome model to encode/craft/score
                _output, *_ = self.exe.run(
                    program=self.model,
                    fetch_list=[self.outputs_name],
                    feed={self.inputs_name: data},
                    return_numpy=True
                )
                return feature_map
    """

    framework = 'paddlepaddle'

    def to_device(self):
        import paddle.fluid as fluid
        return fluid.Executor(self.device)


class BaseTFExecutor(BaseFrameworkExecutor):
    """
    :class:`BaseTFExecutor` implements the base class for the executors using :mod:`tensorflow` library. The common
        setups go into this class.
    To implement your own executor with the :mod:`tensorflow` library,

    .. highlight:: python
    .. code-block:: python

        class MyAwesomeTFEncoder(BaseTFExecutor):
            def post_init(self):
                # load your awesome model
                self.to_device()
                import tensorflow as tf
                model = tf.keras.applications.MobileNetV2(
                    input_shape=(self.img_shape, self.img_shape, 3),
                    include_top=False,
                    pooling=self.pool_strategy,
                    weights='imagenet')
                model.trainable = False
                self.model = model

            def encode(self, data, *args, **kwargs):
                # use your awesome model to encode/craft/score
                return self.model(data)
    """

    framework = 'tensorflow'

    def to_device(self):
        import tensorflow as tf
        tf.config.experimental.set_visible_devices(devices=self.device)


class BaseOnnxExecutor(BaseFrameworkExecutor):
    """
    :class:`BaseOnnxExecutor` implements the base class for the executors using :mod:`onnxruntime` library. The common
        setups go into this class.

    To implement your own executor with the :mod:`onnxruntime` library,

    .. highlight:: python
    .. code-block:: python

        class MyAwesomeOnnxEncoder(BaseOnnxExecutor):
            def __init__(self, output_feature, model_path, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.outputs_name = output_feature
                self.model_path = model_path

            def post_init(self):
                import onnxruntime
                self.model = onnxruntime.InferenceSession(self.model_path, None)
                self.inputs_name = self.model.get_inputs()[0].name
                self.to_device(self.model)

            def encode(self, data, *args, **kwargs):
                # use your awesome model to encode/craft/score
                results = []
                for idx in data:
                    data_encoded, *_ = self.model.run(
                        [self.outputs_name, ], {self.inputs_name: data})
                    results.append(data_encoded)
                return np.concatenate(results, axis=0)

    """
    framework = 'onnx'

    def to_device(self, model, *args, **kwargs):
        model.set_providers(self.device)
