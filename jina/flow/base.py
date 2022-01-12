import argparse
import base64
import copy
import itertools
import json
import multiprocessing
import os
import re
import sys
import threading
import time
import uuid
from collections import OrderedDict
from contextlib import ExitStack
from typing import (
    Optional,
    Union,
    Tuple,
    List,
    Set,
    Dict,
    overload,
    Type,
    TYPE_CHECKING,
)

from jina.flow.builder import allowed_levels, _hanging_pods
from jina import __default_host__, helper
from jina.clients import Client
from jina.clients.mixin import AsyncPostMixin, PostMixin
from jina.enums import (
    FlowBuildLevel,
    PodRoleType,
    FlowInspectType,
    GatewayProtocolType,
    PollingType,
)
from jina.excepts import FlowTopologyError, FlowMissingPodError, RuntimeFailToStart
from jina.helper import (
    colored,
    get_public_ip,
    get_internal_ip,
    typename,
    ArgNamespace,
    download_mermaid_url,
    CatchAllCleanupContextManager,
)
from jina.jaml import JAMLCompatible
from jina.logging.logger import JinaLogger
from jina.parsers import set_gateway_parser, set_pod_parser, set_client_cli_parser
from jina.parsers.flow import set_flow_parser
from jina.peapods import Pod

__all__ = ['Flow']


class FlowType(type(ExitStack), type(JAMLCompatible)):
    """Type of Flow, metaclass of :class:`BaseFlow`"""

    pass


_regex_port = r'(.*?):([0-9]{1,4}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5])$'

if TYPE_CHECKING:
    from jina.executors import BaseExecutor
    from jina.clients.base import BaseClient
    from jina.flow.asyncio import AsyncFlow

GATEWAY_NAME = 'gateway'
FALLBACK_PARSERS = [
    set_gateway_parser(),
    set_pod_parser(),
    set_client_cli_parser(),
    set_flow_parser(),
]


