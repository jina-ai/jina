__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import copy
import os
import tempfile
import threading
import time
from collections import OrderedDict
from contextlib import ExitStack
from functools import wraps
from typing import Union, Tuple, List, Set, Dict, Iterator, Callable, Type, TextIO, Any

import ruamel.yaml
from ruamel.yaml import StringIO

from .. import JINA_GLOBAL
from ..enums import FlowBuildLevel, FlowOptimizeLevel
from ..excepts import FlowTopologyError, FlowMissingPodError, FlowBuildLevelError, FlowConnectivityError
from ..helper import yaml, expand_env_var, get_non_defaults_args, deprecated_alias
from ..logging import get_logger
from ..logging.sse import start_sse_logger
from ..peapods.pod import SocketType, FlowPod, GatewayFlowPod

if False:
    from ..proto import jina_pb2
    import argparse
    import numpy as np


def build_required(required_level: 'FlowBuildLevel'):
    """Annotate a function so that it requires certain build level to run.

    :param required_level: required build level to run this function.

    Example:

    .. highlight:: python
    .. code-block:: python

        @build_required(FlowBuildLevel.RUNTIME)
        def foo():
            print(1)

    """

    def __build_level(func):
        @wraps(func)
        def arg_wrapper(self, *args, **kwargs):
            if hasattr(self, '_build_level'):
                if self._build_level.value >= required_level.value:
                    return func(self, *args, **kwargs)
                else:
                    raise FlowBuildLevelError(
                        'build_level check failed for %r, required level: %s, actual level: %s' % (
                            func, required_level, self._build_level))
            else:
                raise AttributeError('%r has no attribute "_build_level"' % self)

        return arg_wrapper

    return __build_level


