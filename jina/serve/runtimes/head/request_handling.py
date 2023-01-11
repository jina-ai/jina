import asyncio
import threading
import time
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from jina.serve.networking import GrpcConnectionPool
from jina.serve.runtimes.monitoring import MonitoringRequestMixin
from jina.serve.runtimes.worker.request_handling import WorkerRequestHandler

if TYPE_CHECKING:  # pragma: no cover
    from opentelemetry.metrics import Meter
    from prometheus_client import CollectorRegistry

    from jina.logging.logger import JinaLogger
    from jina.types.request.data import DataRequest


class HeaderRequestHandler(MonitoringRequestMixin):
    """
    Class that handles the requests arriving to the head and the results extracted from the requests future.

    :param metrics_registry: optional metrics registry for prometheus. Used if we need to expose metrics from the executor or from the data request handler
    :param runtime_name: optional runtime_name that will be registered during monitoring
    """

    def __init__(
        self,
        logger: 'JinaLogger',
        metrics_registry: Optional['CollectorRegistry'] = None,
        meter: Optional['Meter'] = None,
        runtime_name: Optional[str] = None,
    ):
        super().__init__(metrics_registry, meter, runtime_name)
        self.logger = logger
        self._executor_endpoint_mapping = None
        self._gathering_endpoints = False
        self.runtime_name = runtime_name

    async def _gather_worker_tasks(
        self,
        requests,
        connection_pool,
        deployment_name,
        polling_type,
        timeout_send,
        retries,
    ):
        worker_send_tasks = connection_pool.send_requests(
            requests=requests,
            deployment=deployment_name,
            polling_type=polling_type,
            timeout=timeout_send,
            retries=retries,
        )

        all_worker_results = await asyncio.gather(*worker_send_tasks)
        worker_results = list(
            filter(lambda x: isinstance(x, Tuple), all_worker_results)
        )
        exceptions = list(
            filter(
                lambda x: issubclass(type(x), BaseException),
                all_worker_results,
            )
        )
        total_shards = len(worker_send_tasks)
        failed_shards = len(exceptions)
        if failed_shards:
            self.logger.warning(f'{failed_shards} shards out of {total_shards} failed.')

        return worker_results, exceptions, total_shards, failed_shards

    @staticmethod
    def _merge_metadata(
        metadata,
        uses_after_metadata,
        uses_before_metadata,
        total_shards,
        failed_shards,
    ):
        merged_metadata = {}
        if uses_before_metadata:
            for key, value in uses_before_metadata:
                merged_metadata[key] = value
        for meta in metadata:
            for key, value in meta:
                merged_metadata[key] = value
        if uses_after_metadata:
            for key, value in uses_after_metadata:
                merged_metadata[key] = value

        merged_metadata['total_shards'] = str(total_shards)
        merged_metadata['failed_shards'] = str(failed_shards)
        return merged_metadata

    async def _handle_data_request(
        self,
        requests,
        connection_pool,
        uses_before_address,
        uses_after_address,
        timeout_send,
        retries,
        reduce,
        polling_type,
        deployment_name,
    ) -> Tuple['DataRequest', Dict]:
        for req in requests:
            self._update_start_request_metrics(req)
        WorkerRequestHandler.merge_routes(requests)

        uses_before_metadata = None
        if uses_before_address:
            result = await connection_pool.send_requests_once(
                requests,
                deployment='uses_before',
                timeout=timeout_send,
                retries=retries,
            )
            if issubclass(type(result), BaseException):
                raise result
            else:
                response, uses_before_metadata = result
                requests = [response]

        (
            worker_results,
            exceptions,
            total_shards,
            failed_shards,
        ) = await self._gather_worker_tasks(
            requests=requests,
            deployment_name=deployment_name,
            timeout_send=timeout_send,
            connection_pool=connection_pool,
            polling_type=polling_type,
            retries=retries,
        )

        if len(worker_results) == 0:
            if exceptions:
                # raise the underlying error first
                self._update_end_failed_requests_metrics()
                raise exceptions[0]
            raise RuntimeError(
                f'Head {self.runtime_name} did not receive a response when sending message to worker pods'
            )

        worker_results, metadata = zip(*worker_results)

        response_request = worker_results[0]
        uses_after_metadata = None
        if uses_after_address:
            result = await connection_pool.send_requests_once(
                worker_results,
                deployment='uses_after',
                timeout=timeout_send,
                retries=retries,
            )
            if issubclass(type(result), BaseException):
                self._update_end_failed_requests_metrics()
                raise result
            else:
                response_request, uses_after_metadata = result
        elif len(worker_results) > 1 and reduce:
            response_request = WorkerRequestHandler.reduce_requests(worker_results)
        elif len(worker_results) > 1 and not reduce:
            # worker returned multiple responses, but the head is configured to skip reduction
            # just concatenate the docs in this case
            response_request.data.docs = WorkerRequestHandler.get_docs_from_request(
                requests
            )

        merged_metadata = self._merge_metadata(
            metadata,
            uses_after_metadata,
            uses_before_metadata,
            total_shards,
            failed_shards,
        )

        self._update_end_request_metrics(response_request)

        return response_request, merged_metadata

    async def warmup(
        self,
        connection_pool: GrpcConnectionPool,
        stop_event: threading.Event,
        deployment: str,
    ):
        '''Executes warmup task against the deployments from the connection pool.
        :param connection_pool: GrpcConnectionPool that implements the warmup to the connected deployments.
        :param stop_event: signal to indicate if an early termination of the task is required for graceful teardown.
        :param deployment: deployment name that need to be warmed up.
        '''
        self.logger.debug(f'Running HeadRuntime warmup')

        try:
            await asyncio.create_task(
                connection_pool.warmup(deployment=deployment, stop_event=stop_event)
            )
        except Exception as ex:
            self.logger.error(f'error with HeadRuntime warmup up task: {ex}')
            return