class Flow(PostMixin, JAMLCompatible, ExitStack, metaclass=FlowType):
    """Flow is how Jina streamlines and distributes Executors. """

    # overload_inject_start_client_flow
    @overload
    def __init__(
        self,
        *,
        asyncio: Optional[bool] = False,
        host: Optional[str] = '0.0.0.0',
        https: Optional[bool] = False,
        port: Optional[int] = None,
        protocol: Optional[str] = 'GRPC',
        proxy: Optional[bool] = False,
        results_as_docarray: Optional[bool] = False,
        **kwargs,
    ):
        """Create a Flow. Flow is how Jina streamlines and scales Executors. This overloaded method provides arguments from `jina client` CLI.

        :param asyncio: If set, then the input and output of this Client work in an asynchronous manner.
        :param host: The host address of the runtime, by default it is 0.0.0.0.
        :param https: If set, connect to gateway using https
        :param port: The port of the Gateway, which the client should connect to.
        :param protocol: Communication protocol between server and client.
        :param proxy: If set, respect the http_proxy and https_proxy environment variables. otherwise, it will unset these proxy variables before start. gRPC seems to prefer no proxy
        :param results_as_docarray: If set, return results as DocArray instead of Request.

        .. # noqa: DAR202
        .. # noqa: DAR101
        .. # noqa: DAR003
        """

    # overload_inject_end_client_flow

    # overload_inject_start_gateway_flow
    @overload
    def __init__(
        self,
        *,
        compress: Optional[str] = 'NONE',
        compress_min_bytes: Optional[int] = 1024,
        compress_min_ratio: Optional[float] = 1.1,
        connection_list: Optional[str] = None,
        cors: Optional[bool] = False,
        daemon: Optional[bool] = False,
        default_swagger_ui: Optional[bool] = False,
        description: Optional[str] = None,
        env: Optional[dict] = None,
        expose_endpoints: Optional[str] = None,
        expose_public: Optional[bool] = False,
        graph_description: Optional[str] = '{}',
        host: Optional[str] = '0.0.0.0',
        host_in: Optional[str] = '0.0.0.0',
        log_config: Optional[str] = None,
        name: Optional[str] = 'gateway',
        native: Optional[bool] = False,
        no_crud_endpoints: Optional[bool] = False,
        no_debug_endpoints: Optional[bool] = False,
        pods_addresses: Optional[str] = '{}',
        polling: Optional[str] = 'ANY',
        port_expose: Optional[int] = None,
        port_in: Optional[int] = None,
        prefetch: Optional[int] = 0,
        protocol: Optional[str] = 'GRPC',
        proxy: Optional[bool] = False,
        py_modules: Optional[List[str]] = None,
        quiet: Optional[bool] = False,
        quiet_error: Optional[bool] = False,
        replicas: Optional[int] = 1,
        runtime_backend: Optional[str] = 'PROCESS',
        runtime_cls: Optional[str] = 'GRPCGatewayRuntime',
        shards: Optional[int] = 1,
        timeout_ctrl: Optional[int] = 60,
        timeout_ready: Optional[int] = 600000,
        title: Optional[str] = None,
        uses: Optional[Union[str, Type['BaseExecutor'], dict]] = 'BaseExecutor',
        uses_after_address: Optional[str] = None,
        uses_before_address: Optional[str] = None,
        uses_metas: Optional[dict] = None,
        uses_requests: Optional[dict] = None,
        uses_with: Optional[dict] = None,
        uvicorn_kwargs: Optional[dict] = None,
        workspace: Optional[str] = None,
        **kwargs,
    ):
        """Create a Flow. Flow is how Jina streamlines and scales Executors. This overloaded method provides arguments from `jina gateway` CLI.

        :param compress: The compress algorithm used over the entire Flow.

              Note that this is not necessarily effective,
              it depends on the settings of `--compress-min-bytes` and `compress-min-ratio`
        :param compress_min_bytes: The original message size must be larger than this number to trigger the compress algorithm, -1 means disable compression.
        :param compress_min_ratio: The compression ratio (uncompressed_size/compressed_size) must be higher than this number to trigger the compress algorithm.
        :param connection_list: dictionary JSON with a list of connections to configure
        :param cors: If set, a CORS middleware is added to FastAPI frontend to allow cross-origin access.
        :param daemon: The Pea attempts to terminate all of its Runtime child processes/threads on existing. setting it to true basically tell the Pea do not wait on the Runtime when closing
        :param default_swagger_ui: If set, the default swagger ui is used for `/docs` endpoint.
        :param description: The description of this HTTP server. It will be used in automatics docs such as Swagger UI.
        :param env: The map of environment variables that are available inside runtime
        :param expose_endpoints: A JSON string that represents a map from executor endpoints (`@requests(on=...)`) to HTTP endpoints.
        :param expose_public: If set, expose the public IP address to remote when necessary, by default it exposesprivate IP address, which only allows accessing under the same network/subnet. Important to set this to true when the Pea will receive input connections from remote Peas
        :param graph_description: Routing graph for the gateway
        :param host: The host address of the runtime, by default it is 0.0.0.0.
        :param host_in: The host address for binding to, by default it is 0.0.0.0
        :param log_config: The YAML config of the logger used in this object.
        :param name: The name of this object.

          This will be used in the following places:
          - how you refer to this object in Python/YAML/CLI
          - visualization
          - log message header
          - ...

          When not given, then the default naming strategy will apply.
        :param native: If set, only native Executors is allowed, and the Executor is always run inside WorkerRuntime.
        :param no_crud_endpoints: If set, /index, /search, /update, /delete endpoints are removed from HTTP interface.

                  Any executor that has `@requests(on=...)` bind with those values will receive data requests.
        :param no_debug_endpoints: If set, /status /post endpoints are removed from HTTP interface.
        :param pods_addresses: dictionary JSON with the input addresses of each Pod
        :param polling: The polling strategy of the Pod and its endpoints (when `shards>1`).
              Can be defined for all endpoints of a Pod or by endpoint.
              Define per Pod:
              - ANY: only one (whoever is idle) Pea polls the message
              - ALL: all Peas poll the message (like a broadcast)
              Define per Endpoint:
              JSON dict, {endpoint: PollingType}
              {'/custom': 'ALL', '/search': 'ANY', '*': 'ANY'}
        :param port_expose: The port that the gateway exposes for clients for GRPC connections.
        :param port_in: The port for input data to bind to, default a random port between [49152, 65535]
        :param prefetch: Number of requests fetched from the client before feeding into the first Executor.

              Used to control the speed of data input into a Flow. 0 disables prefetch (disabled by default)
        :param protocol: Communication protocol between server and client.
        :param proxy: If set, respect the http_proxy and https_proxy environment variables. otherwise, it will unset these proxy variables before start. gRPC seems to prefer no proxy
        :param py_modules: The customized python modules need to be imported before loading the executor

          Note that the recommended way is to only import a single module - a simple python file, if your
          executor can be defined in a single file, or an ``__init__.py`` file if you have multiple files,
          which should be structured as a python package. For more details, please see the
          `Executor cookbook <https://docs.jina.ai/fundamentals/executor/repository-structure/>`__
        :param quiet: If set, then no log will be emitted from this object.
        :param quiet_error: If set, then exception stack information will not be added to the log
        :param replicas: The number of replicas in the pod
        :param runtime_backend: The parallel backend of the runtime inside the Pea
        :param runtime_cls: The runtime class to run inside the Pea
        :param shards: The number of shards in the pod running at the same time. For more details check https://docs.jina.ai/fundamentals/flow/topology/
        :param timeout_ctrl: The timeout in milliseconds of the control request, -1 for waiting forever
        :param timeout_ready: The timeout in milliseconds of a Pea waits for the runtime to be ready, -1 for waiting forever
        :param title: The title of this HTTP server. It will be used in automatics docs such as Swagger UI.
        :param uses: The config of the executor, it could be one of the followings:
                  * an Executor YAML file (.yml, .yaml, .jaml)
                  * a Jina Hub Executor (must start with `jinahub://` or `jinahub+docker://`)
                  * a docker image (must start with `docker://`)
                  * the string literal of a YAML config (must start with `!` or `jtype: `)
                  * the string literal of a JSON config

                  When use it under Python, one can use the following values additionally:
                  - a Python dict that represents the config
                  - a text file stream has `.read()` interface
        :param uses_after_address: The address of the uses-before runtime
        :param uses_before_address: The address of the uses-before runtime
        :param uses_metas: Dictionary of keyword arguments that will override the `metas` configuration in `uses`
        :param uses_requests: Dictionary of keyword arguments that will override the `requests` configuration in `uses`
        :param uses_with: Dictionary of keyword arguments that will override the `with` configuration in `uses`
        :param uvicorn_kwargs: Dictionary of kwargs arguments that will be passed to Uvicorn server when starting the server

          More details can be found in Uvicorn docs: https://www.uvicorn.org/settings/
        :param workspace: The working directory for any IO operations in this object. If not set, then derive from its parent `workspace`.

        .. # noqa: DAR202
        .. # noqa: DAR101
        .. # noqa: DAR003
        """

    # overload_inject_end_gateway_flow
    # overload_inject_start_flow
    @overload
    def __init__(
        self,
        *,
        env: Optional[dict] = None,
        inspect: Optional[str] = 'COLLECT',
        log_config: Optional[str] = None,
        name: Optional[str] = None,
        polling: Optional[str] = 'ANY',
        quiet: Optional[bool] = False,
        quiet_error: Optional[bool] = False,
        timeout_ctrl: Optional[int] = 60,
        uses: Optional[str] = None,
        workspace: Optional[str] = './',
        **kwargs,
    ):
        """Create a Flow. Flow is how Jina streamlines and scales Executors. This overloaded method provides arguments from `jina flow` CLI.

        :param env: The map of environment variables that are available inside runtime
        :param inspect: The strategy on those inspect pods in the flow.

              If `REMOVE` is given then all inspect pods are removed when building the flow.
        :param log_config: The YAML config of the logger used in this object.
        :param name: The name of this object.

          This will be used in the following places:
          - how you refer to this object in Python/YAML/CLI
          - visualization
          - log message header
          - ...

          When not given, then the default naming strategy will apply.
        :param polling: The polling strategy of the Pod and its endpoints (when `shards>1`).
              Can be defined for all endpoints of a Pod or by endpoint.
              Define per Pod:
              - ANY: only one (whoever is idle) Pea polls the message
              - ALL: all Peas poll the message (like a broadcast)
              Define per Endpoint:
              JSON dict, {endpoint: PollingType}
              {'/custom': 'ALL', '/search': 'ANY', '*': 'ANY'}
        :param quiet: If set, then no log will be emitted from this object.
        :param quiet_error: If set, then exception stack information will not be added to the log
        :param timeout_ctrl: The timeout in milliseconds of the control request, -1 for waiting forever
        :param uses: The YAML file represents a flow
        :param workspace: The working directory for any IO operations in this object. If not set, then derive from its parent `workspace`.

        .. # noqa: DAR202
        .. # noqa: DAR101
        .. # noqa: DAR003
        """

    # overload_inject_end_flow
    def __init__(
        self,
        args: Optional['argparse.Namespace'] = None,
        **kwargs,
    ):
        super().__init__()
        self._version = '1'  #: YAML version number, this will be later overridden if YAML config says the other way
        self._pod_nodes = OrderedDict()  # type: Dict[str, Pod]
        self._inspect_pods = {}  # type: Dict[str, str]
        self._endpoints_mapping = {}  # type: Dict[str, Dict]
        self._build_level = FlowBuildLevel.EMPTY
        self._last_changed_pod = [
            GATEWAY_NAME
        ]  #: default first pod is gateway, will add when build()
        self._update_args(args, **kwargs)

        if isinstance(self.args, argparse.Namespace):
            self.logger = JinaLogger(
                self.__class__.__name__, **vars(self.args), **self._common_kwargs
            )
        else:
            self.logger = JinaLogger(self.__class__.__name__, **self._common_kwargs)

    def _update_args(self, args, **kwargs):
        from jina.parsers.flow import set_flow_parser
        from jina.helper import ArgNamespace

        _flow_parser = set_flow_parser()
        if args is None:
            args = ArgNamespace.kwargs2namespace(
                kwargs, _flow_parser, True, fallback_parsers=FALLBACK_PARSERS
            )
        self.args = args
        # common args should be the ones that can not be parsed by _flow_parser
        known_keys = vars(args)
        self._common_kwargs = {k: v for k, v in kwargs.items() if k not in known_keys}

        self._kwargs = ArgNamespace.get_non_defaults_args(
            args, _flow_parser
        )  #: for yaml dump

        if self._common_kwargs.get('asyncio', False) and not isinstance(
            self, AsyncPostMixin
        ):
            from jina.flow.asyncio import AsyncFlow

            self.__class__ = AsyncFlow

    @staticmethod
    def _parse_endpoints(op_flow, pod_name, endpoint, connect_to_last_pod=False) -> Set:
        # parsing needs
        if isinstance(endpoint, str):
            endpoint = [endpoint]
        elif not endpoint:
            if op_flow._last_changed_pod and connect_to_last_pod:
                endpoint = [op_flow.last_pod]
            else:
                endpoint = []

        if isinstance(endpoint, (list, tuple)):
            for idx, s in enumerate(endpoint):
                if s == pod_name:
                    raise FlowTopologyError(
                        'the income/output of a pod can not be itself'
                    )
        else:
            raise ValueError(f'endpoint={endpoint} is not parsable')

        # if an endpoint is being inspected, then replace it with inspected Pod
        endpoint = set(op_flow._inspect_pods.get(ep, ep) for ep in endpoint)
        return endpoint

    @property
    def last_pod(self):
        """Last pod


        .. # noqa: DAR401


        .. # noqa: DAR201
        """
        return self._last_changed_pod[-1]

    @last_pod.setter
    def last_pod(self, name: str):
        """
        Set a Pod as the last Pod in the Flow, useful when modifying the Flow.


        .. # noqa: DAR401
        :param name: the name of the existing Pod
        """
        if name not in self._pod_nodes:
            raise FlowMissingPodError(f'{name} can not be found in this Flow')

        if self._last_changed_pod and name == self.last_pod:
            pass
        else:
            self._last_changed_pod.append(name)

        # graph is now changed so we need to
        # reset the build level to the lowest
        self._build_level = FlowBuildLevel.EMPTY

    @allowed_levels([FlowBuildLevel.EMPTY])
    def _add_gateway(
        self,
        needs: str,
        graph_description: Dict[str, List[str]],
        pod_addresses: Dict[str, List[str]],
        **kwargs,
    ):
        kwargs.update(
            dict(
                name=GATEWAY_NAME,
                ctrl_with_ipc=True,  # otherwise ctrl port would be conflicted
                host=self.host,
                protocol=self.protocol,
                port_expose=self.port_expose,
                pod_role=PodRoleType.GATEWAY,
                expose_endpoints=json.dumps(self._endpoints_mapping),
            )
        )

        kwargs.update(self._common_kwargs)
        args = ArgNamespace.kwargs2namespace(kwargs, set_gateway_parser())
        args.noblock_on_start = True
        args.graph_description = json.dumps(graph_description)
        args.pods_addresses = json.dumps(pod_addresses)
        self._pod_nodes[GATEWAY_NAME] = Pod(args, needs)

    def _get_pod_addresses(self) -> Dict[str, List[str]]:
        graph_dict = {}
        for node, v in self._pod_nodes.items():
            if node == 'gateway':
                continue
            graph_dict[node] = [f'{v.host}:{v.head_port_in}']

        return graph_dict

    def _get_k8s_pod_addresses(self, k8s_namespace: str) -> Dict[str, List[str]]:
        graph_dict = {}
        from jina.peapods.networking import K8sGrpcConnectionPool
        from jina.peapods.pods.config.helper import to_compatible_name

        for node, v in self._pod_nodes.items():
            if node == 'gateway':
                continue
            pod_k8s_address = (
                f'{to_compatible_name(v.head_args.name)}.{k8s_namespace}.svc'
            )
            graph_dict[node] = [
                f'{pod_k8s_address}:{K8sGrpcConnectionPool.K8S_PORT_IN}'
            ]

        return graph_dict

    def _get_docker_compose_pod_addresses(self) -> Dict[str, List[str]]:
        graph_dict = {}
        from jina.peapods.pods.config.docker_compose import PORT_IN
        from jina.peapods.pods.config.helper import to_compatible_name

        for node, v in self._pod_nodes.items():
            if node == 'gateway':
                continue
            pod_docker_compose_address = (
                f'{to_compatible_name(v.head_args.name)}:{PORT_IN}'
            )
            graph_dict[node] = [pod_docker_compose_address]

        return graph_dict

    def _get_graph_representation(self) -> Dict[str, List[str]]:
        def _add_node(graph, n):
            # in the graph we need to distinguish between start and end gateway, although they are the same pod
            if n == 'gateway':
                n = 'start-gateway'
            if n not in graph:
                graph[n] = []
            return n

        graph_dict = {}
        for node, v in self._pod_nodes.items():
            node = _add_node(graph_dict, node)
            if node == 'start-gateway':
                continue
            for need in sorted(v.needs):
                need = _add_node(graph_dict, need)
                graph_dict[need].append(node)

        # find all non hanging leafs
        last_pod = self.last_pod
        if last_pod != 'gateway':
            graph_dict[last_pod].append('end-gateway')

        return graph_dict

    @allowed_levels([FlowBuildLevel.EMPTY])
    def needs(
        self, needs: Union[Tuple[str], List[str]], name: str = 'joiner', *args, **kwargs
    ) -> 'Flow':
        """
        Add a blocker to the Flow, wait until all peas defined in **needs** completed.


        .. # noqa: DAR401
        :param needs: list of service names to wait
        :param name: the name of this joiner, by default is ``joiner``
        :param args: additional positional arguments forwarded to the add function
        :param kwargs: additional key value arguments forwarded to the add function
        :return: the modified Flow
        """
        if len(needs) <= 1:
            raise FlowTopologyError(
                'no need to wait for a single service, need len(needs) > 1'
            )
        return self.add(
            name=name, needs=needs, pod_role=PodRoleType.JOIN, *args, **kwargs
        )

    def needs_all(self, name: str = 'joiner', *args, **kwargs) -> 'Flow':
        """
        Collect all hanging Pods so far and add a blocker to the Flow; wait until all handing peas completed.

        :param name: the name of this joiner (default is ``joiner``)
        :param args: additional positional arguments which are forwarded to the add and needs function
        :param kwargs: additional key value arguments which are forwarded to the add and needs function
        :return: the modified Flow
        """
        needs = _hanging_pods(self)
        if len(needs) == 1:
            return self.add(name=name, needs=needs, *args, **kwargs)

        return self.needs(name=name, needs=needs, *args, **kwargs)

    # overload_inject_start_pod
    @overload
    def add(
        self,
        *,
        connection_list: Optional[str] = None,
        daemon: Optional[bool] = False,
        docker_kwargs: Optional[dict] = None,
        entrypoint: Optional[str] = None,
        env: Optional[dict] = None,
        expose_public: Optional[bool] = False,
        external: Optional[bool] = False,
        force_update: Optional[bool] = False,
        gpus: Optional[str] = None,
        host: Optional[str] = '0.0.0.0',
        host_in: Optional[str] = '0.0.0.0',
        install_requirements: Optional[bool] = False,
        log_config: Optional[str] = None,
        name: Optional[str] = None,
        native: Optional[bool] = False,
        peas_hosts: Optional[List[str]] = None,
        polling: Optional[str] = 'ANY',
        port_in: Optional[int] = None,
        port_jinad: Optional[int] = 8000,
        pull_latest: Optional[bool] = False,
        py_modules: Optional[List[str]] = None,
        quiet: Optional[bool] = False,
        quiet_error: Optional[bool] = False,
        quiet_remote_logs: Optional[bool] = False,
        replicas: Optional[int] = 1,
        runtime_backend: Optional[str] = 'PROCESS',
        runtime_cls: Optional[str] = 'WorkerRuntime',
        shards: Optional[int] = 1,
        timeout_ctrl: Optional[int] = 60,
        timeout_ready: Optional[int] = 600000,
        upload_files: Optional[List[str]] = None,
        uses: Optional[Union[str, Type['BaseExecutor'], dict]] = 'BaseExecutor',
        uses_after: Optional[Union[str, Type['BaseExecutor'], dict]] = None,
        uses_after_address: Optional[str] = None,
        uses_before: Optional[Union[str, Type['BaseExecutor'], dict]] = None,
        uses_before_address: Optional[str] = None,
        uses_metas: Optional[dict] = None,
        uses_requests: Optional[dict] = None,
        uses_with: Optional[dict] = None,
        volumes: Optional[List[str]] = None,
        workspace: Optional[str] = None,
        **kwargs,
    ) -> Union['Flow', 'AsyncFlow']:
        """Add an Executor to the current Flow object.

        :param connection_list: dictionary JSON with a list of connections to configure
        :param daemon: The Pea attempts to terminate all of its Runtime child processes/threads on existing. setting it to true basically tell the Pea do not wait on the Runtime when closing
        :param docker_kwargs: Dictionary of kwargs arguments that will be passed to Docker SDK when starting the docker '
          container.

          More details can be found in the Docker SDK docs:  https://docker-py.readthedocs.io/en/stable/
        :param entrypoint: The entrypoint command overrides the ENTRYPOINT in Docker image. when not set then the Docker image ENTRYPOINT takes effective.
        :param env: The map of environment variables that are available inside runtime
        :param expose_public: If set, expose the public IP address to remote when necessary, by default it exposesprivate IP address, which only allows accessing under the same network/subnet. Important to set this to true when the Pea will receive input connections from remote Peas
        :param external: The Pod will be considered an external Pod that has been started independently from the Flow.This Pod will not be context managed by the Flow.
        :param force_update: If set, always pull the latest Hub Executor bundle even it exists on local
        :param gpus: This argument allows dockerized Jina executor discover local gpu devices.

              Note,
              - To access all gpus, use `--gpus all`.
              - To access multiple gpus, e.g. make use of 2 gpus, use `--gpus 2`.
              - To access specified gpus based on device id, use `--gpus device=[YOUR-GPU-DEVICE-ID]`
              - To access specified gpus based on multiple device id, use `--gpus device=[YOUR-GPU-DEVICE-ID1],device=[YOUR-GPU-DEVICE-ID2]`
              - To specify more parameters, use `--gpus device=[YOUR-GPU-DEVICE-ID],runtime=nvidia,capabilities=display
        :param host: The host address of the runtime, by default it is 0.0.0.0.
        :param host_in: The host address for binding to, by default it is 0.0.0.0
        :param install_requirements: If set, install `requirements.txt` in the Hub Executor bundle to local
        :param log_config: The YAML config of the logger used in this object.
        :param name: The name of this object.

          This will be used in the following places:
          - how you refer to this object in Python/YAML/CLI
          - visualization
          - log message header
          - ...

          When not given, then the default naming strategy will apply.
        :param native: If set, only native Executors is allowed, and the Executor is always run inside WorkerRuntime.
        :param peas_hosts: The hosts of the peas when shards greater than 1.
                  Peas will be evenly distributed among the hosts. By default,
                  peas are running on host provided by the argument ``host``
        :param polling: The polling strategy of the Pod and its endpoints (when `shards>1`).
              Can be defined for all endpoints of a Pod or by endpoint.
              Define per Pod:
              - ANY: only one (whoever is idle) Pea polls the message
              - ALL: all Peas poll the message (like a broadcast)
              Define per Endpoint:
              JSON dict, {endpoint: PollingType}
              {'/custom': 'ALL', '/search': 'ANY', '*': 'ANY'}
        :param port_in: The port for input data to bind to, default a random port between [49152, 65535]
        :param port_jinad: The port of the remote machine for usage with JinaD.
        :param pull_latest: Pull the latest image before running
        :param py_modules: The customized python modules need to be imported before loading the executor

          Note that the recommended way is to only import a single module - a simple python file, if your
          executor can be defined in a single file, or an ``__init__.py`` file if you have multiple files,
          which should be structured as a python package. For more details, please see the
          `Executor cookbook <https://docs.jina.ai/fundamentals/executor/repository-structure/>`__
        :param quiet: If set, then no log will be emitted from this object.
        :param quiet_error: If set, then exception stack information will not be added to the log
        :param quiet_remote_logs: Do not display the streaming of remote logs on local console
        :param replicas: The number of replicas in the pod
        :param runtime_backend: The parallel backend of the runtime inside the Pea
        :param runtime_cls: The runtime class to run inside the Pea
        :param shards: The number of shards in the pod running at the same time. For more details check https://docs.jina.ai/fundamentals/flow/topology/
        :param timeout_ctrl: The timeout in milliseconds of the control request, -1 for waiting forever
        :param timeout_ready: The timeout in milliseconds of a Pea waits for the runtime to be ready, -1 for waiting forever
        :param upload_files: The files on the host to be uploaded to the remote
          workspace. This can be useful when your Pod has more
          file dependencies beyond a single YAML file, e.g.
          Python files, data files.

          Note,
          - currently only flatten structure is supported, which means if you upload `[./foo/a.py, ./foo/b.pp, ./bar/c.yml]`, then they will be put under the _same_ workspace on the remote, losing all hierarchies.
          - by default, `--uses` YAML file is always uploaded.
          - uploaded files are by default isolated across the runs. To ensure files are submitted to the same workspace across different runs, use `--workspace-id` to specify the workspace.
        :param uses: The config of the executor, it could be one of the followings:
                  * an Executor YAML file (.yml, .yaml, .jaml)
                  * a Jina Hub Executor (must start with `jinahub://` or `jinahub+docker://`)
                  * a docker image (must start with `docker://`)
                  * the string literal of a YAML config (must start with `!` or `jtype: `)
                  * the string literal of a JSON config

                  When use it under Python, one can use the following values additionally:
                  - a Python dict that represents the config
                  - a text file stream has `.read()` interface
        :param uses_after: The executor attached after the Peas described by --uses, typically used for receiving from all shards, accepted type follows `--uses`
        :param uses_after_address: The address of the uses-before runtime
        :param uses_before: The executor attached after the Peas described by --uses, typically before sending to all shards, accepted type follows `--uses`
        :param uses_before_address: The address of the uses-before runtime
        :param uses_metas: Dictionary of keyword arguments that will override the `metas` configuration in `uses`
        :param uses_requests: Dictionary of keyword arguments that will override the `requests` configuration in `uses`
        :param uses_with: Dictionary of keyword arguments that will override the `with` configuration in `uses`
        :param volumes: The path on the host to be mounted inside the container.

          Note,
          - If separated by `:`, then the first part will be considered as the local host path and the second part is the path in the container system.
          - If no split provided, then the basename of that directory will be mounted into container's root path, e.g. `--volumes="/user/test/my-workspace"` will be mounted into `/my-workspace` inside the container.
          - All volumes are mounted with read-write mode.
        :param workspace: The working directory for any IO operations in this object. If not set, then derive from its parent `workspace`.
        :return: a (new) Flow object with modification

        .. # noqa: DAR202
        .. # noqa: DAR101
        .. # noqa: DAR003
        """

    # overload_inject_end_pod
    @allowed_levels([FlowBuildLevel.EMPTY])
    def add(
        self,
        *,
        needs: Optional[Union[str, Tuple[str], List[str]]] = None,
        copy_flow: bool = True,
        pod_role: 'PodRoleType' = PodRoleType.POD,
        **kwargs,
    ) -> 'Flow':
        """
        Add a Pod to the current Flow object and return the new modified Flow object.
        The attribute of the Pod can be later changed with :py:meth:`set` or deleted with :py:meth:`remove`

        .. # noqa: DAR401
        :param needs: the name of the Pod(s) that this Pod receives data from.
                           One can also use 'gateway' to indicate the connection with the gateway.
        :param pod_role: the role of the Pod, used for visualization and route planning
        :param copy_flow: when set to true, then always copy the current Flow and do the modification on top of it then return, otherwise, do in-line modification
        :param kwargs: other keyword-value arguments that the Pod CLI supports
        :return: a (new) Flow object with modification
        """
        op_flow = copy.deepcopy(self) if copy_flow else self

        # pod naming logic
        pod_name = kwargs.get('name', None)

        if pod_name in op_flow._pod_nodes:
            new_name = f'{pod_name}{len(op_flow._pod_nodes)}'
            self.logger.debug(
                f'"{pod_name}" is used in this Flow already! renamed it to "{new_name}"'
            )
            pod_name = new_name

        if not pod_name:
            pod_name = f'executor{len(op_flow._pod_nodes)}'

        if not pod_name.isidentifier():
            # hyphen - can not be used in the name
            raise ValueError(
                f'name: {pod_name} is invalid, please follow the python variable name conventions'
            )

        # needs logic
        needs = op_flow._parse_endpoints(
            op_flow, pod_name, needs, connect_to_last_pod=True
        )

        # set the kwargs inherit from `Flow(kwargs1=..., kwargs2=)`
        for key, value in op_flow._common_kwargs.items():
            if key not in kwargs:
                kwargs[key] = value

        # check if host is set to remote:port
        if 'host' in kwargs:
            m = re.match(_regex_port, kwargs['host'])
            if (
                kwargs.get('host', __default_host__) != __default_host__
                and m
                and 'port_jinad' not in kwargs
            ):
                kwargs['port_jinad'] = m.group(2)
                kwargs['host'] = m.group(1)

        # update kwargs of this Pod
        kwargs.update(dict(name=pod_name, pod_role=pod_role, num_part=len(needs)))

        parser = set_pod_parser()
        if pod_role == PodRoleType.GATEWAY:
            parser = set_gateway_parser()

        args = ArgNamespace.kwargs2namespace(
            kwargs, parser, True, fallback_parsers=FALLBACK_PARSERS
        )

        # pod workspace if not set then derive from flow workspace
        args.workspace = os.path.abspath(args.workspace or self.workspace)

        args.noblock_on_start = True
        args.extra_search_paths = self.args.extra_search_paths

        port_in = kwargs.get('port_in', None)
        if not port_in:
            port_in = helper.random_port()
            args.port_in = port_in

        op_flow._pod_nodes[pod_name] = Pod(args, needs)

        op_flow.last_pod = pod_name

        return op_flow

    @allowed_levels([FlowBuildLevel.EMPTY])
    def inspect(self, name: str = 'inspect', *args, **kwargs) -> 'Flow':
        """Add an inspection on the last changed Pod in the Flow

        Internally, it adds two Pods to the Flow. But don't worry, the overhead is minimized and you
        can remove them by simply using `Flow(inspect=FlowInspectType.REMOVE)` before using the Flow.

        .. highlight:: bash
        .. code-block:: bash

            Flow -- PUB-SUB -- BasePod(_pass) -- Flow
                    |
                    -- PUB-SUB -- InspectPod (Hanging)

        In this way, :class:`InspectPod` looks like a simple ``_pass`` from outside and
        does not introduce side-effects (e.g. changing the socket type) to the original Flow.
        The original incoming and outgoing socket types are preserved.

        This function is very handy for introducing an Evaluator into the Flow.

        .. seealso::

            :meth:`gather_inspect`

        :param name: name of the Pod
        :param args: args for .add()
        :param kwargs: kwargs for .add()
        :return: the new instance of the Flow
        """
        _last_pod = self.last_pod
        op_flow = self.add(
            name=name, needs=_last_pod, pod_role=PodRoleType.INSPECT, *args, **kwargs
        )

        # now remove uses and add an auxiliary Pod
        if 'uses' in kwargs:
            kwargs.pop('uses')
        op_flow = op_flow.add(
            name=f'_aux_{name}',
            needs=_last_pod,
            pod_role=PodRoleType.INSPECT_AUX_PASS,
            *args,
            **kwargs,
        )

        # register any future connection to _last_pod by the auxiliary Pod
        op_flow._inspect_pods[_last_pod] = op_flow.last_pod

        return op_flow

    @allowed_levels([FlowBuildLevel.EMPTY])
    def gather_inspect(
        self,
        name: str = 'gather_inspect',
        include_last_pod: bool = True,
        *args,
        **kwargs,
    ) -> 'Flow':
        """Gather all inspect Pods output into one Pod. When the Flow has no inspect Pod then the Flow itself
        is returned.

        .. note::

            If ``--no-inspect`` is **not** given, then :meth:`gather_inspect` is auto called before :meth:`build`. So
            in general you don't need to manually call :meth:`gather_inspect`.

        :param name: the name of the gather Pod
        :param include_last_pod: if to include the last modified Pod in the Flow
        :param args: args for .add()
        :param kwargs: kwargs for .add()
        :return: the modified Flow or the copy of it


        .. seealso::

            :meth:`inspect`

        """
        needs = [k for k, v in self._pod_nodes.items() if v.role == PodRoleType.INSPECT]
        if needs:
            if include_last_pod:
                needs.append(self.last_pod)
            return self.add(
                name=name,
                needs=needs,
                pod_role=PodRoleType.JOIN_INSPECT,
                *args,
                **kwargs,
            )
        else:
            # no inspect node is in the graph, return the current graph
            return self

    def _get_gateway_target(self, prefix):
        gateway_pod = self._pod_nodes[GATEWAY_NAME]
        return (
            f'{prefix}-{GATEWAY_NAME}',
            {
                'host': gateway_pod.head_host,
                'port': gateway_pod.head_port_in,
                'expected_parts': 0,
            },
        )

    @allowed_levels([FlowBuildLevel.EMPTY])
    def build(self, copy_flow: bool = False) -> 'Flow':
        """
        Build the current Flow and make it ready to use

        .. note::

            No need to manually call it since 0.0.8. When using Flow with the
            context manager, or using :meth:`start`, :meth:`build` will be invoked.

        :param copy_flow: when set to true, then always copy the current Flow and do the modification on top of it then return, otherwise, do in-line modification
        :return: the current Flow (by default)

        .. note::
            ``copy_flow=True`` is recommended if you are building the same Flow multiple times in a row. e.g.

            .. highlight:: python
            .. code-block:: python

                f = Flow()
                with f:
                    f.index()

                with f.build(copy_flow=True) as fl:
                    fl.search()


        .. # noqa: DAR401
        """

        op_flow = copy.deepcopy(self) if copy_flow else self

        if op_flow.args.inspect == FlowInspectType.COLLECT:
            op_flow.gather_inspect(copy_flow=False)

        if GATEWAY_NAME not in op_flow._pod_nodes:
            op_flow._add_gateway(
                needs={op_flow.last_pod},
                graph_description=op_flow._get_graph_representation(),
                pod_addresses=op_flow._get_pod_addresses(),
            )

        removed_pods = []

        # if set no_inspect then all inspect related nodes are removed
        if op_flow.args.inspect == FlowInspectType.REMOVE:
            filtered_pod_nodes = OrderedDict()
            for k, v in op_flow._pod_nodes.items():
                if not v.role.is_inspect:
                    filtered_pod_nodes[k] = v
                else:
                    removed_pods.append(v.name)

            op_flow._pod_nodes = filtered_pod_nodes
            reverse_inspect_map = {v: k for k, v in op_flow._inspect_pods.items()}
            while (
                len(op_flow._last_changed_pod) > 0
                and len(removed_pods) > 0
                and op_flow.last_pod in removed_pods
            ):
                op_flow._last_changed_pod.pop()

        for end, pod in op_flow._pod_nodes.items():
            # if an endpoint is being inspected, then replace it with inspected Pod
            # but not those inspect related node
            if op_flow.args.inspect.is_keep:
                pod.needs = set(
                    ep if pod.role.is_inspect else op_flow._inspect_pods.get(ep, ep)
                    for ep in pod.needs
                )
            else:
                pod.needs = set(reverse_inspect_map.get(ep, ep) for ep in pod.needs)

        hanging_pods = _hanging_pods(op_flow)
        if hanging_pods:
            op_flow.logger.warning(
                f'{hanging_pods} are hanging in this flow with no pod receiving from them, '
                f'you may want to double check if it is intentional or some mistake'
            )
        op_flow._build_level = FlowBuildLevel.GRAPH
        if len(removed_pods) > 0:
            # very dirty
            op_flow._pod_nodes[GATEWAY_NAME].args.graph_description = json.dumps(
                op_flow._get_graph_representation()
            )
            op_flow._pod_nodes[GATEWAY_NAME].args.pod_addresses = json.dumps(
                op_flow._get_pod_addresses()
            )

            op_flow._pod_nodes[GATEWAY_NAME].update_pea_args()
        return op_flow

    def __call__(self, *args, **kwargs):
        """Builds the Flow
        :param args: args for build
        :param kwargs: kwargs for build
        :return: the built Flow
        """
        return self.build(*args, **kwargs)

    def __enter__(self):
        with CatchAllCleanupContextManager(self):
            return self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if hasattr(self, '_stop_event'):
            self._stop_event.set()

        super().__exit__(exc_type, exc_val, exc_tb)

        # unset all envs to avoid any side-effect
        if self.args.env:
            for k in self.args.env.keys():
                os.environ.pop(k, None)

        # do not know why but removing these 2 lines make 2 tests fail
        if GATEWAY_NAME in self._pod_nodes:
            self._pod_nodes.pop(GATEWAY_NAME)

        self._build_level = FlowBuildLevel.EMPTY

        self.logger.debug('Flow is closed!')
        self.logger.close()

    def start(self):
        """Start to run all Pods in this Flow.

        Remember to close the Flow with :meth:`close`.

        Note that this method has a timeout of ``timeout_ready`` set in CLI,
        which is inherited all the way from :class:`jina.peapods.peas.Pea`


        .. # noqa: DAR401

        :return: this instance
        """
        if self._build_level.value < FlowBuildLevel.GRAPH.value:
            self.build(copy_flow=False)

        # set env only before the Pod get started
        if self.args.env:
            for k, v in self.args.env.items():
                os.environ[k] = str(v)

        for k, v in self:
            if not getattr(v.args, 'external', False):
                self.enter_context(v)

        self._wait_until_all_ready()

        self._build_level = FlowBuildLevel.RUNNING

        return self

    def _wait_until_all_ready(self):
        results = {}
        threads = []

        def _wait_ready(_pod_name, _pod):
            try:
                if not getattr(_pod.args, 'external', False):
                    results[_pod_name] = 'pending'
                    _pod.wait_start_success()
                    results[_pod_name] = 'done'
            except Exception as ex:
                results[_pod_name] = repr(ex)

        def _polling_status():
            spinner = itertools.cycle(
                ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
            )

            while True:
                num_all = len(results)
                num_done = 0
                pendings = []
                for _k, _v in results.items():
                    sys.stdout.flush()
                    if _v == 'pending':
                        pendings.append(_k)
                    else:
                        num_done += 1
                sys.stdout.write('\r{}\r'.format(' ' * 100))
                pending_str = colored(' '.join(pendings)[:50], 'yellow')
                sys.stdout.write(
                    f'{colored(next(spinner), "green")} {num_done}/{num_all} waiting {pending_str} to be ready...'
                )
                sys.stdout.flush()

                if not pendings:
                    sys.stdout.write('\r{}\r'.format(' ' * 100))
                    break
                time.sleep(0.1)

        # kick off all pods wait-ready threads
        for k, v in self:
            t = threading.Thread(
                target=_wait_ready,
                args=(
                    k,
                    v,
                ),
                daemon=True,
            )
            threads.append(t)
            t.start()

        # kick off spinner thread
        t_m = threading.Thread(target=_polling_status, daemon=True)
        t_m.start()

        # kick off ip getter thread
        addr_table = []
        t_ip = threading.Thread(
            target=self._get_address_table, args=(addr_table,), daemon=True
        )
        t_ip.start()

        for t in threads:
            t.join()
        if t_ip is not None:
            t_ip.join()
        t_m.join()

        error_pods = [k for k, v in results.items() if v != 'done']
        if error_pods:
            self.logger.error(
                f'Flow is aborted due to {error_pods} can not be started.'
            )
            self.close()
            raise RuntimeFailToStart
        else:
            success_msg = colored('🎉 Flow is ready to use!', 'green')

            if addr_table:
                self.logger.info(success_msg + '\n' + '\n'.join(addr_table))
            self.logger.debug(
                f'{self.num_pods} Pods (i.e. {self.num_peas} Peas) are running in this Flow'
            )

    @property
    def num_pods(self) -> int:
        """Get the number of Pods in this Flow


        .. # noqa: DAR201"""
        return len(self._pod_nodes)

    @property
    def num_peas(self) -> int:
        """Get the number of peas (shards count) in this Flow


        .. # noqa: DAR201"""
        return sum(v.num_peas for v in self._pod_nodes.values())

    def __eq__(self, other: 'Flow') -> bool:
        """
        Compare the topology of a Flow with another Flow.
        Identification is defined by whether two flows share the same set of edges.

        :param other: the second Flow object
        :return: result of equality check
        """

        if self._build_level.value < FlowBuildLevel.GRAPH.value:
            op_flow = copy.deepcopy(self)
            a = op_flow.build()
        else:
            a = self

        if other._build_level.value < FlowBuildLevel.GRAPH.value:
            op_flow_b = copy.deepcopy(other)
            b = op_flow_b.build()
        else:
            b = other

        return a._pod_nodes == b._pod_nodes

    @property
    def client(self) -> 'BaseClient':
        """Return a :class:`BaseClient` object attach to this Flow.

        .. # noqa: DAR201"""

        kwargs = dict(
            host=self.host,
            port=self.port_expose,
            protocol=self.protocol,
            results_as_docarray=True,
        )
        kwargs.update(self._common_kwargs)
        return Client(**kwargs)

    @property
    def _mermaid_str(self):
        mermaid_graph = [
            '''
            %%{init:{
  "theme": "base",
  "themeVariables": {
      "primaryColor": "#fff",
      "primaryBorderColor": "#fff",
      "mainBkg": "#32C8CD",
      "clusterBkg": "#EEEDE78C",
      "secondaryBorderColor": "none",
      "tertiaryBorderColor": "none",
      "lineColor": "#a6d8da"
      }
}}%%
            '''.replace(
                '\n', ''
            ),
            'flowchart LR;',
        ]

        pod_nodes = []

        # plot subgraphs
        for node, v in self._pod_nodes.items():
            pod_nodes.append(v.name)
            mermaid_graph.extend(v._mermaid_str)

        for node, v in self._pod_nodes.items():
            for need in sorted(v.needs):
                need_print = need
                if need == 'gateway':
                    need_print = 'gatewaystart[gateway]'
                node_print = node
                if node == 'gateway':
                    node_print = 'gatewayend[gateway]'

                _s_role = self._pod_nodes[need].role
                _e_role = self._pod_nodes[node].role
                if getattr(self._pod_nodes[need].args, 'external', False):
                    _s_role = 'EXTERNAL'
                if getattr(self._pod_nodes[node].args, 'external', False):
                    _e_role = 'EXTERNAL'
                line_st = '-->'
                if _s_role == PodRoleType.INSPECT or _e_role == PodRoleType.INSPECT:
                    line_st = '-.->'
                mermaid_graph.append(
                    f'{need_print}:::{str(_s_role)} {line_st} {node_print}:::{str(_e_role)};'
                )

        mermaid_graph.append(f'classDef {str(PodRoleType.INSPECT)} stroke:#F29C9F')

        mermaid_graph.append(f'classDef {str(PodRoleType.JOIN_INSPECT)} stroke:#F29C9F')
        mermaid_graph.append(
            f'classDef {str(PodRoleType.GATEWAY)} fill:none,color:#000,stroke:none'
        )
        mermaid_graph.append(
            f'classDef {str(PodRoleType.INSPECT_AUX_PASS)} stroke-dasharray: 2 2'
        )
        mermaid_graph.append(f'classDef HEADTAIL fill:#32C8CD1D')

        mermaid_graph.append(f'\nclassDef EXTERNAL fill:#fff,stroke:#32C8CD')

        return '\n'.join(mermaid_graph)

    def plot(
        self,
        output: Optional[str] = None,
        vertical_layout: bool = False,
        inline_display: bool = False,
        build: bool = True,
        copy_flow: bool = True,
    ) -> 'Flow':
        """
        Visualize the Flow up to the current point
        If a file name is provided it will create a jpg image with that name,
        otherwise it will display the URL for mermaid.
        If called within IPython notebook, it will be rendered inline,
        otherwise an image will be created.

        Example,

        .. highlight:: python
        .. code-block:: python

            flow = Flow().add(name='pod_a').plot('flow.svg')

        :param output: a filename specifying the name of the image to be created,
                    the suffix svg/jpg determines the file type of the output image
        :param vertical_layout: top-down or left-right layout
        :param inline_display: show image directly inside the Jupyter Notebook
        :param build: build the Flow first before plotting, gateway connection can be better showed
        :param copy_flow: when set to true, then always copy the current Flow and
                do the modification on top of it then return, otherwise, do in-line modification
        :return: the Flow
        """

        # deepcopy causes the below error while reusing a Flow in Jupyter
        # 'Pickling an AuthenticationString object is disallowed for security reasons'
        op_flow = copy.deepcopy(self) if copy_flow else self

        if build:
            op_flow.build(False)

        mermaid_str = op_flow._mermaid_str
        if vertical_layout:
            mermaid_str = mermaid_str.replace('flowchart LR', 'flowchart TD')

        image_type = 'svg'
        if output and not output.endswith('svg'):
            image_type = 'img'

        url = op_flow._mermaid_to_url(mermaid_str, image_type)
        showed = False
        if inline_display:
            try:
                from IPython.display import display, Image

                display(Image(url=url))
                showed = True
            except:
                # no need to panic users
                pass

        if output:
            download_mermaid_url(url, output)
        elif not showed:
            op_flow.logger.info(f'flow visualization: {url}')

        return self

    def _ipython_display_(self):
        """Displays the object in IPython as a side effect"""
        self.plot(
            inline_display=True, build=(self._build_level != FlowBuildLevel.GRAPH)
        )

    def _mermaid_to_url(self, mermaid_str: str, img_type: str) -> str:
        """
        Render the current Flow as URL points to a SVG. It needs internet connection

        :param mermaid_str: the mermaid representation
        :param img_type: image type (svg/jpg)
        :return: the url points to a SVG
        """
        encoded_str = base64.b64encode(bytes(mermaid_str, 'utf-8')).decode('utf-8')

        return f'https://mermaid.ink/{img_type}/{encoded_str}'

    @property
    def port_expose(self) -> int:
        """Return the exposed port of the gateway
        .. # noqa: DAR201
        """
        if GATEWAY_NAME in self._pod_nodes:
            return self._pod_nodes[GATEWAY_NAME].args.port_expose
        else:
            return self._common_kwargs.get('port_expose', None)

    @port_expose.setter
    def port_expose(self, value: int):
        """Set the new exposed port of the Flow (affects Gateway and Client)

        :param value: the new port to expose
        """
        self._common_kwargs['port_expose'] = value

        # Flow is build to graph already
        if self._build_level >= FlowBuildLevel.GRAPH:
            self[GATEWAY_NAME].args.port_expose = self._common_kwargs['port_expose']

        # Flow is running already, then close the existing gateway
        if self._build_level >= FlowBuildLevel.RUNNING:
            self[GATEWAY_NAME].close()
            self.enter_context(self[GATEWAY_NAME])
            self[GATEWAY_NAME].wait_start_success()

    @property
    def host(self) -> str:
        """Return the local address of the gateway
        .. # noqa: DAR201
        """
        if GATEWAY_NAME in self._pod_nodes:
            return self._pod_nodes[GATEWAY_NAME].host
        else:
            return self._common_kwargs.get('host', __default_host__)

    @host.setter
    def host(self, value: str):
        """Set the new host of the Flow (affects Gateway and Client)

        :param value: the new port to expose
        """
        self._common_kwargs['host'] = value

        # Flow is build to graph already
        if self._build_level >= FlowBuildLevel.GRAPH:
            self[GATEWAY_NAME].args.host = self._common_kwargs['host']

        # Flow is running already, then close the existing gateway
        if self._build_level >= FlowBuildLevel.RUNNING:
            self[GATEWAY_NAME].close()
            self.enter_context(self[GATEWAY_NAME])
            self[GATEWAY_NAME].wait_start_success()

    @property
    def address_private(self) -> str:
        """Return the private IP address of the gateway for connecting from other machine in the same network


        .. # noqa: DAR201"""
        return get_internal_ip()

    @property
    def address_public(self) -> str:
        """Return the public IP address of the gateway for connecting from other machine in the public network


        .. # noqa: DAR201"""
        return get_public_ip()

    def __iter__(self):
        return self._pod_nodes.items().__iter__()

    def _get_address_table(self, address_table):
        address_table.extend(
            [
                f'\t🔗 Protocol: \t\t{colored(self.protocol, attrs="bold")}',
                f'\t🏠 Local access:\t'
                + colored(f'{self.host}:{self.port_expose}', 'cyan', attrs='underline'),
                f'\t🔒 Private network:\t'
                + colored(
                    f'{self.address_private}:{self.port_expose}',
                    'cyan',
                    attrs='underline',
                ),
            ]
        )
        if self.address_public:
            address_table.append(
                f'\t🌐 Public address:\t'
                + colored(
                    f'{self.address_public}:{self.port_expose}',
                    'cyan',
                    attrs='underline',
                )
            )
        if self.protocol == GatewayProtocolType.HTTP:
            address_table.append(
                f'\t💬 Swagger UI:\t\t'
                + colored(
                    f'http://localhost:{self.port_expose}/docs',
                    'cyan',
                    attrs='underline',
                )
            )
            address_table.append(
                f'\t📚 Redoc:\t\t'
                + colored(
                    f'http://localhost:{self.port_expose}/redoc',
                    'cyan',
                    attrs='underline',
                )
            )
        return address_table

    def block(
        self, stop_event: Optional[Union[threading.Event, multiprocessing.Event]] = None
    ):
        """Block the Flow until `stop_event` is set or user hits KeyboardInterrupt

        :param stop_event: a threading event or a multiprocessing event that onces set will resume the control Flow
            to main thread.
        """
        try:
            if stop_event is None:
                self._stop_event = (
                    threading.Event()
                )  #: this allows `.close` to close the Flow from another thread/proc
                self._stop_event.wait()
            else:
                stop_event.wait()
        except KeyboardInterrupt:
            pass

    @property
    def protocol(self) -> GatewayProtocolType:
        """Return the protocol of this Flow

        :return: the protocol of this Flow
        """
        v = self._common_kwargs.get('protocol', GatewayProtocolType.GRPC)
        if isinstance(v, str):
            v = GatewayProtocolType.from_string(v)
        return v

    @protocol.setter
    def protocol(self, value: Union[str, GatewayProtocolType]):
        """Set the protocol of this Flow, can only be set before the Flow has been started

        :param value: the protocol to set
        """
        # Flow is running already, protocol cant be changed anymore
        if self._build_level >= FlowBuildLevel.RUNNING:
            raise RuntimeError('Protocol can not be changed after the Flow has started')

        if isinstance(value, str):
            self._common_kwargs['protocol'] = GatewayProtocolType.from_string(value)
        elif isinstance(value, GatewayProtocolType):
            self._common_kwargs['protocol'] = value
        else:
            raise TypeError(f'{value} must be either `str` or `GatewayProtocolType`')

        # Flow is build to graph already
        if self._build_level >= FlowBuildLevel.GRAPH:
            self[GATEWAY_NAME].args.protocol = self._common_kwargs['protocol']

    def __getitem__(self, item):
        if isinstance(item, str):
            return self._pod_nodes[item]
        elif isinstance(item, int):
            return list(self._pod_nodes.values())[item]
        else:
            raise TypeError(f'{typename(item)} is not supported')

    @property
    def workspace(self) -> str:
        """Return the workspace path of the flow.

        .. # noqa: DAR201"""
        return os.path.abspath(self.args.workspace or './')

    @workspace.setter
    def workspace(self, value: str):
        """set workspace dir for flow & all pods

        :param value: workspace to be set
        """
        self.args.workspace = value
        for k, p in self:
            p.args.workspace = value
            p.update_pea_args()

    @property
    def workspace_id(self) -> Dict[str, str]:
        """Get all Pods' ``workspace_id`` values in a dict


        .. # noqa: DAR201"""
        return {
            k: p.args.workspace_id for k, p in self if hasattr(p.args, 'workspace_id')
        }

    @workspace_id.setter
    def workspace_id(self, value: str):
        """Set all Pods' ``workspace_id`` to ``value``

        :param value: a hexadecimal UUID string
        """
        uuid.UUID(value)
        for k, p in self:
            if hasattr(p.args, 'workspace_id'):
                p.args.workspace_id = value
                args = getattr(p, 'peas_args', getattr(p, 'shards_args', None))
                if args is None:
                    raise ValueError(
                        f'could not find "peas_args" or "shards_args" on {p}'
                    )
                values = None
                if isinstance(args, dict):
                    values = args.values()
                elif isinstance(args, list):
                    values = args
                for v in values:
                    if v and isinstance(v, argparse.Namespace):
                        v.workspace_id = value
                    if v and isinstance(v, List):
                        for i in v:
                            i.workspace_id = value

    @property
    def env(self) -> Optional[Dict]:
        """Get all envs to be set in the Flow

        :return: envs as dict
        """
        return self.args.env

    @env.setter
    def env(self, value: Dict[str, str]):
        """set env vars for flow & all pods.
        This can be used by jinad to set envs for Flow and all child objects

        :param value: value to be set
        """
        self.args.env = value
        for k, v in self:
            v.args.env = value

    @property
    def identity(self) -> Dict[str, str]:
        """Get all Pods' ``identity`` values in a dict


        .. # noqa: DAR201
        """
        return {k: p.args.identity for k, p in self}

    @identity.setter
    def identity(self, value: str):
        """Set all Pods' ``identity`` to ``value``

        :param value: a hexadecimal UUID string
        """
        uuid.UUID(value)
        # Re-initiating logger with new identity
        self.logger = JinaLogger(self.__class__.__name__, **vars(self.args))
        for _, p in self:
            p.args.identity = value

    @overload
    def expose_endpoint(self, exec_endpoint: str, path: Optional[str] = None):
        """Expose an Executor's endpoint (defined by `@requests(on=...)`) to HTTP endpoint for easier access.

        After expose, you can send data request directly to `http://hostname:port/endpoint`.

        :param exec_endpoint: the endpoint string, by convention starts with `/`
        :param path: the HTTP endpoint string, when not given, it is `exec_endpoint`
        """
        ...

    @overload
    def expose_endpoint(
        self,
        exec_endpoint: str,
        *,
        path: Optional[str] = None,
        status_code: int = 200,
        tags: Optional[List[str]] = None,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        response_description: str = 'Successful Response',
        deprecated: Optional[bool] = None,
        methods: Optional[List[str]] = None,
        operation_id: Optional[str] = None,
        response_model_by_alias: bool = True,
        response_model_exclude_unset: bool = False,
        response_model_exclude_defaults: bool = False,
        response_model_exclude_none: bool = False,
        include_in_schema: bool = True,
        name: Optional[str] = None,
    ):
        """Expose an Executor's endpoint (defined by `@requests(on=...)`) to HTTP endpoint for easier access.

        After expose, you can send data request directly to `http://hostname:port/endpoint`.

        Use this method to specify your HTTP endpoint with richer semantic and schema.

        :param exec_endpoint: the endpoint string, by convention starts with `/`

        # noqa: DAR101
        """
        ...

    def expose_endpoint(self, exec_endpoint: str, **kwargs):
        """Expose an Executor's endpoint (defined by `@requests(on=...)`) to HTTP endpoint for easier access.

        After expose, you can send data request directly to `http://hostname:port/endpoint`.

        :param exec_endpoint: the endpoint string, by convention starts with `/`

        # noqa: DAR101
        # noqa: DAR102
        """
        self._endpoints_mapping[exec_endpoint] = kwargs

    # for backward support
    join = needs

    def rolling_update(
        self,
        pod_name: str,
        uses_with: Optional[Dict] = None,
    ):
        """
        Reload all replicas of a pod sequentially

        :param pod_name: pod to update
        :param uses_with: a Dictionary of arguments to restart the executor with
        """
        from jina.helper import run_async

        run_async(
            self._pod_nodes[pod_name].rolling_update,
            uses_with=uses_with,
            any_event_loop=True,
        )

    def to_k8s_yaml(
        self,
        output_base_path: str,
        k8s_namespace: Optional[str] = None,
        k8s_connection_pool: bool = True,
    ):
        """
        Converts the Flow into a set of yaml deployments to deploy in Kubernetes
        :param output_base_path: The base path where to dump all the yaml files
        :param k8s_namespace: The name of the k8s namespace to set for the configurations. If None, the name of the Flow will be used.
        :param k8s_connection_pool: Boolean indicating wether the kubernetes connection pool should be used inside the Executor Runtimes.
        """
        import yaml

        if self._build_level.value < FlowBuildLevel.GRAPH.value:
            self.build(copy_flow=False)

        from jina.peapods.pods.config.k8s import K8sPodConfig

        k8s_namespace = k8s_namespace or self.args.name or 'default'

        for node, v in self._pod_nodes.items():
            pod_base = os.path.join(output_base_path, node)
            k8s_pod = K8sPodConfig(
                args=v.args,
                k8s_namespace=k8s_namespace,
                k8s_connection_pool=k8s_connection_pool,
                k8s_pod_addresses=self._get_k8s_pod_addresses(k8s_namespace)
                if (node == 'gateway' and not k8s_connection_pool)
                else None,
            )
            configs = k8s_pod.to_k8s_yaml()
            for name, k8s_objects in configs:
                filename = os.path.join(pod_base, f'{name}.yml')
                os.makedirs(pod_base, exist_ok=True)
                with open(filename, 'w+') as fp:
                    for i, k8s_object in enumerate(k8s_objects):
                        yaml.dump(k8s_object, fp)
                        if i < len(k8s_objects) - 1:
                            fp.write('---\n')

    def to_docker_compose_yaml(
        self, output_path: Optional[str] = None, network_name: Optional[str] = None
    ):
        """
        Converts the Flow into a yaml file to run with `docker-compose up`
        :param output_path: The output path for the yaml file
        :param network_name: The name of the network that will be used by the deployment name
        """
        import yaml

        if self._build_level.value < FlowBuildLevel.GRAPH.value:
            self.build(copy_flow=False)

        output_path = output_path or 'docker-compose.yml'
        network_name = network_name or 'jina-network'

        from jina.peapods.pods.config.docker_compose import DockerComposeConfig

        docker_compose_dict = {
            'version': '3.3',
            'networks': {network_name: {'driver': 'bridge'}},
        }

        services = {}

        for node, v in self._pod_nodes.items():
            docker_compose_pod = DockerComposeConfig(
                args=v.args,
                pod_addresses=self._get_docker_compose_pod_addresses(),
            )
            service_configs = docker_compose_pod.to_docker_compose_config()
            for service_name, service in service_configs:
                service['networks'] = [network_name]
                services[service_name] = service

        docker_compose_dict['services'] = services
        with open(output_path, 'w+') as fp:
            yaml.dump(docker_compose_dict, fp, sort_keys=False)

    def scale(
        self,
        pod_name: str,
        replicas: int,
    ):
        """
        Scale the amount of replicas of a given Executor.

        :param pod_name: pod to update
        :param replicas: The number of replicas to scale to
        """

        # TODO when replicas-host is ready, needs to be passed here

        from jina.helper import run_async

        run_async(
            self._pod_nodes[pod_name].scale,
            replicas=replicas,
            any_event_loop=True,
        )

    @property
    def client_args(self) -> argparse.Namespace:
        """Get Client settings.

        # noqa: DAR201
        """
        if 'port_expose' in self._common_kwargs:
            kwargs = copy.deepcopy(self._common_kwargs)
            kwargs['port'] = self._common_kwargs['port_expose']

        return ArgNamespace.kwargs2namespace(kwargs, set_client_cli_parser())

    @property
    def gateway_args(self) -> argparse.Namespace:
        """Get Gateway settings.

        # noqa: DAR201
        """
        return ArgNamespace.kwargs2namespace(self._common_kwargs, set_gateway_parser())

    def update_network_interface(self, **kwargs):
        """Update the network interface of this Flow (affects Gateway & Client)

        :param kwargs: new network settings
        """
        self._common_kwargs.update(kwargs)
