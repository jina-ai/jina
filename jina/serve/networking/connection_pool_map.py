import os
from typing import TYPE_CHECKING, Dict, List, Optional, Sequence

from jina.logging.logger import JinaLogger
from jina.serve.networking.instrumentation import (
    _NetworkingHistograms,
    _NetworkingMetrics,
)
from jina.serve.networking.replica_list import _ReplicaList

if TYPE_CHECKING:  # pragma: no cover

    from grpc.aio._interceptor import ClientInterceptor
    from opentelemetry.instrumentation.grpc._client import (
        OpenTelemetryClientInterceptor,
    )


class _ConnectionPoolMap:
    def __init__(
        self,
        runtime_name: str,
        logger: Optional[JinaLogger],
        metrics: _NetworkingMetrics,
        histograms: _NetworkingHistograms,
        aio_tracing_client_interceptors: Optional[Sequence['ClientInterceptor']] = None,
        tracing_client_interceptor: Optional['OpenTelemetryClientInterceptor'] = None,
    ):
        self._logger = logger
        # this maps deployments to shards or heads
        self._deployments: Dict[str, Dict[str, Dict[int, _ReplicaList]]] = {}
        # dict stores last entity id used for a particular deployment, used for round robin
        self._access_count: Dict[str, int] = {}
        self._metrics = metrics
        self._histograms = histograms
        self.runtime_name = runtime_name
        if os.name != 'nt':
            os.unsetenv('http_proxy')
            os.unsetenv('https_proxy')
        self.aio_tracing_client_interceptors = aio_tracing_client_interceptors
        self.tracing_client_interceptor = tracing_client_interceptor

    def add_replica(self, deployment: str, shard_id: int, address: str):
        self._add_connection(deployment, shard_id, address, 'shards')

    def add_head(
        self, deployment: str, address: str, head_id: Optional[int] = 0
    ):  # the head_id is always 0 for now, this will change when scaling the head
        self._add_connection(deployment, head_id, address, 'heads')

    def get_replicas(
        self,
        deployment: str,
        head: bool,
        entity_id: Optional[int] = None,
        increase_access_count: bool = True,
    ) -> Optional[_ReplicaList]:
        # returns all replicas of a given deployment, using a given shard
        if deployment in self._deployments:
            type_ = 'heads' if head else 'shards'
            if entity_id is None and head:
                entity_id = 0
            return self._get_connection_list(
                deployment, type_, entity_id, increase_access_count
            )
        else:
            self._logger.debug(
                f'Unknown deployment {deployment}, no replicas available'
            )
            return None

    def get_replicas_all_shards(self, deployment: str) -> List[_ReplicaList]:
        # returns all replicas of a given deployment, for all available shards
        # result is a list of 'shape' (num_shards, num_replicas), containing all replicas for all shards
        replicas = []
        if deployment in self._deployments:
            for shard_id in self._deployments[deployment]['shards']:
                replicas.append(
                    self._get_connection_list(deployment, 'shards', shard_id)
                )
        return replicas

    async def close(self):
        # Close all connections to all replicas
        for deployment in self._deployments:
            for entity_type in self._deployments[deployment]:
                for shard_in in self._deployments[deployment][entity_type]:
                    await self._deployments[deployment][entity_type][shard_in].close()
        self._deployments.clear()

    def _get_connection_list(
        self,
        deployment: str,
        type_: str,
        entity_id: Optional[int] = None,
        increase_access_count: bool = True,
    ) -> Optional[_ReplicaList]:
        try:
            if entity_id is None and len(self._deployments[deployment][type_]) > 0:
                # select a random entity
                if increase_access_count:
                    self._access_count[deployment] += 1
                return self._deployments[deployment][type_][
                    self._access_count[deployment]
                    % len(self._deployments[deployment][type_])
                ]
            else:
                return self._deployments[deployment][type_][entity_id]
        except KeyError:
            if (
                entity_id is None
                and deployment in self._deployments
                and len(self._deployments[deployment][type_])
            ):
                # This can happen as a race condition when removing connections while accessing it
                # In this case we don't care for the concrete entity, so retry with the first one
                return self._get_connection_list(
                    deployment, type_, 0, increase_access_count
                )
            return None

    def _add_deployment(self, deployment: str):
        if deployment not in self._deployments:
            self._deployments[deployment] = {'shards': {}, 'heads': {}}
            self._access_count[deployment] = 0

    def _add_connection(
        self,
        deployment: str,
        entity_id: int,
        address: str,
        type: str,
    ):
        self._add_deployment(deployment)
        if entity_id not in self._deployments[deployment][type]:
            connection_list = _ReplicaList(
                metrics=self._metrics,
                histograms=self._histograms,
                logger=self._logger,
                runtime_name=self.runtime_name,
                aio_tracing_client_interceptors=self.aio_tracing_client_interceptors,
                tracing_client_interceptor=self.tracing_client_interceptor,
                deployment_name=deployment,
            )
            self._deployments[deployment][type][entity_id] = connection_list

        if not self._deployments[deployment][type][entity_id].has_connection(address):
            self._logger.debug(
                f'adding connection for deployment {deployment}/{type}/{entity_id} to {address}'
            )
            self._deployments[deployment][type][entity_id].add_connection(
                address, deployment_name=deployment
            )
        else:
            self._logger.debug(
                f'ignoring activation of pod for deployment {deployment}, {address} already known'
            )

    async def remove_head(self, deployment, address, head_id: Optional[int] = 0):
        return await self._remove_connection(deployment, head_id, address, 'heads')

    async def remove_replica(self, deployment, address, shard_id: Optional[int] = 0):
        return await self._remove_connection(deployment, shard_id, address, 'shards')

    async def _remove_connection(self, deployment, entity_id, address, type):
        if (
            deployment in self._deployments
            and entity_id in self._deployments[deployment][type]
        ):
            self._logger.debug(
                f'removing connection for deployment {deployment}/{type}/{entity_id} to {address}'
            )
            await self._deployments[deployment][type][entity_id].remove_connection(
                address
            )
            if not self._deployments[deployment][type][entity_id].has_connections():
                self._deployments[deployment][type].pop(entity_id)
