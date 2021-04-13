"""
Miscellaneous enums used in Jina.

To use these enums in YAML config, following the example below:

.. highlight:: yaml
.. code-block:: yaml

      chunk_idx:
        uses: index/chunk.yml
        parallel: ${{PARALLEL}}
        parallel_type: !PollingType ANY
        # or
        parallel_type: ANY
        # or
        parallel_type: any
"""

__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from enum import IntEnum, EnumMeta


class EnumType(EnumMeta):
    """The metaclass for BetterEnum."""

    def __new__(cls, *args, **kwargs):
        """Register a new EnumType

        :param args: args passed to super()
        :param kwargs: kwargs passed to super()
        :return: the registry class
        """
        _cls = super().__new__(cls, *args, **kwargs)
        return cls.register_class(_cls)

    @staticmethod
    def register_class(cls):
        """
        Register the class for dumping loading.

        :param cls: Target class.
        :return: Registered class.
        """
        reg_cls_set = getattr(cls, '_registered_class', set())
        if cls.__name__ not in reg_cls_set or getattr(cls, 'force_register', False):
            reg_cls_set.add(cls.__name__)
            setattr(cls, '_registered_class', reg_cls_set)
        from .jaml import JAML

        JAML.register(cls)
        return cls


class BetterEnum(IntEnum, metaclass=EnumType):
    """The base class of Enum used in Jina."""

    def __str__(self):
        return self.name

    @classmethod
    def from_string(cls, s: str):
        """
        Parse the enum from a string.

        :param s: string representation of the enum value
        :return: enum value
        """
        try:
            return cls[s.upper()]
        except KeyError:
            raise ValueError(
                f'{s.upper()} is not a valid enum for {cls!r}, must be one of {list(cls)}'
            )

    @classmethod
    def _to_yaml(cls, representer, data):
        """Required by :mod:`pyyaml`.

        .. note::
            In principle, this should inherit from :class:`JAMLCompatible` directly,
            however, this method is too simple and thus replaced the parent method.
        :param representer: pyyaml representer
        :param data: enum value
        :return: yaml representation
        """
        return representer.represent_scalar(
            'tag:yaml.org,2002:str', str(data), style='"'
        )

    @classmethod
    def _from_yaml(cls, constructor, node):
        """Required by :mod:`pyyaml`.

        .. note::
            In principle, this should inherit from :class:`JAMLCompatible` directly,
            however, this method is too simple and thus replaced the parent method.
        :param constructor: unused
        :param node: node to derive the enum value from
        :return: enum value
        """
        return cls.from_string(node.value)


class SchedulerType(BetterEnum):
    """The enum for Scheduler Type."""

    LOAD_BALANCE = 0  #: balance the workload between Peas, faster peas get more work
    ROUND_ROBIN = 1  # : workload are scheduled round-robin manner to the peas, assuming all peas have uniform processing speed.


class PollingType(BetterEnum):
    """The enum for representing the parallel type of peas in a pod."""

    ANY = 1  #: one of the shards will receive the message
    ALL = 2  #: all shards will receive the message, blocked until all done with the message
    ALL_ASYNC = 3  #: (reserved) all replica will receive the message, but any one of them can return, useful in backup

    @property
    def is_push(self) -> bool:
        """
        Check if :class:`PollingType` is using `push` protocol.

        :return: True if this :class:`PollingType` is using `push` protocol else False.
        """
        return self.value == 1

    @property
    def is_block(self) -> bool:
        """
        Check if :class:`PollingType` is using `block` protocol.

        :return: True if this :class:`PollingType` is requiring `block` protocol else False.
        """
        return self.value == 2


class LogVerbosity(BetterEnum):
    """Verbosity level of the logger."""

    DEBUG = 10
    INFO = 20
    SUCCESS = 25
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


class SocketType(BetterEnum):
    """Enums for representing the socket type in a pod."""

    PULL_BIND = 0
    PULL_CONNECT = 1
    PUSH_BIND = 2
    PUSH_CONNECT = 3
    SUB_BIND = 4
    SUB_CONNECT = 5
    PUB_BIND = 6
    PUB_CONNECT = 7
    PAIR_BIND = 8
    PAIR_CONNECT = 9
    ROUTER_BIND = 10
    DEALER_CONNECT = 11

    @property
    def is_bind(self) -> bool:
        """
        Check if this socket is using `bind` protocol.

        :return: True if this socket is using `bind` protocol else False.
        """
        return self.value % 2 == 0

    @property
    def is_receive(self) -> bool:
        """
        Check if this socket is used for receiving data.

        :return: True if this socket is used for receiving data else False.
        """
        return self.value in {0, 1, 4, 5}

    @property
    def is_pubsub(self):
        """
        Check if this socket is used for publish or subscribe data.

        :return: True if this socket is used for publish or subscribe data else False.
        """
        return 4 <= self.value <= 7

    @property
    def paired(self) -> 'SocketType':
        """
        Get the paired SocketType.

        :return: a paired SocketType.
        """
        return {
            SocketType.PULL_BIND: SocketType.PUSH_CONNECT,
            SocketType.PULL_CONNECT: SocketType.PUSH_BIND,
            SocketType.SUB_BIND: SocketType.PUB_CONNECT,
            SocketType.SUB_CONNECT: SocketType.PUB_BIND,
            SocketType.PAIR_BIND: SocketType.PAIR_CONNECT,
            SocketType.PUSH_CONNECT: SocketType.PULL_BIND,
            SocketType.PUSH_BIND: SocketType.PULL_CONNECT,
            SocketType.PUB_CONNECT: SocketType.SUB_BIND,
            SocketType.PUB_BIND: SocketType.SUB_CONNECT,
            SocketType.PAIR_CONNECT: SocketType.PAIR_BIND,
        }[self]


