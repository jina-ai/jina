import copy
import threading
from collections import OrderedDict
from contextlib import ExitStack
from functools import wraps
from typing import Union, Tuple, List, Set, Dict, Optional, Iterator, Callable, Type, TextIO

import ruamel.yaml
from pkg_resources import resource_stream

from .. import __default_host__
from ..enums import FlowBuildLevel
from ..excepts import FlowTopologyError, FlowMissingPodError, FlowBuildLevelError
from ..helper import yaml, expand_env_var
from ..logging import get_logger
from ..logging.sse import start_sse_logger
from ..main.parser import set_pod_parser, set_frontend_parser
from ..peapods.pod import Pod, SocketType, FrontendPod


def build_required(required_level: 'FlowBuildLevel'):
    """Annotate a function so that it requires certaidn build level to run.

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
    def __init__(self, driver_yaml_path: str = None, sse_logger: bool = False, runtime: str = 'process', *args,
                 **kwargs):
        """Initialize a flow object

        :param driver_yaml_path: the file path of the driver map
        :param sse_logger: to enable the server-side event logger or not
        :param runtime: the runtime that each pod in this flow runs on
        :param kwargs: other keyword arguments that will be shared by all pods in this flow
        """
        self.logger = get_logger(self.__class__.__name__)
        self.with_sse_logger = sse_logger
        self._common_kwargs = kwargs

        with resource_stream('jina', '/'.join(('resources', 'drivers-default.yml'))) as rs:
            self.support_drivers = yaml.load(rs)['drivers']

        if driver_yaml_path:
            # load additional drivers
            with open(driver_yaml_path) as rs:
                self.support_drivers.update(yaml.load(rs)['drivers'])
            self._common_kwargs['driver_yaml_path'] = driver_yaml_path

        self._pod_nodes = OrderedDict()  # type: Dict[str, 'Pod']
        self._build_level = FlowBuildLevel.EMPTY
        self.runtime = runtime
        self._pod_name_counter = {k: 0 for k in self.support_drivers.keys()}
        self._last_changed_pod = []
        self._add_frontend()

    @classmethod
    def to_yaml(cls, representer, data):
        """Required by :mod:`ruamel.yaml.constructor` """
        tmp = data._dump_instance_to_yaml(data)
        return representer.represent_mapping('!' + cls.__name__, tmp)

    @classmethod
    def from_yaml(cls, constructor, node, stop_on_import_error=False):
        """Required by :mod:`ruamel.yaml.constructor` """
        return cls._get_instance_from_yaml(constructor, node, stop_on_import_error)[0]

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
    def _get_instance_from_yaml(cls, constructor, node, stop_on_import_error=False):

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
            obj.add(name=pod_name, **pod_attr, copy_flow=False)

        obj.logger.critical('initialize %s from a yaml config' % cls.__name__)

        # if node.tag in {'!CompoundExecutor'}:
        #     os.environ['JINA_WARN_UNNAMED'] = 'YES'

        return obj, data

    @staticmethod
    def _parse_endpoints(op_flow, pod_name, endpoint, connect_to_last_pod=False) -> Set:
        # parsing recv_from
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

    @staticmethod
    def _get_parsed_args(op_flow, name, kwargs, parser=set_pod_parser):
        kwargs.update(op_flow._common_kwargs)
        args = []
        for k, v in kwargs.items():
            if isinstance(v, bool):
                if v:
                    if not k.startswith('no_') and not k.startswith('no-'):
                        args.append('--%s' % k)
                    else:
                        args.append('--%s' % k[3:])
                else:
                    if k.startswith('no_') or k.startswith('no-'):
                        args.append('--%s' % k)
                    else:
                        args.append('--no_%s' % k)
            elif isinstance(v, list):  # for nargs
                args.extend(['--%s' % k, *(str(vv) for vv in v)])
            else:
                args.extend(['--%s' % k, str(v)])
        try:
            p_args, unknown_args = parser().parse_known_args(args)
            if unknown_args:
                op_flow.logger.warning('not sure what these arguments are: %s' % unknown_args)
        except SystemExit:
            raise ValueError('bad arguments for pod "%s", '
                             'you may want to double check your args "%s"' % (name, args))
        return args, p_args, unknown_args

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

    def _add_frontend(self, **kwargs):
        pod_name = 'frontend'

        kwargs.update(self._common_kwargs)
        kwargs['name'] = 'frontend'
        self._pod_nodes[pod_name] = FrontendPod(kwargs=kwargs, parser=set_frontend_parser)

        self.set_last_pod(pod_name, False)

    def join(self, recv_from: Union[Tuple[str], List[str]], *args, **kwargs) -> 'Flow':
        """
        Add a blocker to the flow, wait until all peas defined in `recv_from` completed.

        :param recv_from: list of service names to wait
        :return: the modified flow
        """
        if len(recv_from) <= 1:
            raise FlowTopologyError('no need to wait for a single service, need len(recv_from) > 1')
        return self.add(name='joiner', driver='merge', num_part=len(recv_from), recv_from=recv_from, *args, **kwargs)

    def add(self,
            recv_from: Union[str, Tuple[str], List[str]] = None,
            send_to: Union[str, Tuple[str], List[str]] = None,
            copy_flow: bool = True,
            **kwargs) -> 'Flow':
        """
        Add a pod to the current flow object and return the new modified flow object.
        The attribute of the pod can be later changed with :py:meth:`set` or deleted with :py:meth:`remove`

        Note there are shortcut versions of this method.
        Recommend to use :py:meth:`add_encoder`, :py:meth:`add_preprocessor`,
        :py:meth:`add_router`, :py:meth:`add_indexer` whenever possible.

        :param recv_from: the name of the pod(s) that this pod receives data from.
                           One can also use 'pod.Frontend' to indicate the connection with the frontend.
        :param send_to:  the name of the pod(s) that this pod sends data to.
                           One can also use 'pod.Frontend' to indicate the connection wisth the frontend.
        :param copy_flow: when set to true, then always copy the current flow and do the modification on top of it then return, otherwise, do in-line modification
        :param kwargs: other keyword-value arguments that the pod CLI supports
        :return: a (new) flow object with modification
        """

        op_flow = copy.deepcopy(self) if copy_flow else self

        driver_type = kwargs.get('driver', None)
        pod_name = kwargs.get('name', None)

        if driver_type and driver_type not in op_flow.support_drivers:
            raise ValueError(
                'pod: %s is not supported, should be one of %s' % (driver_type, op_flow.support_drivers.keys()))

        if pod_name in op_flow._pod_nodes:
            raise FlowTopologyError('name: %s is used in this Flow already!' % pod_name)

        if not pod_name:
            pod_name = '%s%d' % (driver_type if driver_type else 'default', op_flow._pod_name_counter[driver_type])
            op_flow._pod_name_counter[driver_type] += 1

        if not pod_name.isidentifier():
            # hyphen - can not be used in the name
            raise ValueError('name: %s is invalid, please follow the python variable name conventions' % pod_name)

        recv_from = op_flow._parse_endpoints(op_flow, pod_name, recv_from, connect_to_last_pod=True)
        send_to = op_flow._parse_endpoints(op_flow, pod_name, send_to, connect_to_last_pod=False)

        kwargs.update(op_flow._common_kwargs)
        kwargs['name'] = pod_name
        op_flow._pod_nodes[pod_name] = Pod(kwargs=kwargs, send_to=send_to, recv_from=recv_from)

        op_flow.set_last_pod(pod_name, False)

        return op_flow

    def _build_graph(self, copy_flow: bool) -> 'Flow':
        op_flow = copy.deepcopy(self) if copy_flow else self

        _pod_edges = set()

        if not op_flow._last_changed_pod or not op_flow._pod_nodes:
            raise FlowTopologyError('flow is empty?')

        # close the loop
        op_flow._pod_nodes['frontend'].recv_from = {op_flow._last_changed_pod[-1]}

        # direct all income peas' output to the current service
        for k, p in op_flow._pod_nodes.items():
            for s in p.recv_from:
                if s not in op_flow._pod_nodes:
                    raise FlowMissingPodError('%s is not in this flow, misspelled name?' % s)
                op_flow._pod_nodes[s].send_to.add(k)
                _pod_edges.add('%s-%s' % (s, k))
            for s in p.send_to:
                if s not in op_flow._pod_nodes:
                    raise FlowMissingPodError('%s is not in this flow, misspelled name?' % s)
                op_flow._pod_nodes[s].recv_from.add(k)
                _pod_edges.add('%s-%s' % (k, s))

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
                s_pod.tail_args.socket_out = SocketType.PUB_BIND
                s_pod.tail_args.host_out = __default_host__
                e_pod.head_args.socket_in = SocketType.SUB_CONNECT
                e_pod.head_args.host_in = s_name
                e_pod.head_args.port_in = s_pod.tail_args.port_out
            elif len(edges_with_same_end) > 1 and len(edges_with_same_start) == 1:
                Pod.connect(s_pod, e_pod, bind_on_first=False)
            elif len(edges_with_same_start) == 1 and len(edges_with_same_end) == 1:
                # in this case, either side can be BIND
                # we prefer frontend to be always BIND
                # check if either node is frontend
                if s_name == 'frontend':
                    if e_pod.is_head_router:
                        # connect frontend directly to peas
                        e_pod.connect_to_last(s_pod)
                    else:
                        Pod.connect(s_pod, e_pod, bind_on_first=True)
                elif e_name == 'frontend':
                    if s_pod.is_tail_router and s_pod.tail_args.num_part == 1:
                        # connect frontend directly to peas only if this is unblock router
                        # as frontend can not block & reduce message
                        s_pod.connect_to_next(e_pod)
                    else:
                        Pod.connect(s_pod, e_pod, bind_on_first=False)
                else:
                    e_pod.head_args.socket_in = s_pod.tail_args.socket_out.paired
                    if e_pod.is_head_router and not s_pod.is_tail_router:
                        e_pod.connect_to_last(s_pod)
                    elif s_pod.is_tail_router and s_pod.tail_args.num_part == 1:
                        s_pod.connect_to_next(e_pod)
                    else:
                        Pod.connect(s_pod, e_pod, bind_on_first=False)
            else:
                raise FlowTopologyError('found %d edges start with %s and %d edges end with %s, '
                                        'this type of topology is ambiguous and should not exist, '
                                        'i can not determine the socket type' % (
                                            len(edges_with_same_start), s_name, len(edges_with_same_end), e_name))

        op_flow._build_level = FlowBuildLevel.GRAPH
        return op_flow

    def build(self, runtime: Optional[str] = 'process', copy_flow: bool = False, *args, **kwargs) -> 'Flow':
        """
        Build the current flow and make it ready to use

        :param runtime: supported 'thread', 'process', 'swarm', 'k8s', 'shell', if None then only build graph only
        :param copy_flow: return the copy of the current flow
        :return: the current flow (by default)
        """

        op_flow = self._build_graph(copy_flow)
        runtime = runtime or op_flow.runtime

        if not runtime:
            op_flow.logger.error('no specified runtime, build_level stays at %s, '
                                 'and you can not run this flow.' % op_flow._build_level)
        elif runtime in {'thread', 'process'}:
            for p in op_flow._pod_nodes.values():
                p.set_parallel_runtime(runtime)
            op_flow._build_level = FlowBuildLevel.RUNTIME
        else:
            raise NotImplementedError('runtime=%s is not supported yet' % runtime)

        return op_flow

    def __call__(self, *args, **kwargs):
        return self.build(*args, **kwargs)

    def __enter__(self):
        if self._build_level.value < FlowBuildLevel.RUNTIME.value:
            self.logger.warning(
                'current build_level=%s, lower than required. '
                'build the flow now via build() with default parameters' % self._build_level)
            self.build()

        if self.with_sse_logger:
            sse_logger = threading.Thread(name='sse-logger', target=start_sse_logger)
            sse_logger.setDaemon(True)
            sse_logger.start()

        self._pod_stack = ExitStack()
        for v in self._pod_nodes.values():
            self._pod_stack.enter_context(v)

        self.logger.info('%d Pods (i.e. %d Peas) are running in this Flow' % (
            len(self._pod_nodes),
            sum(v.num_peas for v in self._pod_nodes.values())))

        self.logger.critical('flow is now ready for use, current build_level is %s' % self._build_level)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        """Close the flow and release all resources associated to it. """
        if hasattr(self, '_pod_stack'):
            self._pod_stack.close()
        self._build_level = FlowBuildLevel.EMPTY
        self.logger.critical(
            'flow is closed and all resources should be released already, current build level is %s' % self._build_level)

    def __eq__(self, other: 'Flow'):
        """
        Comparing the topology of a flow with another flow.
        Identification is defined by whether two flows share the same set of edges.

        :param other: the second flow object
        """

        if self._build_level.value < FlowBuildLevel.GRAPH.value:
            a = self.build(runtime=None, copy_flow=True)
        else:
            a = self

        if other._build_level.value < FlowBuildLevel.GRAPH.value:
            b = other.build(runtime=None, copy_flow=True)
        else:
            b = other

        return a._pod_edges == b._pod_edges

    @build_required(FlowBuildLevel.RUNTIME)
    def _get_client(self, bytes_gen: Iterator[bytes] = None, **kwargs):
        from ..main.parser import set_client_cli_parser
        from ..clients.python import PyClient

        _, p_args, _ = self._get_parsed_args(self, PyClient.__name__, kwargs, parser=set_client_cli_parser)
        p_args.grpc_port = self._pod_nodes['frontend'].grpc_port
        p_args.grpc_host = self._pod_nodes['frontend'].grpc_host
        c = PyClient(p_args, delay=True)
        if bytes_gen:
            c.raw_bytes = bytes_gen
        return c

    def train(self, raw_bytes: Iterator[bytes] = None, callback: Callable[['jina_pb2.Message'], None] = None,
              **kwargs):
        """Do training on the current flow

        It will start a :py:class:`CLIClient` and call :py:func:`train`.

        Example,

        .. highlight:: python
        .. code-block:: python

            with f.build(runtime='thread') as flow:
                flow.train(txt_file='aa.txt')
                flow.train(image_zip_file='aa.zip', batch_size=64)
                flow.train(video_zip_file='aa.zip')
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

        :param raw_bytes: An iterator of bytes. If not given, then you have to specify it in `kwargs`.
        :param callback: the callback function to invoke after training
        :param kwargs: accepts all keyword arguments of `jina client` CLI
        """
        self._get_client(raw_bytes, mode='train', **kwargs).start(callback)

    def index(self, raw_bytes: Iterator[bytes] = None, callback: Callable[['jina_pb2.Message'], None] = None,
              **kwargs):
        """Do indexing on the current flow

        Example,

        .. highlight:: python
        .. code-block:: python

            with f.build(runtime='thread') as flow:
                flow.index(txt_file='aa.txt')
                flow.index(image_zip_file='aa.zip', batch_size=64)
                flow.index(video_zip_file='aa.zip')
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

        :param raw_bytes: An iterator of bytes. If not given, then you have to specify it in `kwargs`.
        :param callback: the callback function to invoke after indexing
        :param kwargs: accepts all keyword arguments of `jina client` CLI
        """
        self._get_client(raw_bytes, mode='index', **kwargs).start(callback)

    def search(self, raw_bytes: Iterator[bytes] = None, callback: Callable[['jina_pb2.Message'], None] = None,
               **kwargs):
        """Do indexing on the current flow

        It will start a :py:class:`CLIClient` and call :py:func:`search`.


        Example,

        .. highlight:: python
        .. code-block:: python

            with f.build(runtime='thread') as flow:
                flow.search(txt_file='aa.txt')
                flow.search(image_zip_file='aa.zip', batch_size=64)
                flow.search(video_zip_file='aa.zip')
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

        :param raw_bytes: An iterator of bytes. If not given, then you have to specify it in `kwargs`.
        :param callback: the callback function to invoke after searching
        :param kwargs: accepts all keyword arguments of `jina client` CLI
        """
        self._get_client(raw_bytes, mode='search', **kwargs).start(callback)
