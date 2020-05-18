from . import BaseExecutor
import grpc


class BaseClientExecutor(BaseExecutor):
    def __init__(self, host=None, port=None, timeout=-1, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.host = host
        self.port = port
        self.timeout = timeout if timeout >= 0 else 200


class TFServingClientExecutor(BaseClientExecutor):
    def __init__(self, name, input_name, output_name, signature_name='serving_default', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = name
        self.input_name = input_name
        self.output_name = output_name
        self.signature_name = signature_name

    def post_init(self):
        from tensorflow_serving.apis import prediction_service_pb2_grpc
        self._channel = grpc.insecure_channel('{}:{}'.format(self.host, self.port))
        self._stub = prediction_service_pb2_grpc.PredictionServiceStub(self._channel)

    def get_request(self, data_dict):
        request = self.get_default_request()
        return self.fill_request(request, data_dict)

    def get_default_request(self):
        from tensorflow_serving.apis import predict_pb2
        request = predict_pb2.PredictRequest()
        request.model_spec.name = self.name
        request.model_spec.signature_name = self.signature_name
        return request

    def fill_request(self, request, data_dict):
        import tensorflow as tf
        for k, v in data_dict.items():
            request.inputs[k].CopyFrom(tf.make_tensor_proto(v))
        return request

    def callback(self, response):
        pass