class FlowOutputType(BetterEnum):
    """The enum for representing flow output config."""

    SHELL_PROC = 0  #: a shell-script, run each microservice as a process
    SHELL_DOCKER = 1  #: a shell-script, run each microservice as a container
    DOCKER_SWARM = 2  #: a docker-swarm YAML config
    K8S = 3  #: a Kubernetes YAML config


class FlowBuildLevel(BetterEnum):
    """
    The enum for representing a flow's build level.

    Some :class:`jina.flow.Flow` class functions require certain build level to run.
    """

    EMPTY = 0  #: Nothing is built
    GRAPH = 1  #: The underlying graph is built, you may visualize the flow


class PeaRoleType(BetterEnum):
    """The enum of a Pea role."""

    SINGLETON = 0
    HEAD = 1
    TAIL = 2
    PARALLEL = 3


class PodRoleType(BetterEnum):
    """The enum of a Pod role for visualization."""

    POD = 0
    JOIN = 1
    INSPECT = 2
    GATEWAY = 3
    INSPECT_AUX_PASS = 4
    JOIN_INSPECT = 5

    @property
    def is_inspect(self) -> bool:
        """
        If the role is inspect pod related.

        :return: True if the Pod role is inspect related else False.
        """
        return self.value in {2, 4}


class RequestType(BetterEnum):
    """The enum of Client mode."""

    INDEX = 0
    SEARCH = 1
    DELETE = 2
    UPDATE = 3
    CONTROL = 4
    TRAIN = 5
    # TODO make Dump a control request to be passed to the Pod directly
    DUMP = 6


class CompressAlgo(BetterEnum):
    """
    The enum of Compress algorithms.

    .. note::
        LZ4 requires additional package, to install it use pip install "jina[lz4]"

    .. seealso::

        https://docs.python.org/3/library/archiving.html
    """

    NONE = 0
    LZ4 = 1
    ZLIB = 2
    GZIP = 3
    BZ2 = 4
    LZMA = 5


class OnErrorStrategy(BetterEnum):
    """
    The level of error handling.

    .. warning::
        In theory, all methods below do not 100% guarantee the success
        execution on the sequel flow. If something is wrong in the upstream,
        it is hard to CARRY this exception and moving forward without ANY
        side-effect.
    """

    IGNORE = (
        0  #: Ignore it, keep running all Drivers & Executors logics in the sequel flow
    )
    SKIP_EXECUTOR = 1  #: Skip all Executors in the sequel, but drivers are still called
    SKIP_HANDLE = 2  #: Skip all Drivers & Executors in the sequel, only `pre_hook` and `post_hook` are called
    THROW_EARLY = 3  #: Immediately throw the exception, the sequel flow will not be running at all


class FlowInspectType(BetterEnum):
    """Inspect strategy in the flow."""

    HANG = 0  # keep them hanging there
    REMOVE = 1  # remove them in the build
    COLLECT = 2  # spawn a new pod and collect them before build

    @property
    def is_keep(self) -> bool:
        """
        Check if the target is inspected.

        :return: True if the target is inspected else False.
        """
        return self.value in {0, 2}


class RemoteAccessType(BetterEnum):
    """Remote access type when connect to the host."""

    SSH = 0  # ssh connection
    JINAD = 1  # using rest api via jinad


class BuildTestLevel(BetterEnum):
    """Test level in :command:`jina hub build`, higher level includes lower levels."""

    NONE = 0  # no build test
    EXECUTOR = 1  # test at executor level, directly use the config yaml
    POD_NONDOCKER = 2  # test at pod level, directly use the config yaml
    POD_DOCKER = 3  # test at pod level but pod --uses the built image
    FLOW = 4  # test at a simple flow


class DataInputType(BetterEnum):
    """Data input type in the request generator."""

    AUTO = 0  # auto inference the input type from data (!WARN: could be slow as it relies on try-execept)
    DOCUMENT = 1  # the input is a full document
    CONTENT = 2  # the input is just the content of the document


class RuntimeBackendType(BetterEnum):
    """Type of backend in runtime."""

    THREAD = 0
    PROCESS = 1


def replace_enum_to_str(obj):
    """
    Transform BetterEnum type into string.

    :param obj: Target obj.
    :return: Transformed obj with string type values.
    """
    for k, v in obj.items():
        if isinstance(v, dict):
            obj[k] = replace_enum_to_str(v)
        elif isinstance(v, BetterEnum):
            obj[k] = str(v)
    return obj
