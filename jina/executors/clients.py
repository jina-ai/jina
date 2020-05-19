from . import BaseExecutor
import grpc


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
        request = self.get_default_request()
        input_dict = self.get_input(data)
        return self.fill_request(request, input_dict)

    def get_input(self, data):
        raise NotImplementedError

    def get_response(self, response):
        if response.exception():
            self.logger.error('exception raised in encoding: {}'.format(response.exception))
            raise ValueError
        return self.get_output(response)

    def get_output(self, response):
        raise NotImplementedError

    def get_default_request(self):
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

    def callback(self, response):
        pass
