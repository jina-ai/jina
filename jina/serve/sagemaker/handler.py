from jina.serve.runtimes.worker.request_handling import WorkerRequestHandler
from jina.parsers import set_pod_parser
from jina.logging.logger import JinaLogger
from jina import DocumentArray
from jina.types.request.data import DataRequest
import asyncio


class JinaExecutorHandler(object):
    """
    A JinaExecutorHandler handler implementation.
    """

    def __init__(self):
        self.request_handler = None
        self.args = None

    def initialize(self, context):
        """
        Initialize Executor. This will be called during model loading time
        :param context: Initial context contains model server system properties.
        :return:
        """
        # Get args from context
        args = set_pod_parser(['--uses', 'config.yml'])
        self.request_handler = WorkerRequestHandler(args, logger=JinaLogger(self.__class__.__name__))

    def handle(self, data, context):
        """
        Call executor
        :param data: input data
        :param context: mms context
        """

        docs = data['body']
        req = DataRequest()
        req.data.docs = DocumentArray.from_pydantic_model(docs)
        req.parameters = {'a': 'get params from body o context'}
        req.header.exec_endpoint = '/endpoint_from_body_or_context'
        resp = asyncio.run(self.request_handler.handle(req))
        return resp.docs.to_dict()


_service = JinaExecutorHandler()


def handle(data, context):
    if _service.request_handler is None:
        _service.initialize(context)

    if data is None:
        return None

    return _service.handle(data, context)
