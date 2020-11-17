__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import argparse
import base64
import copy
import os
import tempfile
import threading
import time
from collections import OrderedDict, defaultdict
from contextlib import ExitStack
from typing import Optional, Union, Tuple, List, Set, Dict, Iterator, Callable, Type, TextIO, Any
from urllib.request import Request, urlopen

import ruamel.yaml
from ruamel.yaml import StringIO

from .builder import build_required, _build_flow, _optimize_flow, _hanging_pods
from .. import JINA_GLOBAL
from ..enums import FlowBuildLevel, PodRoleType, FlowInspectType
from ..excepts import FlowTopologyError, FlowMissingPodError
from ..helper import yaml, expand_env_var, get_non_defaults_args, deprecated_alias, complete_path, colored, \
    get_public_ip, get_internal_ip
from ..logging import JinaLogger
from ..logging.sse import start_sse_logger
from ..peapods.pod import FlowPod, GatewayFlowPod

if False:
    from ..proto import jina_pb2
    import argparse
    import numpy as np


class Flow(ExitStack):
    def __init__(self, args: Optional['argparse.Namespace'] = None, **kwargs):
        """Initialize a flow object

        :param kwargs: other keyword arguments that will be shared by all pods in this flow


        More explain on ``optimize_level``:

        As an example, the following flow will generate 6 Peas,

        .. highlight:: python
        .. code-block:: python

            f = Flow(optimize_level=FlowOptimizeLevel.NONE).add(uses='forward', parallel=3)

        The optimized version, i.e. :code:`Flow(optimize_level=FlowOptimizeLevel.FULL)`
        will generate 4 Peas, but it will force the :class:`GatewayPea` to take BIND role,
        as the head and tail routers are removed.

        """
        super().__init__()
        self._pod_nodes = OrderedDict()  # type: Dict[str, 'FlowPod']
        self._inspect_pods = {}  # type: Dict[str, str]
        self._build_level = FlowBuildLevel.EMPTY
        self._last_changed_pod = ['gateway']  #: default first pod is gateway, will add when build()
        self._update_args(args, **kwargs)
        if isinstance(self.args, argparse.Namespace):
            self.logger = JinaLogger(self.__class__.__name__, **vars(self.args))
        else:
            self.logger = JinaLogger(self.__class__.__name__)

    def _update_args(self, args, **kwargs):
        from ..parser import set_flow_parser
        _flow_parser = set_flow_parser()
        if args is None:
            from ..helper import get_parsed_args
            _, args, _ = get_parsed_args(kwargs, _flow_parser, 'Flow')

        self.args = args
        self._common_kwargs = kwargs
        self._kwargs = get_non_defaults_args(args, _flow_parser)  #: for yaml dump

    @classmethod
    def to_yaml(cls, representer, data):
        """Required by :mod:`ruamel.yaml.constructor` """
        tmp = data._dump_instance_to_yaml(data)
        representer.sort_base_mapping_type_on_output = False
        return representer.represent_mapping('!' + cls.__name__, tmp)

    @staticmethod
    def _dump_instance_to_yaml(data):
        # note: we only save non-default property for the sake of clarity
        r = {}

        if data._kwargs:
            r['with'] = data._kwargs

        if data._pod_nodes:
            r['pods'] = {}

        if 'gateway' in data._pod_nodes:
            # always dump gateway as the first pod, if exist
            r['pods']['gateway'] = {}

        for k, v in data._pod_nodes.items():
            if k == 'gateway':
                continue

            kwargs = {'needs': list(v.needs)} if v.needs else {}
            kwargs.update(v._kwargs)

            if 'name' in kwargs:
                kwargs.pop('name')

            r['pods'][k] = kwargs
        return r

    @classmethod
    def from_yaml(cls, constructor, node):
        """Required by :mod:`ruamel.yaml.constructor` """
        return cls._get_instance_from_yaml(constructor, node)[0]

    def save_config(self, filename: str = None) -> bool:
        """
        Serialize the object to a yaml file

        :param filename: file path of the yaml file, if not given then :attr:`config_abspath` is used
        :return: successfully dumped or not
        """
        f = filename
        if not f:
            f = tempfile.NamedTemporaryFile('w', delete=False, dir=os.environ.get('JINA_EXECUTOR_WORKDIR', None)).name
        yaml.register_class(Flow)

        with open(f, 'w', encoding='utf8') as fp:
            yaml.dump(self, fp)
        self.logger.info(f'{self}\'s yaml config is save to {f}')
        return True

    @property
    def yaml_spec(self):
        yaml.register_class(Flow)
        stream = StringIO()
        yaml.dump(self, stream)
        return stream.getvalue().strip()

    @classmethod
    def load_config(cls: Type['Flow'], filename: Union[str, TextIO]) -> 'Flow':
        """Build an executor from a YAML file.

        :param filename: the file path of the YAML file or a ``TextIO`` stream to be loaded from
        :return: an executor object
        """
        yaml.register_class(Flow)
        if not filename: raise FileNotFoundError
        if isinstance(filename, str):
            # deserialize from the yaml
            filename = complete_path(filename)
            with open(filename, encoding='utf8') as fp:
                return yaml.load(fp)
        else:
            with filename:
                return yaml.load(filename)

    @classmethod
    def _get_instance_from_yaml(cls, constructor, node):

        data = ruamel.yaml.constructor.SafeConstructor.construct_mapping(
            constructor, node, deep=True)

        p = data.get('with', {})  # type: Dict[str, Any]
        a = p.pop('args') if 'args' in p else ()
        k = p.pop('kwargs') if 'kwargs' in p else {}
        # maybe there are some hanging kwargs in "parameters"
        tmp_a = (expand_env_var(v) for v in a)
        tmp_p = {kk: expand_env_var(vv) for kk, vv in {**k, **p}.items()}
        obj = cls(*tmp_a, **tmp_p)

        pp = data.get('pods', {})
        for pod_name, pod_attr in pp.items():
            p_pod_attr = {kk: expand_env_var(vv) for kk, vv in pod_attr.items()}
            if pod_name != 'gateway':
                # ignore gateway when reading, it will be added during build()
                obj.add(name=pod_name, **p_pod_attr, copy_flow=False)

        obj.logger.success(f'successfully built {cls.__name__} from a yaml config')

        # if node.tag in {'!CompoundExecutor'}:
        #     os.environ['JINA_WARN_UNNAMED'] = 'YES'

        return obj, data

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

        if isinstance(endpoint, list) or isinstance(endpoint, tuple):
            for idx, s in enumerate(endpoint):
                if s == pod_name:
                    raise FlowTopologyError('the income/output of a pod can not be itself')
        else:
            raise ValueError(f'endpoint={endpoint} is not parsable')

        # if an endpoint is being inspected, then replace it with inspected Pod
        endpoint = set(op_flow._inspect_pods.get(ep, ep) for ep in endpoint)
        return endpoint

    @property
    def last_pod(self):
        return self._last_changed_pod[-1]

    @last_pod.setter
    def last_pod(self, name: str):
        """
        Set a pod as the last pod in the flow, useful when modifying the flow.

        :param name: the name of the existing pod
        :param copy_flow: when set to true, then always copy the current flow and do the modification on top of it then return, otherwise, do in-line modification
        :return: a (new) flow object with modification
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

    def _add_gateway(self, needs, **kwargs):
        pod_name = 'gateway'

        kwargs.update(self._common_kwargs)
        kwargs['name'] = 'gateway'
        self._pod_nodes[pod_name] = GatewayFlowPod(kwargs, needs)

    def needs(self, needs: Union[Tuple[str], List[str]],
              name: str = 'joiner', *args, **kwargs) -> 'Flow':
        """
        Add a blocker to the flow, wait until all peas defined in **needs** completed.

        :param needs: list of service names to wait
        :param name: the name of this joiner, by default is ``joiner``
        :return: the modified flow
        """
        if len(needs) <= 1:
            raise FlowTopologyError('no need to wait for a single service, need len(needs) > 1')
        return self.add(name=name, needs=needs, pod_role=PodRoleType.JOIN, *args, **kwargs)

    def add(self,
            needs: Union[str, Tuple[str], List[str]] = None,
            copy_flow: bool = True,
            pod_role: 'PodRoleType' = PodRoleType.POD,
            **kwargs) -> 'Flow':
        """
        Add a pod to the current flow object and return the new modified flow object.
        The attribute of the pod can be later changed with :py:meth:`set` or deleted with :py:meth:`remove`

        Note there are shortcut versions of this method.
        Recommend to use :py:meth:`add_encoder`, :py:meth:`add_preprocessor`,
        :py:meth:`add_router`, :py:meth:`add_indexer` whenever possible.

        :param needs: the name of the pod(s) that this pod receives data from.
                           One can also use 'pod.Gateway' to indicate the connection with the gateway.
        :param pod_role: the role of the Pod, used for visualization and route planning
        :param copy_flow: when set to true, then always copy the current flow and do the modification on top of it then return, otherwise, do in-line modification
        :param kwargs: other keyword-value arguments that the pod CLI supports
        :return: a (new) flow object with modification
        """

        op_flow = copy.deepcopy(self) if copy_flow else self

        pod_name = kwargs.get('name', None)

        if pod_name in op_flow._pod_nodes:
            new_name = f'{pod_name}{len(op_flow._pod_nodes)}'
            self.logger.debug(f'"{pod_name}" is used in this Flow already! renamed it to "{new_name}"')
            pod_name = new_name

        if not pod_name:
            pod_name = f'pod{len(op_flow._pod_nodes)}'

        if not pod_name.isidentifier():
            # hyphen - can not be used in the name
            raise ValueError(f'name: {pod_name} is invalid, please follow the python variable name conventions')

        needs = op_flow._parse_endpoints(op_flow, pod_name, needs, connect_to_last_pod=True)

        for key, value in op_flow._common_kwargs.items():
            if key not in kwargs:
                kwargs[key] = value

        kwargs['name'] = pod_name
        kwargs['log-id'] = self.args.log_id
        kwargs['num_part'] = len(needs)

        op_flow._pod_nodes[pod_name] = self._invoke_flowpod(kwargs, needs, pod_role)
        op_flow.last_pod = pod_name

        return op_flow

    def _invoke_flowpod(self, kwargs: Dict, needs: Set[str], pod_role: 'PodRoleType'):
        """This gets inherited in jinad"""
        return FlowPod(kwargs=kwargs, needs=needs, pod_role=pod_role)

    def inspect(self, name: str = 'inspect', *args, **kwargs) -> 'Flow':
        """Add an inspection on the last changed Pod in the Flow

        Internally, it adds two pods to the flow. But no worry, the overhead is minimized and you
        can remove them by simply give `Flow(inspect=FlowInspectType.REMOVE)` before using the flow.

        .. highlight:: bash
        .. code-block:: bash

            Flow -- PUB-SUB -- BasePod(_pass) -- Flow
                    |
                    -- PUB-SUB -- InspectPod (Hanging)

        In this way, :class:`InspectPod` looks like a simple ``_pass`` from outside and
        does not introduce side-effect (e.g. changing the socket type) to the original flow.
        The original incoming and outgoing socket types are preserved.

        This function is very handy for introducing evaluator into the flow.

        .. seealso::

            :meth:`gather_inspect`

        """

        _last_pod = self.last_pod
        op_flow = self.add(name=name, needs=_last_pod, pod_role=PodRoleType.INSPECT, *args, **kwargs)

        # now remove uses and add an auxiliary Pod
        if 'uses' in kwargs:
            kwargs.pop('uses')
        op_flow = op_flow.add(name=f'_aux_{name}', needs=_last_pod,
                              pod_role=PodRoleType.INSPECT_AUX_PASS, *args, **kwargs)

        # register any future connection to _last_pod by the auxiliary pod
        op_flow._inspect_pods[_last_pod] = op_flow.last_pod

        return op_flow

    def gather_inspect(self, name: str = 'gather_inspect', uses='_merge_eval', include_last_pod: bool = True, *args,
                       **kwargs) -> 'Flow':
        """ Gather all inspect pods output into one pod. When the flow has no inspect pod then the flow itself
        is returned.

        .. note::

            If ``--no-inspect`` is **not** given, then :meth:`gather_inspect` is auto called before :meth:`build`. So
            in general you don't need to manually call :meth:`gather_inspect`.

        :param name: the name of the gather pod
        :param uses: the config of the executor, by default is ``_pass``
        :param include_last_pod: if to include the last modified pod in the flow
        :param args:
        :param kwargs:
        :return: the modified flow or the copy of it


        .. seealso::

            :meth:`inspect`

        """

        needs = [k for k, v in self._pod_nodes.items() if v.role == PodRoleType.INSPECT]
        if needs:
            if include_last_pod:
                needs.append(self.last_pod)
            return self.add(name=name, uses=uses, needs=needs, pod_role=PodRoleType.JOIN_INSPECT, *args, **kwargs)
        else:
            # no inspect node is in the graph, return the current graph
            return self

    def build(self, copy_flow: bool = False) -> 'Flow':
        """
        Build the current flow and make it ready to use

        .. note::

            No need to manually call it since 0.0.8. When using flow with the
            context manager, or using :meth:`start`, :meth:`build` will be invoked.

        :param copy_flow: when set to true, then always copy the current flow and do the modification on top of it then return, otherwise, do in-line modification
        :return: the current flow (by default)

        .. note::
            ``copy_flow=True`` is recommended if you are building the same flow multiple times in a row. e.g.

            .. highlight:: python
            .. code-block:: python

                f = Flow()
                with f:
                    f.index()

                with f.build(copy_flow=True) as fl:
                    fl.search()

        """

        op_flow = copy.deepcopy(self) if copy_flow else self

        _pod_edges = set()

        if op_flow.args.inspect == FlowInspectType.COLLECT:
            op_flow.gather_inspect(copy_flow=False)

        if 'gateway' not in op_flow._pod_nodes:
            op_flow._add_gateway(needs={op_flow.last_pod})

        # construct a map with a key a start node and values an array of its end nodes
        _outgoing_map = defaultdict(list)

        # if set no_inspect then all inspect related nodes are removed
        if op_flow.args.inspect == FlowInspectType.REMOVE:
            op_flow._pod_nodes = {k: v for k, v in op_flow._pod_nodes.items() if not v.role.is_inspect}
            reverse_inspect_map = {v: k for k, v in op_flow._inspect_pods.items()}

        for end, pod in op_flow._pod_nodes.items():
            # if an endpoint is being inspected, then replace it with inspected Pod
            # but not those inspect related node
            if op_flow.args.inspect.is_keep:
                pod.needs = set(ep if pod.role.is_inspect else op_flow._inspect_pods.get(ep, ep) for ep in pod.needs)
            else:
                pod.needs = set(reverse_inspect_map.get(ep, ep) for ep in pod.needs)

            for start in pod.needs:
                if start not in op_flow._pod_nodes:
                    raise FlowMissingPodError(f'{start} is not in this flow, misspelled name?')
                _outgoing_map[start].append(end)
                _pod_edges.add((start, end))

        op_flow = _build_flow(op_flow, _outgoing_map)
        op_flow = _optimize_flow(op_flow, _outgoing_map, _pod_edges)
        hanging_pods = _hanging_pods(op_flow)
        if hanging_pods:
            self.logger.warning(f'{hanging_pods} are hanging in this flow with no pod receiving from them, '
                                f'you may want to double check if it is intentional or some mistake')
        op_flow._build_level = FlowBuildLevel.GRAPH
        return op_flow

    def __call__(self, *args, **kwargs):
        return self.build(*args, **kwargs)

    def __enter__(self):
        return self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        super().__exit__(exc_type, exc_val, exc_tb)
        if self.args.logserver:
            self._stop_log_server()
        self._build_level = FlowBuildLevel.EMPTY
        self.logger.success(
            f'flow is closed and all resources should be released already, current build level is {self._build_level}')
        self.logger.close()

    def _stop_log_server(self):
        import urllib.request
        try:
            # it may have been shutdown from the outside
            urllib.request.urlopen(JINA_GLOBAL.logserver.shutdown, timeout=5)
        except Exception as ex:
            self.logger.info(f'Failed to connect to shutdown log sse server: {repr(ex)}')

    def _start_log_server(self):
        try:
            import urllib.request
            import flask, flask_cors
            try:
                with open(self.args.logserver_config) as fp:
                    log_config = yaml.load(fp)
                self._sse_logger = threading.Thread(name='sentinel-sse-logger',
                                                    target=start_sse_logger, daemon=True,
                                                    args=(log_config,
                                                          self.args.log_id,
                                                          self.yaml_spec))
                self._sse_logger.start()
                time.sleep(1)
                response = urllib.request.urlopen(JINA_GLOBAL.logserver.ready, timeout=5)
                if response.status == 200:
                    self.logger.success(f'logserver is started and available at {JINA_GLOBAL.logserver.address}')
            except Exception as ex:
                self.logger.error(f'Could not start logserver because of {repr(ex)}')
        except ModuleNotFoundError:
            self.logger.error(
                f'sse logserver can not start because of "flask" and "flask_cors" are missing, '
                f'use pip install "jina[http]" (with double quotes) to install the dependencies')
        except Exception as ex:
            self.logger.error(f'logserver fails to start: {repr(ex)}')

    def start(self):
        """Start to run all Pods in this Flow.

        Remember to close the Flow with :meth:`close`.

        Note that this method has a timeout of ``timeout_ready`` set in CLI,
        which is inherited all the way from :class:`jina.peapods.peas.BasePea`
        """

        if self._build_level.value < FlowBuildLevel.GRAPH.value:
            self.build(copy_flow=False)

        if self.args.logserver:
            self.logger.info('starting logserver...')
            self._start_log_server()

        for v in self._pod_nodes.values():
            self.enter_context(v)

        self.logger.info(f'{self.num_pods} Pods (i.e. {self.num_peas} Peas) are running in this Flow')

        self._show_success_message()

        return self

    @property
    def num_pods(self) -> int:
        """Get the number of pods in this flow"""
        return len(self._pod_nodes)

    @property
    def num_peas(self) -> int:
        """Get the number of peas (parallel count) in this flow"""
        return sum(v.num_peas for v in self._pod_nodes.values())

    def __eq__(self, other: 'Flow'):
        """
        Comparing the topology of a flow with another flow.
        Identification is defined by whether two flows share the same set of edges.

        :param other: the second flow object
        """

        if self._build_level.value < FlowBuildLevel.GRAPH.value:
            a = self.build()
        else:
            a = self

        if other._build_level.value < FlowBuildLevel.GRAPH.value:
            b = other.build()
        else:
            b = other

        return a._pod_nodes == b._pod_nodes

    @build_required(FlowBuildLevel.GRAPH)
    def _get_client(self, **kwargs):
        kwargs.update(self._common_kwargs)
        from ..clients import py_client
        if 'port_expose' not in kwargs:
            kwargs['port_expose'] = self.port_expose
        if 'host' not in kwargs:
            kwargs['host'] = self.host
        return py_client(**kwargs)

    @deprecated_alias(buffer='input_fn', callback='output_fn')
    def train(self, input_fn: Union[Iterator['jina_pb2.DocumentProto'], Iterator[bytes], Callable] = None,
              output_fn: Callable[['jina_pb2.RequestProto'], None] = None,
              **kwargs):
        """Do training on the current flow

        It will start a :py:class:`CLIClient` and call :py:func:`train`.

        Example,

        .. highlight:: python
        .. code-block:: python

            with f:
                f.train(input_fn)
                ...


        This will call the pre-built reader to read files into an iterator of bytes and feed to the flow.

        One may also build a reader/generator on your own.

        Example,

        .. highlight:: python
        .. code-block:: python

            def my_reader():
                for _ in range(10):
                    yield b'abcdfeg'   # each yield generates a document for training

            with f.build(runtime='thread') as flow:
                flow.train(bytes_gen=my_reader())

        :param input_fn: An iterator of bytes. If not given, then you have to specify it in **kwargs**.
        :param output_fn: the callback function to invoke after training
        :param kwargs: accepts all keyword arguments of `jina client` CLI
        """
        self._get_client(**kwargs).train(input_fn, output_fn, **kwargs)

    def index_ndarray(self, array: 'np.ndarray', axis: int = 0, size: int = None, shuffle: bool = False,
                      output_fn: Callable[['jina_pb2.RequestProto'], None] = None,
                      **kwargs):
        """Using numpy ndarray as the index source for the current flow

        :param array: the numpy ndarray data source
        :param axis: iterate over that axis
        :param size: the maximum number of the sub arrays
        :param shuffle: shuffle the the numpy data source beforehand
        :param output_fn: the callback function to invoke after indexing
        :param kwargs: accepts all keyword arguments of `jina client` CLI
        """
        from ..clients.python.io import input_numpy
        self._get_client(**kwargs).index(input_numpy(array, axis, size, shuffle),
                                         output_fn, **kwargs)

    def search_ndarray(self, array: 'np.ndarray', axis: int = 0, size: int = None, shuffle: bool = False,
                       output_fn: Callable[['jina_pb2.RequestProto'], None] = None,
                       **kwargs):
        """Use a numpy ndarray as the query source for searching on the current flow

        :param array: the numpy ndarray data source
        :param axis: iterate over that axis
        :param size: the maximum number of the sub arrays
        :param shuffle: shuffle the the numpy data source beforehand
        :param output_fn: the callback function to invoke after indexing
        :param kwargs: accepts all keyword arguments of `jina client` CLI
        """
        from ..clients.python.io import input_numpy
        self._get_client(**kwargs).search(input_numpy(array, axis, size, shuffle),
                                          output_fn, **kwargs)

    def index_lines(self, lines: Iterator[str] = None, filepath: str = None, size: int = None,
                    sampling_rate: float = None, read_mode='r',
                    output_fn: Callable[['jina_pb2.RequestProto'], None] = None,
                    **kwargs):
        """ Use a list of lines as the index source for indexing on the current flow

        :param lines: a list of strings, each is considered as d document
        :param filepath: a text file that each line contains a document
        :param size: the maximum number of the documents
        :param sampling_rate: the sampling rate between [0, 1]
        :param read_mode: specifies the mode in which the file
                is opened. 'r' for reading in text mode, 'rb' for reading in binary
        :param output_fn: the callback function to invoke after indexing
        :param kwargs: accepts all keyword arguments of `jina client` CLI
        """
        from ..clients.python.io import input_lines
        self._get_client(**kwargs).index(input_lines(lines, filepath, size, sampling_rate, read_mode),
                                         output_fn,
                                         **kwargs)

    def index_files(self, patterns: Union[str, List[str]], recursive: bool = True,
                    size: int = None, sampling_rate: float = None, read_mode: str = None,
                    output_fn: Callable[['jina_pb2.RequestProto'], None] = None,
                    **kwargs):
        """ Use a set of files as the index source for indexing on the current flow

        :param patterns: The pattern may contain simple shell-style wildcards, e.g. '\*.py', '[\*.zip, \*.gz]'
        :param recursive: If recursive is true, the pattern '**' will match any files and
                    zero or more directories and subdirectories.
        :param size: the maximum number of the files
        :param sampling_rate: the sampling rate between [0, 1]
        :param read_mode: specifies the mode in which the file
                is opened. 'r' for reading in text mode, 'rb' for reading in binary mode
        :param output_fn: the callback function to invoke after indexing
        :param kwargs: accepts all keyword arguments of `jina client` CLI
        """
        from ..clients.python.io import input_files
        self._get_client(**kwargs).index(input_files(patterns, recursive, size, sampling_rate, read_mode),
                                         output_fn,
                                         **kwargs)

    def search_files(self, patterns: Union[str, List[str]], recursive: bool = True,
                     size: int = None, sampling_rate: float = None, read_mode: str = None,
                     output_fn: Callable[['jina_pb2.RequestProto'], None] = None,
                     **kwargs):
        """ Use a set of files as the query source for searching on the current flow

        :param patterns: The pattern may contain simple shell-style wildcards, e.g. '\*.py', '[\*.zip, \*.gz]'
        :param recursive: If recursive is true, the pattern '**' will match any files and
                    zero or more directories and subdirectories.
        :param size: the maximum number of the files
        :param sampling_rate: the sampling rate between [0, 1]
        :param read_mode: specifies the mode in which the file
                is opened. 'r' for reading in text mode, 'rb' for reading in
        :param output_fn: the callback function to invoke after indexing
        :param kwargs: accepts all keyword arguments of `jina client` CLI
        """
        from ..clients.python.io import input_files
        self._get_client(**kwargs).search(input_files(patterns, recursive, size, sampling_rate, read_mode),
                                          output_fn,
                                          **kwargs)

    def search_lines(self, filepath: str = None, lines: Iterator[str] = None, size: int = None,
                     sampling_rate: float = None, read_mode='r',
                     output_fn: Callable[['jina_pb2.RequestProto'], None] = None,
                     **kwargs):
        """ Use a list of files as the query source for searching on the current flow

        :param filepath: a text file that each line contains a document
        :param lines: a list of strings, each is considered as d document
        :param size: the maximum number of the documents
        :param sampling_rate: the sampling rate between [0, 1]
        :param read_mode: specifies the mode in which the file
                is opened. 'r' for reading in text mode, 'rb' for reading in binary
        :param output_fn: the callback function to invoke after indexing
        :param kwargs: accepts all keyword arguments of `jina client` CLI
        """
        from ..clients.python.io import input_lines
        self._get_client(**kwargs).search(input_lines(lines, filepath, size, sampling_rate, read_mode),
                                          output_fn,
                                          **kwargs)

    @deprecated_alias(buffer='input_fn', callback='output_fn')
    def index(self, input_fn: Union[Iterator[Union['jina_pb2.DocumentProto', bytes]], Callable] = None,
              output_fn: Callable[['jina_pb2.RequestProto'], None] = None,
              **kwargs):
        """Do indexing on the current flow

        Example,

        .. highlight:: python
        .. code-block:: python

            with f:
                f.index(input_fn)
                ...


        This will call the pre-built reader to read files into an iterator of bytes and feed to the flow.

        One may also build a reader/generator on your own.

        Example,

        .. highlight:: python
        .. code-block:: python

            def my_reader():
                for _ in range(10):
                    yield b'abcdfeg'  # each yield generates a document to index

            with f.build(runtime='thread') as flow:
                flow.index(bytes_gen=my_reader())

        It will start a :py:class:`CLIClient` and call :py:func:`index`.

        :param input_fn: An iterator of bytes. If not given, then you have to specify it in **kwargs**.
        :param output_fn: the callback function to invoke after indexing
        :param kwargs: accepts all keyword arguments of `jina client` CLI
        """
        self._get_client(**kwargs).index(input_fn, output_fn, **kwargs)

    @deprecated_alias(buffer='input_fn', callback='output_fn')
    def search(self, input_fn: Union[Iterator[Union['jina_pb2.DocumentProto', bytes]], Callable] = None,
               output_fn: Callable[['jina_pb2.RequestProto'], None] = None,
               **kwargs):
        """Do searching on the current flow

        It will start a :py:class:`CLIClient` and call :py:func:`search`.


        Example,

        .. highlight:: python
        .. code-block:: python

            with f:
                f.search(input_fn)
                ...


        This will call the pre-built reader to read files into an iterator of bytes and feed to the flow.

        One may also build a reader/generator on your own.

        Example,

        .. highlight:: python
        .. code-block:: python

            def my_reader():
                for _ in range(10):
                    yield b'abcdfeg'   # each yield generates a query for searching

            with f.build(runtime='thread') as flow:
                flow.search(bytes_gen=my_reader())

        :param input_fn: An iterator of bytes. If not given, then you have to specify it in **kwargs**.
        :param output_fn: the callback function to invoke after searching
        :param kwargs: accepts all keyword arguments of `jina client` CLI
        """
        self._get_client(**kwargs).search(input_fn, output_fn, **kwargs)

    def plot(self, output: str = None,
             vertical_layout: bool = False,
             inline_display: bool = True,
             build: bool = True,
             copy_flow: bool = True) -> 'Flow':
        """
        Visualize the flow up to the current point
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
        :param build: build the flow first before plotting, gateway connection can be better showed
        :param copy_flow: when set to true, then always copy the current flow and
                do the modification on top of it then return, otherwise, do in-line modification
        :return: the flow
        """

        op_flow = copy.deepcopy(self) if copy_flow else self
        if build:
            op_flow.build(False)
        mermaid_graph = ["%%{init: {'theme': 'base', "
                         "'themeVariables': { 'primaryColor': '#32C8CD', "
                         "'edgeLabelBackground':'#fff', 'clusterBkg': '#FFCC66'}}}%%"]
        mermaid_graph.append('graph TD' if vertical_layout else 'graph LR')

        start_repl = {}
        end_repl = {}
        for node, v in op_flow._pod_nodes.items():
            if not v.is_singleton and v.role != PodRoleType.GATEWAY:
                mermaid_graph.append(f'subgraph sub_{node} ["{node} ({v._args.parallel})"]')
                if v.is_head_router:
                    head_router = node + '_HEAD'
                    end_repl[node] = (head_router, '((fa:fa-random))')
                if v.is_tail_router:
                    tail_router = node + '_TAIL'
                    start_repl[node] = (tail_router, '((fa:fa-random))')

                p_r = '((%s))'
                p_e = '[[%s]]'
                for j in range(v._args.parallel):
                    r = node + (f'_{j}' if v._args.parallel > 1 else '')
                    if v.is_head_router:
                        mermaid_graph.append(f'\t{head_router}{p_r % "head"}:::pea-->{r}{p_e % r}:::pea')
                    if v.is_tail_router:
                        mermaid_graph.append(f'\t{r}{p_e % r}:::pea-->{tail_router}{p_r % "tail"}:::pea')
                mermaid_graph.append('end')

        for node, v in op_flow._pod_nodes.items():
            ed_str = str(v.head_args.socket_in).split('_')[0]
            for need in sorted(v.needs):
                edge_str = ''
                if need in op_flow._pod_nodes:
                    st_str = str(op_flow._pod_nodes[need].tail_args.socket_out).split('_')[0]
                    edge_str = f'|{st_str}-{ed_str}|'

                _s = start_repl.get(need, (need, f'({need})'))
                _e = end_repl.get(node, (node, f'({node})'))
                _s_role = op_flow._pod_nodes[need].role
                _e_role = op_flow._pod_nodes[node].role
                line_st = '-->'

                if _s_role in {PodRoleType.INSPECT, PodRoleType.JOIN_INSPECT}:
                    _s = start_repl.get(need, (need, f'{{{{{need}}}}}'))

                if _e_role == PodRoleType.GATEWAY:
                    _e = ('gateway_END', f'({node})')
                elif _e_role in {PodRoleType.INSPECT, PodRoleType.JOIN_INSPECT}:
                    _e = end_repl.get(node, (node, f'{{{{{node}}}}}'))

                if _s_role == PodRoleType.INSPECT or _e_role == PodRoleType.INSPECT:
                    line_st = '-.->'

                mermaid_graph.append(
                    f'{_s[0]}{_s[1]}:::{str(_s_role)} {line_st} {edge_str}{_e[0]}{_e[1]}:::{str(_e_role)}')
        mermaid_graph.append(f'classDef {str(PodRoleType.POD)} fill:#32C8CD,stroke:#009999')
        mermaid_graph.append(f'classDef {str(PodRoleType.INSPECT)} fill:#ff6666,color:#fff')
        mermaid_graph.append(f'classDef {str(PodRoleType.JOIN_INSPECT)} fill:#ff6666,color:#fff')
        mermaid_graph.append(f'classDef {str(PodRoleType.GATEWAY)} fill:#6E7278,color:#fff')
        mermaid_graph.append(f'classDef {str(PodRoleType.INSPECT_AUX_PASS)} fill:#fff,color:#000,stroke-dasharray: 5 5')
        mermaid_graph.append('classDef pea fill:#009999,stroke:#1E6E73')
        mermaid_str = '\n'.join(mermaid_graph)

        image_type = 'svg'
        if output and output.endswith('jpg'):
            image_type = 'jpg'

        url = op_flow._mermaid_to_url(mermaid_str, image_type)
        showed = False
        if inline_display:
            try:
                from IPython.display import display, Image
                from IPython.utils import io

                display(Image(url=url))
                showed = True
            except:
                # no need to panic users
                pass

        if output:
            op_flow._download_mermaid_url(url, output)
        elif not showed:
            op_flow.logger.info(f'flow visualization: {url}')

        return self

    def _mermaid_to_url(self, mermaid_str, img_type) -> str:
        """
        Rendering the current flow as a url points to a SVG, it needs internet connection
        :param kwargs: keyword arguments of :py:meth:`to_mermaid`
        :return: the url points to a SVG
        """
        if img_type == 'jpg':
            img_type = 'img'

        encoded_str = base64.b64encode(bytes(mermaid_str, 'utf-8')).decode('utf-8')

        return f'https://mermaid.ink/{img_type}/{encoded_str}'

    def _download_mermaid_url(self, mermaid_url, output) -> None:
        """
        Rendering the current flow as a jpg image, this will call :py:meth:`to_mermaid` and it needs internet connection
        :param path: the file path of the image
        :param kwargs: keyword arguments of :py:meth:`to_mermaid`
        :return:
        """
        try:
            req = Request(mermaid_url, headers={'User-Agent': 'Mozilla/5.0'})
            with open(output, 'wb') as fp:
                fp.write(urlopen(req).read())
        except:
            self.logger.error('can not download image, please check your graph and the network connections')

    def dry_run(self, **kwargs):
        """Send a DRYRUN request to this flow, passing through all pods in this flow,
        useful for testing connectivity and debugging"""
        self.logger.warning('calling dry_run() on a flow is depreciated, it will be removed in the future version. '
                            'calling index(), search(), train() will trigger a dry_run()')

    @build_required(FlowBuildLevel.GRAPH)
    def to_swarm_yaml(self, path: TextIO):
        """
        Generate the docker swarm YAML compose file

        :param path: the output yaml path
        """
        swarm_yml = {'version': '3.4',
                     'services': {}}

        for k, v in self._pod_nodes.items():
            swarm_yml['services'][k] = {
                'command': v.to_cli_command(),
                'deploy': {'parallel': 1}
            }

        yaml.dump(swarm_yml, path)

    @property
    @build_required(FlowBuildLevel.GRAPH)
    def port_expose(self):
        return self._pod_nodes['gateway'].port_expose

    @property
    @build_required(FlowBuildLevel.GRAPH)
    def host(self):
        return self._pod_nodes['gateway'].host

    def __iter__(self):
        return self._pod_nodes.values().__iter__()

    def _show_success_message(self):
        if self._pod_nodes['gateway']._args.rest_api:
            header = 'http://'
            protocol = 'REST'
        else:
            header = 'tcp://'
            protocol = 'gRPC'

        address_table = [f'\t🖥️ Local access:\t' + colored(f'{header}{self.host}:{self.port_expose}',
                                                           'cyan', attrs='underline'),
                         f'\t🔒 Private network:\t' + colored(f'{header}{get_internal_ip()}:{self.port_expose}',
                                                            'cyan', attrs='underline')]
        public_ip = get_public_ip()
        if public_ip:
            address_table.append(
                f'\t🌐 Public address:\t' + colored(f'{header}{public_ip}:{self.port_expose}',
                                                  'cyan', attrs='underline'))
        self.logger.success(f'🎉 Flow is ready to use, accepting {colored(protocol + " request", attrs="bold")}')
        self.logger.info('\n'+'\n'.join(address_table))

    def block(self):
        """Block the process until user hits KeyboardInterrupt """
        try:
            self._show_success_message()
            threading.Event().wait()
        except KeyboardInterrupt:
            pass

    def use_grpc_gateway(self):
        """Change to use gRPC gateway for IO """
        self._common_kwargs['rest_api'] = False

    def use_rest_gateway(self):
        """Change to use REST gateway for IO """
        self._common_kwargs['rest_api'] = True

    # for backward support
    join = needs
