from typing import TYPE_CHECKING, Any, Dict, Optional, Sequence, Union
from urllib.parse import urlparse

from grpc.aio import ClientInterceptor

from jina.excepts import EstablishGrpcConnectionError
from jina.serve.networking.connection_stub import create_async_channel_stub
from jina.serve.networking.instrumentation import (
    _NetworkingHistograms,
    _NetworkingMetrics,
)
from jina.serve.networking.utils import TLS_PROTOCOL_SCHEMES

if TYPE_CHECKING:
    from opentelemetry.instrumentation.grpc._client import (
        OpenTelemetryClientInterceptor,
    )


class _ReplicaList:
    """
    Maintains a list of connections to replicas and uses round robin for selecting a replica
    """

    def __init__(
            self,
            metrics: _NetworkingMetrics,
            histograms: _NetworkingHistograms,
            logger,
            runtime_name: str,
            aio_tracing_client_interceptors: Optional[Sequence['ClientInterceptor']] = None,
            tracing_client_interceptor: Optional['OpenTelemetryClientInterceptor'] = None,
            deployment_name: str = '',
            channel_options: Optional[Union[list, Dict[str, Any]]] = None,
    ):
        self.runtime_name = runtime_name
        self._connections = []
        self._address_to_connection_idx = {}
        self._address_to_channel = {}
        self._rr_counter = 0  # round robin counter
        self._metrics = metrics
        self._histograms = histograms
        self._logger = logger
        self.aio_tracing_client_interceptors = aio_tracing_client_interceptors
        self.tracing_client_interceptors = tracing_client_interceptor
        self._deployment_name = deployment_name
        self.channel_options = channel_options
        # a set containing all the ConnectionStubs that will be created using add_connection
        # this set is not updated in reset_connection and remove_connection
        self._warmup_stubs = set()

    async def reset_connection(self, address: str, deployment_name: str):
        """
        Removes and then re-adds a connection.
        Result is the same as calling :meth:`remove_connection` and then :meth:`add_connection`, but this allows for
        handling of race condition if multiple callers reset a connection at the same time.

        :param address: Target address of this connection
        :param deployment_name: Target deployment of this connection
        """
        self._logger.debug(f'resetting connection for {deployment_name} to {address}')
        parsed_address = urlparse(address)
        resolved_address = parsed_address.netloc if parsed_address.netloc else address
        if (
                resolved_address in self._address_to_connection_idx
                and self._address_to_connection_idx[resolved_address] is not None
        ):
            # remove connection:
            # in contrast to remove_connection(), we don't 'shorten' the data structures below, instead
            # update the data structure with the new connection and let the old connection be colleced by
            # the GC
            id_to_reset = self._address_to_connection_idx[resolved_address]
            # re-add connection:
            self._address_to_connection_idx[resolved_address] = id_to_reset
            stubs, channel = self._create_connection(address, deployment_name)
            self._address_to_channel[resolved_address] = channel
            self._connections[id_to_reset] = stubs

    def add_connection(self, address: str, deployment_name: str):
        """
        Add connection with address to the connection list
        :param address: Target address of this connection
        :param deployment_name: Target deployment of this connection
        """
        parsed_address = urlparse(address)
        resolved_address = parsed_address.netloc if parsed_address.netloc else address

        if resolved_address not in self._address_to_connection_idx:
            self._address_to_connection_idx[resolved_address] = len(self._connections)
            stubs, channel = self._create_connection(address, deployment_name)
            self._address_to_channel[resolved_address] = channel
            self._connections.append(stubs)
            # create a new set of stubs and channels for warmup to avoid
            # loosing channel during remove_connection or reset_connection
            stubs, _ = self._create_connection(address, deployment_name)
            self._warmup_stubs.add(stubs)

    async def remove_connection(self, address: str):
        """
        Remove connection with address from the connection list

        .. warning::
            This completely removes the connection, including all dictionary keys that point to it.
            Therefore, be careful not to call this method while iterating over all connections.
            If you want to reset (remove and re-add) a connection, use :meth:`jina.serve.networking.ReplicaList.reset_connection`,
            which is safe to use in this scenario.

        :param address: Remove connection for this address
        """
        parsed_address = urlparse(address)
        resolved_address = parsed_address.netloc if parsed_address.netloc else address
        if resolved_address in self._address_to_connection_idx:
            self._rr_counter = (
                self._rr_counter % (len(self._connections) - 1)
                if (len(self._connections) - 1)
                else 0
            )
            idx_to_delete = self._address_to_connection_idx.pop(resolved_address)
            self._connections.pop(idx_to_delete)
            # update the address/idx mapping
            for a in self._address_to_connection_idx:
                if self._address_to_connection_idx[a] > idx_to_delete:
                    self._address_to_connection_idx[a] -= 1

    def _create_connection(self, address, deployment_name: str):
        self._logger.debug(f'create_connection connection for {deployment_name} to {address}')
        parsed_address = urlparse(address)
        address = parsed_address.netloc if parsed_address.netloc else address
        use_tls = parsed_address.scheme in TLS_PROTOCOL_SCHEMES

        stubs, channel = create_async_channel_stub(
            address,
            deployment_name=deployment_name,
            metrics=self._metrics,
            histograms=self._histograms,
            tls=use_tls,
            aio_tracing_client_interceptors=self.aio_tracing_client_interceptors,
            channel_options=self.channel_options,
        )
        return stubs, channel

    async def get_next_connection(self, num_retries=3):
        """
        Returns a connection from the list. Strategy is round robin
        :param num_retries: how many retries should be performed when all connections are currently unavailable
        :returns: A connection from the pool
        """
        return await self._get_next_connection(num_retries=num_retries)

    async def _get_next_connection(self, num_retries=3):
        """
        :param num_retries: how many retries should be performed when all connections are currently unavailable
        :returns: A connection from the pool
        """
        try:
            connection = None
            for i in range(len(self._connections)):
                internal_rr_counter = (self._rr_counter + i) % len(self._connections)
                connection = self._connections[internal_rr_counter]
                # connection is None if it is currently being reset. In that case, try different connection
                if connection is not None:
                    break
            all_connections_unavailable = connection is None and num_retries <= 0
            if all_connections_unavailable:
                if num_retries <= 0:
                    raise EstablishGrpcConnectionError(
                        f'Error while resetting connections {self._connections} for {self._deployment_name}. Connections cannot be used.'
                    )
            elif connection is None:
                # give control back to async event loop so connection resetting can be completed; then retry
                self._logger.debug(
                    f' No valid connection found for {self._deployment_name}, give chance for potential resetting of connection'
                )
                return await self._get_next_connection(num_retries=num_retries - 1)
        except IndexError:
            # This can happen as a race condition while _removing_ connections
            self._rr_counter = 0
            connection = self._connections[self._rr_counter]
        self._rr_counter = (self._rr_counter + 1) % len(self._connections)
        return connection

    def get_all_connections(self):
        """
        Returns all available connections
        :returns: A complete list of all connections from the pool
        """
        return self._connections

    def has_connection(self, address: str) -> bool:
        """
        Checks if a connection for ip exists in the list
        :param address: The address to check
        :returns: True if a connection for the ip exists in the list
        """
        parsed_address = urlparse(address)
        resolved_address = parsed_address.netloc if parsed_address.netloc else address
        return resolved_address in self._address_to_connection_idx

    def has_connections(self) -> bool:
        """
        Checks if this contains any connection
        :returns: True if any connection is managed, False otherwise
        """
        return len(self._address_to_connection_idx) > 0

    async def close(self):
        """
        Close all connections and clean up internal state
        """
        for address in self._address_to_channel:
            await self._address_to_channel[address].close(0.5)
        self._address_to_channel.clear()
        self._address_to_connection_idx.clear()
        self._connections.clear()
        self._rr_counter = 0
        for stub in self._warmup_stubs:
            await stub.channel.close(0.5)
        self._warmup_stubs.clear()

    @property
    def warmup_stubs(self):
        """Return set of warmup stubs
        :returns: Set of stubs. The set doesn't remove any items once added.
        """
        return self._warmup_stubs
