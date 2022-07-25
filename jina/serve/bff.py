from typing import Optional, Dict

from jina.serve.runtimes.gateway.graph.topology_graph import TopologyGraph
from jina.serve.networking import GrpcConnectionPool

from jina.logging.logger import JinaLogger
from jina.serve.runtimes.gateway.request_handling import RequestHandler
from jina.serve.stream import RequestStreamer

from docarray import DocumentArray

__all__ = ['GatewayBFF']


class GatewayBFF:
    """
    Wrapper object to be used in a BFF or in the Gateway. Naming to be defined
    """

    def __init__(
            self,
            graph_representation,
            executor_addresses,
            graph_conditions,
            deployments_disable_reduce,
            timeout_send,
            retries,
            compression,
            runtime_name='bff',
            prefetch: int = 0,
            logger: Optional['JinaLogger'] = None,
            metrics_registry=None,
    ):
        """
        :param graph_representation: Graph representation of the Flow
        :param executor_addresses: Addresses of the Executors
        :param logger: Optional logger that can be used for logging
        """
        self._timeout_send = timeout_send
        self._retries = retries
        self.logger = logger
        self._metrics_registry = metrics_registry
        self._topology_graph = self._create_topology_graph(graph_representation, graph_conditions,
                                                           deployments_disable_reduce)
        self._connection_pool = self._create_connection_pool(executor_addresses, compression)
        request_handler = RequestHandler(metrics_registry, runtime_name)

        self._streamer = RequestStreamer(
            request_handler=request_handler.handle_request(
                graph=self._topology_graph, connection_pool=self._connection_pool
            ),
            result_handler=request_handler.handle_result(),
            prefetch=prefetch,
            logger=self.logger,
        )
        self._streamer.Call = self._streamer.stream

    def _create_topology_graph(self, graph_description, graph_conditions, deployments_disable_reduce):
        # check if it should be in K8s, maybe ConnectionPoolFactory to be created
        import json

        graph_description = json.loads(graph_description)
        graph_conditions = json.loads(graph_conditions)
        deployments_disable_reduce = json.loads(deployments_disable_reduce)
        return TopologyGraph(
            graph_description,
            graph_conditions,
            deployments_disable_reduce,
            timeout_send=self._timeout_send,
            retries=self._retries,
        )

    def _create_connection_pool(self, deployments_addresses, compression):
        import json

        deployments_addresses = json.loads(deployments_addresses)
        # add the connections needed
        connection_pool = GrpcConnectionPool(
            logger=self.logger,
            compression=compression,
            metrics_registry=self._metrics_registry,
        )
        for deployment_name, addresses in deployments_addresses.items():
            for address in addresses:
                connection_pool.add_connection(
                    deployment=deployment_name, address=address, head=True
                )

        return connection_pool

    def stream(self, *args, **kwargs):
        return self._streamer.stream(*args, **kwargs)

    def stream_docs(self, da: DocumentArray, exec_endpoint: str, request_size: int, target_executor: Optional[str] = None, parameters: Optional[Dict] = None, *args, **kwargs):
        from jina.clients.request import request_generator # move request_generator to another module
        from jina.enums import DataInputType
        return self._streamer.stream(request_generator(data=da, data_type=DataInputType.DOCUMENT, exec_endpoint=exec_endpoint, request_size=request_size, target_executor=target_executor, parameters=parameters))

    async def close(self):
        await self._streamer.wait_floating_requests_end()
        await self._connection_pool.close()

    Call = stream
