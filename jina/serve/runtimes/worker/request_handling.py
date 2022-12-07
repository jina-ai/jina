import asyncio
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from docarray import DocumentArray

from jina import __default_endpoint__
from jina.excepts import BadConfigSource
from jina.importer import ImportExtensions
from jina.serve.executors import BaseExecutor
from jina.serve.runtimes.worker.batch_queue import BatchQueue
from jina.types.request.data import DataRequest

if TYPE_CHECKING:  # pragma: no cover
    import argparse

    from opentelemetry import metrics, trace
    from opentelemetry.context.context import Context
    from prometheus_client import CollectorRegistry

    from jina.logging.logger import JinaLogger


class WorkerRequestHandler:
    """Object to encapsulate the code related to handle the data requests passing to executor and its returned values"""

    _KEY_RESULT = '__results__'

    def __init__(
        self,
        args: 'argparse.Namespace',
        logger: 'JinaLogger',
        metrics_registry: Optional['CollectorRegistry'] = None,
        tracer_provider: Optional['trace.TracerProvider'] = None,
        meter_provider: Optional['metrics.MeterProvider'] = None,
        deployment_name: str = '',
        **kwargs,
    ):
        """Initialize private parameters and execute private loading functions.

        :param args: args from CLI
        :param logger: the logger provided by the user
        :param metrics_registry: optional metrics registry for prometheus used if we need to expose metrics from the executor of from the data request handler
        :param tracer_provider: Optional tracer_provider that will be provided to the executor for tracing
        :param meter_provider: Optional meter_provider that will be provided to the executor for metrics
        :param deployment_name: name of the deployment to use as Executor name to set in requests
        :param kwargs: extra keyword arguments
        """
        super().__init__()
        self.args = args
        self.logger = logger
        self._is_closed = False
        self._load_executor(
            metrics_registry=metrics_registry,
            tracer_provider=tracer_provider,
            meter_provider=meter_provider,
        )
        meter = (
            meter_provider.get_meter(self.__class__.__name__)
            if meter_provider
            else None
        )
        self._init_monitoring(metrics_registry, meter)
        self.deployment_name = deployment_name
        # In order to support batching parameters separately, we have to lazily create batch queues
        # So we store the config for each endpoint in the initialization
        self._batchqueue_config: Dict[str, Dict] = {}
        # the below is of "shape" exec_endpoint_name -> parameters_key -> batch_queue
        self._batchqueue_instances: Dict[
            str, Dict[str, BatchQueue]
        ] = self._init_batchqueue_dict()

    def _all_batch_queues(self) -> List[BatchQueue]:
        """Returns a list of all batch queue instances
        :return: List of all batch queues for this request handler
        """
        return [
            batch_queue
            for param_to_queue in self._batchqueue_instances.values()
            for batch_queue in param_to_queue.values()
        ]

    def _init_batchqueue_dict(self) -> Dict[str, Dict[str, BatchQueue]]:
        """Determines how endpoints and method names map to batch queues, without instantiating them.
        :return: a dictionary of "shape" exec_endpoint_name -> parameters_key -> batch_queue.
            The `exec_endpoint_name` keys are filled in, the rest is empty.
        """
        if getattr(self._executor, 'dynamic_batching', None) is not None:
            # We need to sort the keys into endpoints and functions
            # Endpoints allow specific configurations while functions allow configs to be applied to all endpoints of the function
            dbatch_endpoints = []
            dbatch_functions = []
            for key, dbatch_config in self._executor.dynamic_batching.items():
                if key.startswith('/'):
                    dbatch_endpoints.append((key, dbatch_config))
                else:
                    dbatch_functions.append((key, dbatch_config))

            # Specific endpoint configs take precedence over function configs
            for endpoint, dbatch_config in dbatch_endpoints:
                self._batchqueue_config[endpoint] = dbatch_config

            # Process function configs
            func_endpoints: Dict[str, List[str]] = {
                func.__name__: [] for func in self._executor.requests.values()
            }
            for endpoint, func in self._executor.requests.items():
                func_endpoints[func.__name__].append(endpoint)
            for func_name, dbatch_config in dbatch_functions:
                for endpoint in func_endpoints[func_name]:
                    if endpoint not in self._batchqueue_config:
                        self._batchqueue_config[endpoint] = dbatch_config

            self.logger.debug(
                f'Executor Dynamic Batching configs: {self._executor.dynamic_batching}'
            )
            self.logger.debug(
                f'Endpoint Batch Queue Configs: {self._batchqueue_config}'
            )

            return {endpoint: {} for endpoint in self._batchqueue_config.keys()}

    def _init_monitoring(
        self,
        metrics_registry: Optional['CollectorRegistry'] = None,
        meter: Optional['metrics.Meter'] = None,
    ):

        if metrics_registry:

            with ImportExtensions(
                required=True,
                help_text='You need to install the `prometheus_client` to use the montitoring functionality of jina',
            ):
                from prometheus_client import Counter, Summary

                from jina.serve.monitoring import _SummaryDeprecated

                self._document_processed_metrics = Counter(
                    'document_processed',
                    'Number of Documents that have been processed by the executor',
                    namespace='jina',
                    labelnames=('executor_endpoint', 'executor', 'runtime_name'),
                    registry=metrics_registry,
                )

                self._request_size_metrics = _SummaryDeprecated(
                    old_name='request_size_bytes',
                    name='received_request_bytes',
                    documentation='The size in bytes of the request returned to the gateway',
                    namespace='jina',
                    labelnames=('executor_endpoint', 'executor', 'runtime_name'),
                    registry=metrics_registry,
                )

                self._sent_response_size_metrics = Summary(
                    'sent_response_bytes',
                    'The size in bytes of the response sent to the gateway',
                    namespace='jina',
                    labelnames=('executor_endpoint', 'executor', 'runtime_name'),
                    registry=metrics_registry,
                )
        else:
            self._document_processed_metrics = None
            self._request_size_metrics = None
            self._sent_response_size_metrics = None

        if meter:
            self._document_processed_counter = meter.create_counter(
                name='jina_document_processed',
                description='Number of Documents that have been processed by the executor',
            )

            self._request_size_histogram = meter.create_histogram(
                name='jina_received_request_bytes',
                description='The size in bytes of the request returned to the gateway',
            )

            self._sent_response_size_histogram = meter.create_histogram(
                name='jina_sent_response_bytes',
                description='The size in bytes of the response sent to the gateway',
            )
        else:
            self._document_processed_counter = None
            self._request_size_histogram = None
            self._sent_response_size_histogram = None

    def _load_executor(
        self,
        metrics_registry: Optional['CollectorRegistry'] = None,
        tracer_provider: Optional['trace.TracerProvider'] = None,
        meter_provider: Optional['metrics.MeterProvider'] = None,
    ):
        """
        Load the executor to this runtime, specified by ``uses`` CLI argument.
        :param metrics_registry: Optional prometheus metrics registry that will be passed to the executor so that it can expose metrics
        :param tracer_provider: Optional tracer_provider that will be provided to the executor for tracing
        :param meter_provider: Optional meter_provider that will be provided to the executor for metrics
        """
        try:
            self._executor: BaseExecutor = BaseExecutor.load_config(
                self.args.uses,
                uses_with=self.args.uses_with,
                uses_metas=self.args.uses_metas,
                uses_requests=self.args.uses_requests,
                uses_dynamic_batching=self.args.uses_dynamic_batching,
                runtime_args={  # these are not parsed to the yaml config file but are pass directly during init
                    'workspace': self.args.workspace,
                    'shard_id': self.args.shard_id,
                    'shards': self.args.shards,
                    'replicas': self.args.replicas,
                    'name': self.args.name,
                    'metrics_registry': metrics_registry,
                    'tracer_provider': tracer_provider,
                    'meter_provider': meter_provider,
                },
                py_modules=self.args.py_modules,
                extra_search_paths=self.args.extra_search_paths,
            )
            self.logger.debug(f'{self._executor} is successfully loaded!')

        except BadConfigSource:
            self.logger.error(f'fail to load config from {self.args.uses}')
            raise
        except FileNotFoundError:
            self.logger.error(f'fail to load file dependency')
            raise
        except Exception:
            self.logger.critical(f'can not load the executor from {self.args.uses}')
            raise

    def _refresh_executor(self, changed_files):
        import copy
        import importlib
        import inspect
        import sys

        try:
            sys_mod_files_modules = {
                getattr(module, '__file__', ''): module
                for module in sys.modules.values()
            }

            for file in changed_files:
                if file in sys_mod_files_modules:
                    importlib.reload(sys_mod_files_modules[file])
                else:
                    self.logger.debug(
                        f'Changed file {file} was not previously imported.'
                    )
        except Exception as exc:
            self.logger.error(
                f' Exception when refreshing Executor when changes detected in {changed_files}'
            )
            raise exc

        importlib.reload(inspect.getmodule(self._executor.__class__))
        requests = copy.copy(self._executor.requests)
        old_cls = self._executor.__class__
        new_cls = getattr(importlib.import_module(old_cls.__module__), old_cls.__name__)
        new_executor = new_cls.__new__(new_cls)
        new_executor.__dict__ = self._executor.__dict__
        for k, v in requests.items():
            requests[k] = getattr(new_executor.__class__, requests[k].__name__)
        self._executor = new_executor
        self._executor.requests.clear()
        requests = {k: v.__name__ for k, v in requests.items()}
        self._executor._add_requests(requests)

    @staticmethod
    def _parse_params(parameters: Dict, executor_name: str):
        parsed_params = parameters  # TODO: Copy? This still points to the same object
        specific_parameters = parameters.get(executor_name, None)
        if specific_parameters:
            parsed_params.update(**specific_parameters)

        return parsed_params

    @staticmethod
    def _metric_attributes(executor_endpoint, executor, runtime_name):
        return {
            'executor_endpoint': executor_endpoint,
            'executor': executor,
            'runtime_name': runtime_name,
        }

    def _record_request_size_monitoring(self, requests):
        for req in requests:
            if self._request_size_metrics:
                self._request_size_metrics.labels(
                    requests[0].header.exec_endpoint,
                    self._executor.__class__.__name__,
                    self.args.name,
                ).observe(req.nbytes)
            if self._request_size_histogram:
                attributes = WorkerRequestHandler._metric_attributes(
                    requests[0].header.exec_endpoint,
                    self._executor.__class__.__name__,
                    self.args.name,
                )
                self._request_size_histogram.record(req.nbytes, attributes=attributes)

    def _record_docs_processed_monitoring(self, requests, docs):
        if self._document_processed_metrics:
            self._document_processed_metrics.labels(
                requests[0].header.exec_endpoint,
                self._executor.__class__.__name__,
                self.args.name,
            ).inc(len(docs))
        if self._document_processed_counter:
            attributes = WorkerRequestHandler._metric_attributes(
                requests[0].header.exec_endpoint,
                self._executor.__class__.__name__,
                self.args.name,
            )
            self._document_processed_counter.add(len(docs), attributes=attributes)

    def _record_response_size_monitoring(self, requests):
        if self._sent_response_size_metrics:
            self._sent_response_size_metrics.labels(
                requests[0].header.exec_endpoint,
                self._executor.__class__.__name__,
                self.args.name,
            ).observe(requests[0].nbytes)
        if self._sent_response_size_histogram:
            attributes = WorkerRequestHandler._metric_attributes(
                requests[0].header.exec_endpoint,
                self._executor.__class__.__name__,
                self.args.name,
            )
            self._sent_response_size_histogram.record(
                requests[0].nbytes, attributes=attributes
            )

    def _set_result(self, requests, return_data, docs):
        # assigning result back to request
        if return_data is not None:
            if isinstance(return_data, DocumentArray):
                docs = return_data
            elif isinstance(return_data, dict):
                params = requests[0].parameters
                results_key = self._KEY_RESULT

                if not results_key in params.keys():
                    params[results_key] = dict()

                params[results_key].update({self.args.name: return_data})
                requests[0].parameters = params

            else:
                raise TypeError(
                    f'The return type must be DocumentArray / Dict / `None`, '
                    f'but getting {return_data!r}'
                )

        WorkerRequestHandler.replace_docs(
            requests[0], docs, self.args.output_array_type
        )
        return docs

    async def handle(
        self, requests: List['DataRequest'], tracing_context: Optional['Context'] = None
    ) -> DataRequest:
        """Initialize private parameters and execute private loading functions.

        :param requests: The messages to handle containing a DataRequest
        :param tracing_context: Optional OpenTelemetry tracing context from the originating request.
        :returns: the processed message
        """

        # skip executor if endpoints mismatch
        exec_endpoint: str = requests[0].header.exec_endpoint
        if exec_endpoint not in self._executor.requests:
            if __default_endpoint__ in self._executor.requests:
                exec_endpoint = __default_endpoint__
            else:
                self.logger.debug(
                    f'skip executor: mismatch request, exec_endpoint: {exec_endpoint}, requests: {self._executor.requests}'
                )
                return requests[0]

        self._record_request_size_monitoring(requests)

        params = self._parse_params(requests[0].parameters, self._executor.metas.name)

        if exec_endpoint in self._batchqueue_config:
            assert len(requests) == 1, 'dynamic batching does not support no_reduce'

            param_key = str(params)
            if param_key not in self._batchqueue_instances[exec_endpoint]:
                self._batchqueue_instances[exec_endpoint][param_key] = BatchQueue(
                    executor=self._executor,
                    exec_endpoint=exec_endpoint,
                    args=self.args,
                    params=params,
                    **self._batchqueue_config[exec_endpoint],
                )
            # This is necessary because push might need to await for the queue to be emptied
            task = await self._batchqueue_instances[exec_endpoint][param_key].push(
                requests[0]
            )
            await task
        else:
            docs = WorkerRequestHandler.get_docs_from_request(
                requests,
                field='docs',
            )

            docs_matrix, docs_map = WorkerRequestHandler._get_docs_matrix_from_request(
                requests
            )
            return_data = await self._executor.__acall__(
                req_endpoint=requests[0].header.exec_endpoint,
                docs=docs,
                parameters=params,
                docs_matrix=docs_matrix,
                docs_map=docs_map,
                tracing_context=tracing_context,
            )

            _ = self._set_result(requests, return_data, docs)

        for req in requests:
            req.add_executor(self.deployment_name)

        self._record_docs_processed_monitoring(requests, requests[0].docs)
        self._record_response_size_monitoring(requests)

        return requests[0]

    @staticmethod
    def replace_docs(
        request: List['DataRequest'], docs: 'DocumentArray', ndarrray_type: str = None
    ) -> None:
        """Replaces the docs in a message with new Documents.

        :param request: The request object
        :param docs: the new docs to be used
        :param ndarrray_type: type tensor and embedding will be converted to
        """
        request.data.set_docs_convert_arrays(docs, ndarray_type=ndarrray_type)

    @staticmethod
    def replace_parameters(request: List['DataRequest'], parameters: Dict) -> None:
        """Replaces the parameters in a message with new Documents.

        :param request: The request object
        :param parameters: the new parameters to be used
        """
        request.parameters = parameters

    @staticmethod
    def merge_routes(requests: List['DataRequest']) -> None:
        """Merges all routes found in requests into the first message

        :param requests: The messages containing the requests with the routes to merge
        """
        if len(requests) <= 1:
            return
        existing_executor_routes = [r.executor for r in requests[0].routes]
        for request in requests[1:]:
            for route in request.routes:
                if route.executor not in existing_executor_routes:
                    requests[0].routes.append(route)
                    existing_executor_routes.append(route.executor)

    async def close(self):
        """Close the data request handler, by closing the executor and the batch queues."""
        if not self._is_closed:
            await asyncio.gather(*[q.close() for q in self._all_batch_queues()])
            self._executor.close()
            self._is_closed = True

    @staticmethod
    def _get_docs_matrix_from_request(
        requests: List['DataRequest'],
    ) -> Tuple[Optional[List['DocumentArray']], Optional[Dict[str, 'DocumentArray']]]:
        """
        Returns a docs matrix from a list of DataRequest objects.

        :param requests: List of DataRequest objects
        :return: docs matrix and doc: list of DocumentArray objects
        """
        docs_map = {}
        docs_matrix = []
        for req in requests:
            docs_matrix.append(req.docs)
            docs_map[req.last_executor] = req.docs

        # to unify all length=0 DocumentArray (or any other results) will simply considered as None
        # otherwise, the executor has to handle [None, None, None] or [DocArray(0), DocArray(0), DocArray(0)]
        len_r = sum(len(r) for r in docs_matrix)
        if len_r == 0:
            docs_matrix = None

        return docs_matrix, docs_map

    @staticmethod
    def get_parameters_dict_from_request(
        requests: List['DataRequest'],
    ) -> 'Dict':
        """
        Returns a parameters dict from a list of DataRequest objects.
        :param requests: List of DataRequest objects
        :return: parameters matrix: list of parameters (Dict) objects
        """
        key_result = WorkerRequestHandler._KEY_RESULT
        parameters = requests[0].parameters
        if key_result not in parameters.keys():
            parameters[key_result] = dict()
        # we only merge the results and make the assumption that the others params does not change during execution

        for req in requests:
            parameters[key_result].update(req.parameters.get(key_result, dict()))

        return parameters

    @staticmethod
    def get_docs_from_request(
        requests: List['DataRequest'],
        field: str,
    ) -> 'DocumentArray':
        """
        Gets a field from the message

        :param requests: requests to get the field from
        :param field: field name to access

        :returns: DocumentArray extracted from the field from all messages
        """
        if len(requests) > 1:
            result = DocumentArray(
                [
                    d
                    for r in reversed([request for request in requests])
                    for d in getattr(r, field)
                ]
            )
        else:
            result = getattr(requests[0], field)

        return result

    @staticmethod
    def reduce(docs_matrix: List['DocumentArray']) -> Optional['DocumentArray']:
        """
        Reduces a list of DocumentArrays into one DocumentArray. Changes are applied to the first
        DocumentArray in-place.

        Reduction consists in reducing every DocumentArray in `docs_matrix` sequentially using
        :class:`DocumentArray`.:method:`reduce`.
        The resulting DocumentArray contains Documents of all DocumentArrays.
        If a Document exists in many DocumentArrays, data properties are merged with priority to the left-most
        DocumentArrays (that is, if a data attribute is set in a Document belonging to many DocumentArrays, the
        attribute value of the left-most DocumentArray is kept).
        Matches and chunks of a Document belonging to many DocumentArrays are also reduced in the same way.
        Other non-data properties are ignored.

        .. note::
            - Matches are not kept in a sorted order when they are reduced. You might want to re-sort them in a later
                step.
            - The final result depends on the order of DocumentArrays when applying reduction.

        :param docs_matrix: List of DocumentArrays to be reduced
        :return: the resulting DocumentArray
        """
        if docs_matrix:
            da = docs_matrix[0]
            da.reduce_all(docs_matrix[1:])
            return da

    @staticmethod
    def reduce_requests(requests: List['DataRequest']) -> 'DataRequest':
        """
        Reduces a list of requests containing DocumentArrays into one request object. Changes are applied to the first
        request object in-place.

        Reduction consists in reducing every DocumentArray in `requests` sequentially using
        :class:`DocumentArray`.:method:`reduce`.
        The resulting DataRequest object contains Documents of all DocumentArrays inside requests.

        :param requests: List of DataRequest objects
        :return: the resulting DataRequest
        """
        docs_matrix, _ = WorkerRequestHandler._get_docs_matrix_from_request(requests)

        # Reduction is applied in-place to the first DocumentArray in the matrix
        da = WorkerRequestHandler.reduce(docs_matrix)
        WorkerRequestHandler.replace_docs(requests[0], da)

        params = WorkerRequestHandler.get_parameters_dict_from_request(requests)
        WorkerRequestHandler.replace_parameters(requests[0], params)

        return requests[0]
