from typing import TYPE_CHECKING, AsyncIterator

from jina.helper import get_full_version
from jina.proto import jina_pb2
from jina.types.request.data import DataRequest
from jina.types.request.status import StatusMessage

if TYPE_CHECKING:  # pragma: no cover
    from types import SimpleNamespace
    from jina.types.request import Request
    from jina.logging.logger import JinaLogger


class GatewayRequestHandler:
    """Object to encapsulate the code related to handle the data requests in the Gateway"""
    def __init__(
            self,
            args: 'SimpleNamespace',
            logger: 'JinaLogger',
            **kwargs,
    ):
        import json

        from jina.serve.runtimes.gateway.streamer import GatewayStreamer, _ExecutorStreamer
        self.runtime_args = args
        self.logger = logger
        graph_description = json.loads(self.runtime_args.graph_description)
        graph_conditions = json.loads(self.runtime_args.graph_conditions)
        deployments_addresses = json.loads(self.runtime_args.deployments_addresses)
        deployments_metadata = json.loads(self.runtime_args.deployments_metadata)
        deployments_no_reduce = json.loads(self.runtime_args.deployments_no_reduce)

        self.streamer = GatewayStreamer(
            graph_representation=graph_description,
            executor_addresses=deployments_addresses,
            graph_conditions=graph_conditions,
            deployments_metadata=deployments_metadata,
            deployments_no_reduce=deployments_no_reduce,
            timeout_send=self.runtime_args.timeout_send,
            retries=self.runtime_args.retries,
            compression=self.runtime_args.compression,
            runtime_name=self.runtime_args.runtime_name,
            prefetch=self.runtime_args.prefetch,
            logger=self.logger,
            metrics_registry=self.runtime_args.metrics_registry,
            meter=self.runtime_args.meter,
            aio_tracing_client_interceptors=self.runtime_args.aio_tracing_client_interceptors,
            tracing_client_interceptor=self.runtime_args.tracing_client_interceptor,
        )
        GatewayStreamer._set_env_streamer_args(
            graph_representation=graph_description,
            executor_addresses=deployments_addresses,
            graph_conditions=graph_conditions,
            deployments_metadata=deployments_metadata,
            deployments_no_reduce=deployments_no_reduce,
            timeout_send=self.runtime_args.timeout_send,
            retries=self.runtime_args.retries,
            compression=self.runtime_args.compression,
            runtime_name=self.runtime_args.runtime_name,
            prefetch=self.runtime_args.prefetch,
        )

        self.executor = {
            executor_name: _ExecutorStreamer(
                self.streamer._connection_pool, executor_name=executor_name
            )
            for executor_name in deployments_addresses.keys()
        }

    async def dry_run(self, empty, context) -> jina_pb2.StatusProto:
        """
        Process the call requested by having a dry run call to every Executor in the graph

        :param empty: The service expects an empty protobuf message
        :param context: grpc context
        :returns: the response request
        """
        from jina._docarray import Document, DocumentArray
        from jina.serve.executors import __dry_run_endpoint__

        da = DocumentArray([Document()])
        try:
            async for _ in self.streamer.stream_docs(
                    docs=da, exec_endpoint=__dry_run_endpoint__, request_size=1
            ):
                pass
            status_message = StatusMessage()
            status_message.set_code(jina_pb2.StatusProto.SUCCESS)
            return status_message.proto
        except Exception as ex:
            status_message = StatusMessage()
            status_message.set_exception(ex)
            return status_message.proto

    async def _status(self, empty, context) -> jina_pb2.JinaInfoProto:
        """
        Process the the call requested and return the JinaInfo of the Runtime

        :param empty: The service expects an empty protobuf message
        :param context: grpc context
        :returns: the response request
        """
        info_proto = jina_pb2.JinaInfoProto()
        version, env_info = get_full_version()
        for k, v in version.items():
            info_proto.jina[k] = str(v)
        for k, v in env_info.items():
            info_proto.envs[k] = str(v)
        return info_proto

    async def stream(
            self, request_iterator, context=None, *args, **kwargs
    ) -> AsyncIterator['Request']:
        """
        stream requests from client iterator and stream responses back.

        :param request_iterator: iterator of requests
        :param context: context of the grpc call
        :param args: positional arguments
        :param kwargs: keyword arguments
        :yield: responses to the request after streaming to Executors in Flow
        """
        async for resp in self.streamer.rpc_stream(
                request_iterator=request_iterator, context=context, *args, **kwargs
        ):
            yield resp

    async def process_single_data(
            self, request: DataRequest, context=None
    ) -> DataRequest:
        """Implements request and response handling of a single DataRequest
        :param request: DataRequest from Client
        :param context: grpc context
        :return: response DataRequest
        """
        return await self.streamer.process_single_data(request, context)

    Call = stream
