__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Dict

import grpc

from . import BaseExecutor

if False:
    from tensorflow_serving.apis import predict_pb2
    from tensorflow_serving.apis import classification_pb2
    from tensorflow_serving.apis import regression_pb2


class BaseClientExecutor(BaseExecutor):
    """
    :class:`BaseClientExecutor` is the base class for the executors that wrap up a client to other server.

    """

    def __init__(self, host: str, port: str, timeout: int = -1, *args, **kwargs):
        """
        :param host: the host address of the server
        :param port: the host port of the server
        :param timeout: waiting time in seconds until drop the request, by default 200
        """
        super().__init__(*args, **kwargs)
        self.host = host
        self.port = port
        self.timeout = timeout if timeout >= 0 else 200


class BaseTFServingClientExecutor(BaseClientExecutor):
    """
    :class:`BaseTFServingClientExecutor` is the base class for the executors that wrap up a tf serving client. For the
        sake of generality, this implementation has the dependency on :mod:`tensorflow_serving`.

    Assuming that the tf server is running with `Predict` method, one can implement an executor with a `tfserving`
        client as following,

    .. highlight:: python
    .. code-block:: python

        class MyAwesomeTFServingClientEncoder(BaseTFServingClientExecutor, BaseEncoder):
            def encode(self, data: Any, *args, **kwargs) -> Any:
                _req = self.get_request(data)
                return self.get_response(_req)

            def get_input(self, data):
                input_1 = data[:, 0]
                input_2 = data[:, 1:]
                return {
                    'my_input_1': inpnut_1.reshape(-1, 1).astype(np.float32),
                    'my_input_2': inpnut_2.astype(np.float32)
                    }

            def get_output(self, response):
                return np.array(response.result().outputs['output_feature'].float_val)

    """

    def __init__(self, model_name: str, signature_name: str = 'serving_default', method_name: str = 'Predict',
                 *args, **kwargs):
        """
        :param model_name: the name of the tf serving model. It must match the `MODEL_NAME` parameter when starting the
            tf server.
        :param signature_name: the name of the tf serving signature. It must match the key in the `signature_def_map`
            when exporting the tf serving model.
        :param method_name: the name of the tf serving method. This parameter corresponds to the `method_name` parameter
             when building the signature map with ``build_signature_def()``. Currently, only ``Predict`` is supported.
            The other methods including ``Classify``, ``Regression`` needs users to implement the
            `_fill_classify_request` and `_fill_regression_request`, correspondingly. For the details of
            ``signature_defs``, please refer to https://www.tensorflow.org/tfx/serving/signature_defs.

        """
        super().__init__(*args, **kwargs)
        self.model_name = model_name
        self.signature_name = signature_name
        self._method_name_dict = {
            'Predict': ('predict_pb2', 'PredictRequest'),
            'Classify': ('classification_pb2', 'ClassificationRequest'),
            'Regression': ('regression_pb2', 'RegressionRequest')
        }
        if method_name not in self._method_name_dict:
            raise ValueError(f'unknown method name: {self.method_name}')
        self.method_name = method_name
        self.module_name, self.request_name = self._method_name_dict[self.method_name]

    def post_init(self):
        """
        Initialize the channel and stub for the gRPC client

        """
        self._channel = grpc.insecure_channel(f'{self.host}:{self.port}')
        from tensorflow_serving.apis import prediction_service_pb2_grpc
        self._stub = prediction_service_pb2_grpc.PredictionServiceStub(self._channel)

    def get_request(self, data):
        """
        Construct the gRPC request to the tf server.

        """
        _request = self.get_default_request()
        _data_dict = self.get_input(data)
        return self.fill_request(_request, _data_dict)

    def fill_request(self, request, input_dict):
        return getattr(self, self.method_name)(request, input_dict)

    def get_input(self, data) -> Dict:
        """
        Convert the input data into a dict with the models input feature names as the keys and the input tensors as the
            values.
        """
        raise NotImplementedError

    def get_response(self, request: 'predict_pb2.PredictRequest'):
        """
        Get the response from the tf server and postprocess the response
        """
        _response = getattr(self._stub, self.method_name).future(request, self.timeout)
        if _response.exception():
            self.logger.error(f'exception raised in encoding: {_response.exception}')
            raise ValueError
        return self.get_output(_response)

    def get_output(self, response: grpc.UnaryUnaryMultiCallable):
        """
        Postprocess the response from the tf server
        """
        raise NotImplementedError

    def get_default_request(self) -> 'predict_pb2.PredictRequest':
        """
        Construct the default gRPC request to the tf server.
        """
        request = self._get_default_request()
        request.model_spec.name = self.model_name
        request.model_spec.signature_name = self.signature_name
        return request

    def _get_default_request(self):
        import tensorflow_serving.apis
        return getattr(getattr(tensorflow_serving.apis, self.module_name), self.request_name)()

    def Predict(self, request: 'predict_pb2.PredictRequest', data_dict: Dict) -> 'predict_pb2.PredictRequest':
        """ Fill in the ``PredictRequest`` with the data dict
        """
        import tensorflow as tf
        for k, v in data_dict.items():
            request.inputs[k].CopyFrom(tf.make_tensor_proto(v))
        return request

    def Classify(self, request: 'classification_pb2.ClassificationRequest', data_dict: Dict) \
            -> 'classification_pb2.ClassificationRequest':
        """ Fill in the ``ClassificationRequest`` with the data dict
        """
        self.logger.error('building Classify request failed, _fill_classify_request() is not implemented')
        pass

    def Regression(self, request: 'regression_pb2.RegressionRequest', data_dict: Dict) \
            -> 'regression_pb2.RegressionRequest':
        """ Fill in the ``RegressionRequest`` with the data dict
        """
        self.logger.error('building Regression request failed, _fill_regression_request() is not implemented')
        pass
