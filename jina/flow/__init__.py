import copy
import threading
import time
from collections import OrderedDict
from contextlib import ExitStack
from functools import wraps
from typing import Union, Tuple, List, Set, Dict, Iterator, Callable, Type, TextIO, Any

import ruamel.yaml

from ..enums import FlowBuildLevel
from ..excepts import FlowTopologyError, FlowMissingPodError, FlowBuildLevelError, FlowConnectivityError
from ..helper import yaml, expand_env_var, kwargs2list
from ..logging import get_logger
from ..logging.sse import start_sse_logger
from ..main.parser import set_pod_parser
from ..peapods.pod import SocketType, FlowPod, FrontendFlowPod

if False:
    from ..proto import jina_pb2


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
    def __init__(self, sse_logger: bool = False,
                 image_name: str = 'jina:master-debian',
                 repository: str = 'docker.pkg.github.com/jina-ai/jina',
                 optimized: bool = True,
                 *args,
                 **kwargs):
        """Initialize a flow object

        :param driver_yaml_path: the file path of the driver map
        :param sse_logger: to enable the server-side event logger or not
        :param optimized: trailing away redundant routers. however, this may change the frontend zmq socket to BIND
                            and hence not allow multiple clients connected to the frontend at the same time.
        :param kwargs: other keyword arguments that will be shared by all pods in this flow


        More explain on ``optimized``:

        As an example, the following flow will generates a 6 Peas,

        .. highlight:: python
        .. code-block:: python

            f = Flow(optimized=False).add(yaml_path='route', replicas=3)

        The optimized version will generate 4 Peas, but it will force the :class:`FrontendPea` to take BIND role,
        as the head and tail routers are removed.
        """
        self.logger = get_logger(self.__class__.__name__)
        self.with_sse_logger = sse_logger
        self.image_name = image_name
        self.repository = repository
        self.optimized = optimized
        self._common_kwargs = kwargs

        self._pod_nodes = OrderedDict()  # type: Dict[str, 'FlowPod']
        self._build_level = FlowBuildLevel.EMPTY
        self._pod_name_counter = 0
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
            p_pod_attr = {kk: expand_env_var(vv) for kk, vv in pod_attr.items()}
            obj.add(name=pod_name, **p_pod_attr, copy_flow=False)

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
        args = kwargs2list(kwargs)
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
        self._pod_nodes[pod_name] = FrontendFlowPod(kwargs)

        self.set_last_pod(pod_name, False)

    def join(self, recv_from: Union[Tuple[str], List[str]], *args, **kwargs) -> 'Flow':
        """
        Add a blocker to the flow, wait until all peas defined in `recv_from` completed.

        :param recv_from: list of service names to wait
        :return: the modified flow
        """
        if len(recv_from) <= 1:
            raise FlowTopologyError('no need to wait for a single service, need len(recv_from) > 1')
        return self.add(name='joiner', yaml_path='merge', recv_from=recv_from, *args, **kwargs)

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

        pod_name = kwargs.get('name', None)

        if pod_name in op_flow._pod_nodes:
            raise FlowTopologyError('name: %s is used in this Flow already!' % pod_name)

        if not pod_name:
            pod_name = '%s%d' % ('pod', op_flow._pod_name_counter)
            op_flow._pod_name_counter += 1

        if not pod_name.isidentifier():
            # hyphen - can not be used in the name
            raise ValueError('name: %s is invalid, please follow the python variable name conventions' % pod_name)

        recv_from = op_flow._parse_endpoints(op_flow, pod_name, recv_from, connect_to_last_pod=True)
        send_to = op_flow._parse_endpoints(op_flow, pod_name, send_to, connect_to_last_pod=False)

        kwargs.update(op_flow._common_kwargs)
        kwargs['name'] = pod_name
        kwargs['num_part'] = len(recv_from)
        op_flow._pod_nodes[pod_name] = FlowPod(kwargs=kwargs, send_to=send_to, recv_from=recv_from)

        op_flow.set_last_pod(pod_name, False)

        return op_flow

    def build(self, copy_flow: bool = True) -> 'Flow':
        """
        Build the current flow and make it ready to use

        :param copy_flow: return the copy of the current flow.
        :return: the current flow (by default)

        .. note::
            ``copy_flow=True`` is recommended if you are building the same flow multiple times in a row. e.g.

            .. highlight:: python
            .. code-block:: python

                f = Flow()
                with f.build(copy_flow=True) as fl:
                    fl.index()

                with f.build(copy_flow=False) as fl:
                    fl.search()

        """

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
                FlowPod.connect(s_pod, e_pod, first_socket_type=SocketType.PUB_BIND)
            elif len(edges_with_same_start) == 1 and len(edges_with_same_end) > 1:
                FlowPod.connect(s_pod, e_pod, first_socket_type=SocketType.PUSH_CONNECT)
            elif len(edges_with_same_start) == 1 and len(edges_with_same_end) == 1:
                # in this case, either side can be BIND
                # we prefer frontend to be always CONNECT so that multiple clients can connect to it
                # check if either node is frontend
                if s_name == 'frontend':
                    if self.optimized and e_pod.is_head_router:
                        # connect frontend directly to peas
                        e_pod.connect_to_tail_of(s_pod)
                    else:
                        FlowPod.connect(s_pod, e_pod, first_socket_type=SocketType.PUSH_CONNECT)
                elif e_name == 'frontend':
                    if self.optimized and s_pod.is_tail_router and s_pod.tail_args.num_part == 1:
                        # connect frontend directly to peas only if this is unblock router
                        # as frontend can not block & reduce message
                        s_pod.connect_to_head_of(e_pod)
                    else:
                        FlowPod.connect(s_pod, e_pod, first_socket_type=SocketType.PUSH_BIND)
                else:
                    e_pod.head_args.socket_in = s_pod.tail_args.socket_out.paired
                    if self.optimized and e_pod.is_head_router and not s_pod.is_tail_router:
                        e_pod.connect_to_tail_of(s_pod)
                    elif self.optimized and s_pod.is_tail_router and s_pod.tail_args.num_part == 1:
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
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @build_required(FlowBuildLevel.GRAPH)
    def start(self):
        """Start to run all Pods in this Flow.

        Remember to close the Flow with :meth:`close`.

        Note that this method has a timeout of ``ready_timeout`` set in CLI,
        which is inherited all the way from :class:`jina.peapods.peas.Pea`
        """
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

    def close(self):
        """Close the flow and release all resources associated to it. """
        if hasattr(self, '_pod_stack'):
            self._pod_stack.close()
        self._build_level = FlowBuildLevel.EMPTY
        time.sleep(1)  # sleep for a while until all resources are safely closed
        self.logger.critical(
            'flow is closed and all resources should be released already, current build level is %s' % self._build_level)

    def __eq__(self, other: 'Flow'):
        """
        Comparing the topology of a flow with another flow.
        Identification is defined by whether two flows share the same set of edges.

        :param other: the second flow object
        """

        if self._build_level.value < FlowBuildLevel.GRAPH.value:
            a = self.build(copy_flow=True)
        else:
            a = self

        if other._build_level.value < FlowBuildLevel.GRAPH.value:
            b = other.build(copy_flow=True)
        else:
            b = other

        return a._pod_nodes == b._pod_nodes

    @build_required(FlowBuildLevel.GRAPH)
    def _get_client(self, bytes_gen: Iterator[bytes] = None, **kwargs):
        from ..main.parser import set_client_cli_parser
        from ..clients.python import PyClient

        _, p_args, _ = self._get_parsed_args(self, PyClient.__name__, kwargs, parser=set_client_cli_parser)
        p_args.grpc_port = self._pod_nodes['frontend'].grpc_port
        p_args.grpc_host = self._pod_nodes['frontend'].grpc_host
        c = PyClient(p_args)
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

    def dry_run(self, **kwargs):
        """Send a DRYRUN request to this flow, passing through all pods in this flow
        useful for testing connectivity and debugging"""
        if not self._get_client(mode='search', **kwargs).dry_run():
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
                'image': self.image_name,
                'command': v.to_cli_command(),
                'deploy': {'replicas': 1}
            }

        yaml.dump(swarm_yml, path)
