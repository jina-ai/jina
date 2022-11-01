from typing import TYPE_CHECKING, Dict, List, Optional

from docarray import DocumentArray

from jina import __default_endpoint__
from jina.excepts import BadConfigSource
from jina.importer import ImportExtensions
from jina.serve.executors import BaseExecutor
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
        **kwargs,
    ):
        """Initialize private parameters and execute private loading functions.

        :param args: args from CLI
        :param logger: the logger provided by the user
        :param metrics_registry: optional metrics registry for prometheus used if we need to expose metrics from the executor of from the data request handler
        :param tracer_provider: Optional tracer_provider that will be provided to the executor for tracing
        :param meter_provider: Optional meter_provider that will be provided to the executor for metrics
        :param kwargs: extra keyword arguments
        """
        super().__init__()
        self.args = args
        self.args.parallel = self.args.shards
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

    @staticmethod
    def _parse_params(parameters: Dict, executor_name: str):
        parsed_params = parameters
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
        if (
            requests[0].header.exec_endpoint not in self._executor.requests
            and __default_endpoint__ not in self._executor.requests
        ):
            self.logger.debug(
                f'skip executor: mismatch request, exec_endpoint: {requests[0].header.exec_endpoint}, requests: {self._executor.requests}'
            )
            return requests[0]

        self._record_request_size_monitoring(requests)

        params = self._parse_params(requests[0].parameters, self._executor.metas.name)
        docs = WorkerRequestHandler.get_docs_from_request(
            requests,
            field='docs',
        )

        # executor logic
        return_data = await self._executor.__acall__(
            req_endpoint=requests[0].header.exec_endpoint,
            docs=docs,
            parameters=params,
            docs_matrix=WorkerRequestHandler.get_docs_matrix_from_request(
                requests,
                field='docs',
            ),
            tracing_context=tracing_context,
        )

        docs = self._set_result(requests, return_data, docs)

        self._record_docs_processed_monitoring(requests, docs)
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

    def close(self):
        """Close the data request handler, by closing the executor"""
        if not self._is_closed:
            self._executor.close()
            self._is_closed = True

    @staticmethod
    def get_docs_matrix_from_request(
        requests: List['DataRequest'],
        field: str,
    ) -> List['DocumentArray']:
        """
        Returns a docs matrix from a list of DataRequest objects.
        :param requests: List of DataRequest objects
        :param field: field to be retrieved
        :return: docs matrix: list of DocumentArray objects
        """
        if len(requests) > 1:
            result = [getattr(request, field) for request in requests]
        else:
            result = [getattr(requests[0], field)]

        # to unify all length=0 DocumentArray (or any other results) will simply considered as None
        # otherwise, the executor has to handle [None, None, None] or [DocArray(0), DocArray(0), DocArray(0)]
        len_r = sum(len(r) for r in result)
        if len_r:
            return result

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
        Reduces a list of requests containing DocumentArrays inton one request object. Changes are applied to the first
        request object in-place.

        Reduction consists in reducing every DocumentArray in `requests` sequentially using
        :class:`DocumentArray`.:method:`reduce`.
        The resulting DataRequest object contains Documents of all DocumentArrays inside requests.

        :param requests: List of DataRequest objects
        :return: the resulting DataRequest
        """
        docs_matrix = WorkerRequestHandler.get_docs_matrix_from_request(
            requests, field='docs'
        )

        # Reduction is applied in-place to the first DocumentArray in the matrix
        da = WorkerRequestHandler.reduce(docs_matrix)
        WorkerRequestHandler.replace_docs(requests[0], da)

        params = WorkerRequestHandler.get_parameters_dict_from_request(requests)
        WorkerRequestHandler.replace_parameters(requests[0], params)

        return requests[0]
