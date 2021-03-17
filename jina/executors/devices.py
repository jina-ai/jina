__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from abc import abstractmethod

from ..helper import cached_property


class BaseDevice:
    """:class:`BaseFrameworkExecutor` is the base class for the executors using other frameworks internally, including `tensorflow`, `pytorch`, `onnx`, `faiss` and `paddlepaddle`."""

    @cached_property
    @abstractmethod
    def device(self):
        """
        Set the device on which the executor will be running.

        ..notes:
            In the case of using GPUs, we only use the first gpu from the visible gpus. To specify which gpu to use,
            please use the environment variable `CUDA_VISIBLE_DEVICES`.
        """

    @abstractmethod
    def to_device(self, *args, **kwargs):
        """Move the computation from GPU to CPU or vice versa."""


class TorchDevice(BaseDevice):
    """
    :class:`BaseTorchDeviceHandler` implements the base class for the executors using :mod:`torch` library. The common setups go into this class.

    To implement your own executor with the :mod:`torch` library,

    .. highlight:: python
    .. code-block:: python

        class MyAwesomeTorchEncoder(BaseEncoder, BaseTorchDeviceHandler):
            def post_init(self):
                # load your awesome model
                import torchvision.models as models
                self.model = models.mobilenet_v2().features.eval()
                self.to_device(self.model)

            def encode(self, data, *args, **kwargs):
                # use your awesome model to encode/craft/score
                import torch
                torch.set_grad_enabled(False)

                _input = torch.as_tensor(data, device=self.device)
                _output = self.model(_input).cpu()

                return _output.numpy()

    """

    @cached_property
    def device(self):
        """
        Set the device on which the executors using :mod:`torch` library will be running.

        ..notes:
            In the case of using GPUs, we only use the first gpu from the visible gpus. To specify which gpu to use,
            please use the environment variable `CUDA_VISIBLE_DEVICES`.
        """
        import torch

        return torch.device('cuda:0') if self.on_gpu else torch.device('cpu')

    def to_device(self, model, *args, **kwargs):
        """Load the model to device."""
        model.to(self.device)


class PaddleDevice(BaseDevice):
    """
    :class:`BasePaddleExecutor` implements the base class for the executors using :mod:`paddlepaddle` library. The common setups go into this class.

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

    @cached_property
    def device(self):
        """
        Set the device on which the executors using :mod:`paddlepaddle` library will be running.

        ..notes:
            In the case of using GPUs, we only use the first gpu from the visible gpus. To specify which gpu to use,
            please use the environment variable `CUDA_VISIBLE_DEVICES`.
        """
        import paddle.fluid as fluid

        return fluid.CUDAPlace(0) if self.on_gpu else fluid.CPUPlace()

    def to_device(self):
        """Load the model to device."""
        import paddle.fluid as fluid

        return fluid.Executor(self.device)


class TFDevice(BaseDevice):
    """
    :class:`BaseTFDeviceHandler` implements the base class for the executors using :mod:`tensorflow` library. The common setups go into this class.

    To implement your own executor with the :mod:`tensorflow` library,

    .. highlight:: python
    .. code-block:: python

        class MyAwesomeTFEncoder(BaseTFDeviceHandler):
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

    @cached_property
    def device(self):
        """
        Set the device on which the executors using :mod:`tensorflow` library will be running.

        ..notes:
            In the case of using GPUs, we only use the first gpu from the visible gpus. To specify which gpu to use,
            please use the environment variable `CUDA_VISIBLE_DEVICES`.
        """
        import tensorflow as tf

        cpus = tf.config.experimental.list_physical_devices(device_type='CPU')
        gpus = tf.config.experimental.list_physical_devices(device_type='GPU')
        if self.on_gpu and len(gpus) > 0:
            cpus.append(gpus[0])
        return cpus

    def to_device(self):
        """Load the model to device."""
        import tensorflow as tf

        tf.config.experimental.set_visible_devices(devices=self.device)


class OnnxDevice(BaseDevice):
    """
    :class:`OnnxDevice` implements the base class for the executors using :mod:`onnxruntime` library. The common setups go into this class.

    To implement your own executor with the :mod:`onnxruntime` library,

    .. highlight:: python
    .. code-block:: python

        class MyAwesomeOnnxEncoder(BaseOnnxDeviceHandler):
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

    @cached_property
    def device(self):
        """
        Set the device on which the executors using :mod:`onnxruntime` library will be running.

        ..notes:
            In the case of using GPUs, we only use the first gpu from the visible gpus. To specify which gpu to use,
            please use the environment variable `CUDA_VISIBLE_DEVICES`.
        """
        return ['CUDAExecutionProvider'] if self.on_gpu else ['CPUExecutionProvider']

    def to_device(self, model, *args, **kwargs):
        """Load the model to device."""
        model.set_providers(self.device)


class FaissDevice(BaseDevice):
    """:class:`FaissDevice` implements the base class for the executors using :mod:`faiss` library. The common setups go into this class."""

    @cached_property
    def device(self):
        """
        Set the device on which the executors using :mod:`faiss` library will be running.

        ..notes:
            In the case of using GPUs, we only use the first gpu from the visible gpus. To specify which gpu to use,
            please use the environment variable `CUDA_VISIBLE_DEVICES`.
        """
        import faiss

        # For now, consider only one GPU, do not distribute the index
        return faiss.StandardGpuResources() if self.on_gpu else None

    def to_device(self, index, *args, **kwargs):
        """Load the model to device."""
        import faiss

        device = self.device
        return (
            faiss.index_cpu_to_gpu(device, 0, index, None)
            if device is not None
            else index
        )


class MindsporeDevice(BaseDevice):
    """:class:`MindsporeDevice` implements the base classes for the executors using :mod:`mindspore` library. The common setups go into this class."""

    @cached_property
    def device(self):
        """
        Set the device on which the executors using :mod:`mindspore` library will be running.

        ..notes:
            In the case of using GPUs, we only use the first gpu from the visible gpus. To specify which gpu to use,
            please use the environment variable `CUDA_VISIBLE_DEVICES`.
        """
        return 'GPU' if self.on_gpu else 'CPU'

    def to_device(self):
        """Load the model to device."""
        import mindspore.context as context

        context.set_context(mode=context.GRAPH_MODE, device_target=self.device)
