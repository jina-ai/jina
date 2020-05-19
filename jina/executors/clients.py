from . import BaseExecutor
import grpc
from typing import Dict


class BaseClientExecutor(BaseExecutor):
    """
    :class:`BaseClientExecutor` is the base class for the executors that wrap up a client to other server.

    """
    def __init__(self, host=None, port=None, timeout=-1, *args, **kwargs):
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

    To implement your own executor with `tfserving`,

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
    def __init__(self, service_name, signature_name='serving_default', *args, **kwargs):
        """
        :param service_name: the name of the tf serving service
        :param signature_name: the name of the tf serving signature

        """
        super().__init__(*args, **kwargs)
        self.service_name = service_name
        self.signature_name = signature_name

    def post_init(self):
        """
        Initialize the channel and stub for the gRPC client

        """
        from tensorflow_serving.apis import prediction_service_pb2_grpc
        self._channel = grpc.insecure_channel('{}:{}'.format(self.host, self.port))
        self._stub = prediction_service_pb2_grpc.PredictionServiceStub(self._channel)

    def get_request(self, data):
        """
        Construct the gRPC request to the tf server.

        """
        request = self.get_default_request()
        input_dict = self.get_input(data)
        return self.fill_request(request, input_dict)

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
        _response = self._stub.Predict.future(request, self.timeout)
        if _response.exception():
            self.logger.error('exception raised in encoding: {}'.format(_response.exception))
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
        from tensorflow_serving.apis import predict_pb2
        request = predict_pb2.PredictRequest()
        request.model_spec.name = self.service_name
        request.model_spec.signature_name = self.signature_name
        return request

    @staticmethod
    def fill_request(request, data_dict):
        import tensorflow as tf
        for k, v in data_dict.items():
            request.inputs[k].CopyFrom(tf.make_tensor_proto(v))
        return request