class Flow:
    def __init__(self, args: 'argparse.Namespace' = None, **kwargs):
        """Initialize a flow object

        :param kwargs: other keyword arguments that will be shared by all pods in this flow


        More explain on ``optimize_level``:

        As an example, the following flow will generate 6 Peas,

        .. highlight:: python
        .. code-block:: python

            f = Flow(optimize_level=FlowOptimizeLevel.NONE).add(yaml_path='forward', replicas=3)

        The optimized version, i.e. :code:`Flow(optimize_level=FlowOptimizeLevel.FULL)`
        will generate 4 Peas, but it will force the :class:`GatewayPea` to take BIND role,
        as the head and tail routers are removed.
        
        """
        self.logger = get_logger(self.__class__.__name__)
        self._pod_nodes = OrderedDict()  # type: Dict[str, 'FlowPod']
        self._build_level = FlowBuildLevel.EMPTY
        self._pod_name_counter = 0
        self._last_changed_pod = ['gateway']  #: default first pod is gateway, will add when build()

        self._update_args(args, **kwargs)

    def _update_args(self, args, **kwargs):
        from ..main.parser import set_flow_parser
        _flow_parser = set_flow_parser()
        if args is None:
            from ..helper import get_parsed_args
            _, args, _ = get_parsed_args(kwargs, _flow_parser, 'Flow')

        self.args = args
        if kwargs and self.args.logserver and 'log_sse' not in kwargs:
            kwargs['log_sse'] = True
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
        # yaml.sort_base_mapping_type_on_output = False
        # yaml.representer.add_representer(OrderedDict, yaml.Representer.represent_dict)

        with open(f, 'w', encoding='utf8') as fp:
            yaml.dump(self, fp)
        self.logger.info(f'{self}\'s yaml config is save to %s' % f)
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
                endpoint = [op_flow._last_changed_pod[-1]]
            else:
                endpoint = []

        if isinstance(endpoint, list) or isinstance(endpoint, tuple):
            for idx, s in enumerate(endpoint):
                if s == pod_name:
                    raise FlowTopologyError('the income/output of a pod can not be itself')
        else:
            raise ValueError('endpoint=%s is not parsable' % endpoint)
        return set(endpoint)

    def set_last_pod(self, name: str, copy_flow: bool = True) -> 'Flow':
        """
        Set a pod as the last pod in the flow, useful when modifying the flow.

        :param name: the name of the existing pod
        :param copy_flow: when set to true, then always copy the current flow and do the modification on top of it then return, otherwise, do in-line modification
        :return: a (new) flow object with modification
        """
        op_flow = copy.deepcopy(self) if copy_flow else self

        if name not in op_flow._pod_nodes:
            raise FlowMissingPodError('%s can not be found in this Flow' % name)

        if op_flow._last_changed_pod and name == op_flow._last_changed_pod[-1]:
            pass
        else:
            op_flow._last_changed_pod.append(name)

        # graph is now changed so we need to
        # reset the build level to the lowest
        op_flow._build_level = FlowBuildLevel.EMPTY

        return op_flow

    def _add_gateway(self, needs, **kwargs):
        pod_name = 'gateway'

        kwargs.update(self._common_kwargs)
        kwargs['name'] = 'gateway'
        self._pod_nodes[pod_name] = GatewayFlowPod(kwargs, needs)

        # self.set_last_pod(pod_name, False)

    def join(self, needs: Union[Tuple[str], List[str]], *args, **kwargs) -> 'Flow':
        """
        Add a blocker to the flow, wait until all peas defined in **needs** completed.

        :param needs: list of service names to wait
        :return: the modified flow
        """
        if len(needs) <= 1:
            raise FlowTopologyError('no need to wait for a single service, need len(needs) > 1')
        return self.add(name='joiner', yaml_path='_merge', needs=needs, *args, **kwargs)

    def add(self,
            needs: Union[str, Tuple[str], List[str]] = None,
            copy_flow: bool = True,
            **kwargs) -> 'Flow':
        """
        Add a pod to the current flow object and return the new modified flow object.
        The attribute of the pod can be later changed with :py:meth:`set` or deleted with :py:meth:`remove`

        Note there are shortcut versions of this method.
        Recommend to use :py:meth:`add_encoder`, :py:meth:`add_preprocessor`,
        :py:meth:`add_router`, :py:meth:`add_indexer` whenever possible.

        :param needs: the name of the pod(s) that this pod receives data from.
                           One can also use 'pod.Gateway' to indicate the connection with the gateway.
        :param copy_flow: when set to true, then always copy the current flow and do the modification on top of it then return, otherwise, do in-line modification
        :param kwargs: other keyword-value arguments that the pod CLI supports
        :return: a (new) flow object with modification
        """

        op_flow = copy.deepcopy(self) if copy_flow else self

        pod_name = kwargs.get('name', None)

        if pod_name in op_flow._pod_nodes:
            raise FlowTopologyError('name: %s is used in this Flow already!' % pod_name)

        if not pod_name:
            pod_name = '%s%d' % ('pod', op_flow._pod_name_counter)
            op_flow._pod_name_counter += 1

        if not pod_name.isidentifier():
            # hyphen - can not be used in the name
            raise ValueError('name: %s is invalid, please follow the python variable name conventions' % pod_name)

        needs = op_flow._parse_endpoints(op_flow, pod_name, needs, connect_to_last_pod=True)

        kwargs.update(op_flow._common_kwargs)
        kwargs['name'] = pod_name
        op_flow._pod_nodes[pod_name] = FlowPod(kwargs=kwargs, needs=needs)

        op_flow.set_last_pod(pod_name, False)

        return op_flow

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

        if 'gateway' not in op_flow._pod_nodes:
            op_flow._add_gateway(needs={op_flow._last_changed_pod[-1]})

        # direct all income peas' output to the current service
        for k, p in op_flow._pod_nodes.items():
            for s in p.needs:
                if s not in op_flow._pod_nodes:
                    raise FlowMissingPodError('%s is not in this flow, misspelled name?' % s)
                _pod_edges.add('%s-%s' % (s, k))

        for k in _pod_edges:
            s_name, e_name = k.split('-')
            edges_with_same_start = [ed for ed in _pod_edges if ed.startswith(s_name)]
            edges_with_same_end = [ed for ed in _pod_edges if ed.endswith(e_name)]

            s_pod = op_flow._pod_nodes[s_name]
            e_pod = op_flow._pod_nodes[e_name]

            # Rule
            # if a node has multiple income/outgoing peas,
            # then its socket_in/out must be PULL_BIND or PUB_BIND
            # otherwise it should be different than its income
            # i.e. income=BIND => this=CONNECT, income=CONNECT => this = BIND
            #
            # when a socket is BIND, then host must NOT be set, aka default host 0.0.0.0
            # host_in and host_out is only set when corresponding socket is CONNECT

            if len(edges_with_same_start) > 1 and len(edges_with_same_end) == 1:
                FlowPod.connect(s_pod, e_pod, first_socket_type=SocketType.PUB_BIND)
            elif len(edges_with_same_start) == 1 and len(edges_with_same_end) > 1:
                FlowPod.connect(s_pod, e_pod, first_socket_type=SocketType.PUSH_CONNECT)
            elif len(edges_with_same_start) == 1 and len(edges_with_same_end) == 1:
                # in this case, either side can be BIND
                # we prefer gateway to be always CONNECT so that multiple clients can connect to it
                # check if either node is gateway
                # this is the only place where gateway appears
                if s_name == 'gateway':
                    if self.args.optimize_level > FlowOptimizeLevel.IGNORE_GATEWAY and e_pod.is_head_router:
                        # connect gateway directly to peas
                        e_pod.connect_to_tail_of(s_pod)
                    else:
                        FlowPod.connect(s_pod, e_pod, first_socket_type=SocketType.PUSH_CONNECT)
                elif e_name == 'gateway':
                    if self.args.optimize_level > FlowOptimizeLevel.IGNORE_GATEWAY and s_pod.is_tail_router and s_pod.tail_args.num_part <= 1:
                        # connect gateway directly to peas only if this is unblock router
                        # as gateway can not block & reduce message
                        s_pod.connect_to_head_of(e_pod)
                    else:
                        FlowPod.connect(s_pod, e_pod, first_socket_type=SocketType.PUSH_BIND)
                else:
                    e_pod.head_args.socket_in = s_pod.tail_args.socket_out.paired
                    if self.args.optimize_level > FlowOptimizeLevel.NONE and e_pod.is_head_router and not s_pod.is_tail_router:
                        e_pod.connect_to_tail_of(s_pod)
                    elif self.args.optimize_level > FlowOptimizeLevel.NONE and s_pod.is_tail_router and s_pod.tail_args.num_part <= 1:
                        s_pod.connect_to_head_of(e_pod)
                    else:
                        FlowPod.connect(s_pod, e_pod, first_socket_type=SocketType.PUSH_CONNECT)
            else:
                raise FlowTopologyError('found %d edges start with %s and %d edges end with %s, '
                                        'this type of topology is ambiguous and should not exist, '
                                        'i can not determine the socket type' % (
                                            len(edges_with_same_start), s_name, len(edges_with_same_end), e_name))

        op_flow._build_level = FlowBuildLevel.GRAPH
        return op_flow

    def __call__(self, *args, **kwargs):
        return self.build(*args, **kwargs)

    def __enter__(self):
        return self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _start_log_server(self):
        try:
            import urllib.request
            import flask, flask_cors
            self._sse_logger = threading.Thread(name='sentinel-sse-logger',
                                                target=start_sse_logger, daemon=True,
                                                args=(self.args.logserver_config,
                                                      self.yaml_spec))
            self._sse_logger.start()
            time.sleep(1)
            urllib.request.urlopen(JINA_GLOBAL.logserver.ready, timeout=5)
            self.logger.success(f'logserver is started and available at {JINA_GLOBAL.logserver.address}')
        except ModuleNotFoundError:
            self.logger.error(
                f'sse logserver can not start because of "flask" and "flask_cors" are missing, '
                f'use pip install "jina[http]" (with double quotes) to install the dependencies')
        except:
            self.logger.error('logserver fails to start')

    def start(self):
        """Start to run all Pods in this Flow.

        Remember to close the Flow with :meth:`close`.

        Note that this method has a timeout of ``timeout_ready`` set in CLI,
        which is inherited all the way from :class:`jina.peapods.peas.BasePea`
        """

        if self._build_level.value < FlowBuildLevel.GRAPH.value:
            self.build(copy_flow=False)

        if self.args.logserver:
            self.logger.info('start logserver...')
            self._start_log_server()

        self._pod_stack = ExitStack()
        for v in self._pod_nodes.values():
            self._pod_stack.enter_context(v)

        self.logger.info('%d Pods (i.e. %d Peas) are running in this Flow' % (
            self.num_pods,
            self.num_peas))

        self.logger.success('flow is now ready for use, current build_level is %s' % self._build_level)

        return self

    @property
    def num_pods(self) -> int:
        """Get the number of pods in this flow"""
        return len(self._pod_nodes)

    @property
    def num_peas(self) -> int:
        """Get the number of peas (replicas count) in this flow"""
        return sum(v.num_peas for v in self._pod_nodes.values())

    def close(self):
        """Close the flow and release all resources associated to it. """
        if hasattr(self, '_pod_stack'):
            self._pod_stack.close()
        # if hasattr(self, 'sse_logger') and self.sse_logger.is_alive():
        #     self.sse_logger.stop()
        self._build_level = FlowBuildLevel.EMPTY
        # time.sleep(1)  # sleep for a while until all resources are safely closed
        self.logger.success(
            'flow is closed and all resources should be released already, current build level is %s' % self._build_level)

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
        if 'port_grpc' not in kwargs:
            kwargs['port_grpc'] = self.port_grpc
        if 'host' not in kwargs:
            kwargs['host'] = self.host
        return py_client(**kwargs)

    @deprecated_alias(buffer='input_fn', callback='output_fn')
    def train(self, input_fn: Union[Iterator['jina_pb2.Document'], Iterator[bytes], Callable] = None,
              output_fn: Callable[['jina_pb2.Message'], None] = None,
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
        self._get_client(**kwargs).train(input_fn, output_fn)

    def index_numpy(self, array: 'np.ndarray', axis: int = 0, size: int = None, shuffle: bool = False,
                    output_fn: Callable[['jina_pb2.Message'], None] = None,
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
        self._get_client(**kwargs).index(input_numpy(array, axis, size, shuffle), output_fn)

    def search_numpy(self, array: 'np.ndarray', axis: int = 0, size: int = None, shuffle: bool = False,
                     output_fn: Callable[['jina_pb2.Message'], None] = None,
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
        self._get_client(**kwargs).search(input_numpy(array, axis, size, shuffle), output_fn)

    def index_lines(self, lines: Iterator[str] = None, filepath: str = None, size: int = None,
                    sampling_rate: float = None, read_mode='r',
                    output_fn: Callable[['jina_pb2.Message'], None] = None,
                    **kwargs):
        """ Use a list of files as the query source for indexing on the current flow

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
        self._get_client(**kwargs).index(input_lines(lines, filepath,  size, sampling_rate, read_mode), output_fn)

    def index_files(self, patterns: Union[str, List[str]], recursive: bool = True,
                    size: int = None, sampling_rate: float = None, read_mode: str = None,
                    output_fn: Callable[['jina_pb2.Message'], None] = None,
                    **kwargs):
        """ Use a set of files as the index source for indexing on the current flow

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
        self._get_client(**kwargs).index(input_files(patterns, recursive, size, sampling_rate, read_mode), output_fn)

    def search_files(self, patterns: Union[str, List[str]], recursive: bool = True,
                     size: int = None, sampling_rate: float = None, read_mode: str = None,
                     output_fn: Callable[['jina_pb2.Message'], None] = None,
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
        self._get_client(**kwargs).search(input_files(patterns, recursive, size, sampling_rate, read_mode), output_fn)

    def search_lines(self, filepath: str = None, lines: Iterator[str] = None, size: int = None,
                     sampling_rate: float = None, read_mode='r',
                     output_fn: Callable[['jina_pb2.Message'], None] = None,
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
        self._get_client(**kwargs).search(input_lines(filepath, lines, size, sampling_rate, read_mode), output_fn)

    @deprecated_alias(buffer='input_fn', callback='output_fn')
    def index(self, input_fn: Union[Iterator['jina_pb2.Document'], Iterator[bytes], Callable] = None,
              output_fn: Callable[['jina_pb2.Message'], None] = None,
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
        self._get_client(**kwargs).index(input_fn, output_fn)

    @deprecated_alias(buffer='input_fn', callback='output_fn')
    def search(self, input_fn: Union[Iterator['jina_pb2.Document'], Iterator[bytes], Callable] = None,
               output_fn: Callable[['jina_pb2.Message'], None] = None,
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
        self._get_client(**kwargs).search(input_fn, output_fn)

    def dry_run(self, **kwargs):
        """Send a DRYRUN request to this flow, passing through all pods in this flow,
        useful for testing connectivity and debugging"""
        if not self._get_client(**kwargs).dry_run():
            raise FlowConnectivityError('a dry run shows this flow is badly connected due to the network settings')

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
                'deploy': {'replicas': 1}
            }

        yaml.dump(swarm_yml, path)

    @property
    @build_required(FlowBuildLevel.GRAPH)
    def port_grpc(self):
        return self._pod_nodes['gateway'].port_grpc

    @property
    @build_required(FlowBuildLevel.GRAPH)
    def host(self):
        return self._pod_nodes['gateway'].host

    def __iter__(self):
        return self._pod_nodes.values().__iter__()

    def block(self):
        """Block the process until user hits KeyboardInterrupt """
        try:
            self.logger.success(f'flow is started at {self.host}:{self.port_grpc}, '
                                f'you can now use client to send request!')
            threading.Event().wait()
        except KeyboardInterrupt:
            pass

    def use_grpc_gateway(self):
        """Change to use gRPC gateway for IO """
        self._common_kwargs['rest_api'] = False

    def use_rest_gateway(self):
        """Change to use REST gateway for IO """
        self._common_kwargs['rest_api'] = True
