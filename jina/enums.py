"""
Miscellaneous enums used in jina
"""

from enum import IntEnum


class BetterEnum(IntEnum):
    def __str__(self):
        return self.name

    @classmethod
    def from_string(cls, s: str):
        """Parse the enum from a string"""
        try:
            return cls[s.upper()]
        except KeyError:
            raise ValueError('%s is not a valid enum for %s' % (s.upper(), cls))


class ReplicaType(BetterEnum):
    """The enum for representing the parallel type of peas in a pod

    .. note::
        ``PUSH_BLOCK`` does not exist as push message has different request ids, they can not be blocked
    """
    PUSH_NONBLOCK = 1  #: push without blocking
    PUB_BLOCK = 2  #: publish message with blocking (in this case, blocking means collecting all published messages until next)
    PUB_NONBLOCK = 3  #: publish message but no blocking

    @property
    def is_push(self) -> bool:
        """

        :return: if this :class:`ReplicaType` is using `push` protocol
        """
        return self.value == 1

    @property
    def is_block(self) -> bool:
        """

        :return: if this :class:`ReplicaType` is requiring `block` protocol
        """
        return self.value == 2


class LogVerbosity(BetterEnum):
    """Verbosity level of the logger """
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


class SocketType(BetterEnum):
    """Enums for representing the socket type in a pod """
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

    @property
    def is_bind(self) -> bool:
        """

        :return: if this socket is using `bind` protocol
        """
        return self.value % 2 == 0

    @property
    def is_receive(self) -> bool:
        """

        :return: if this socket is used for receiving data
        """
        return self.value in {0, 1, 4, 5}

    @property
    def is_pubsub(self):
        """

        :return: if this socket is used for publish or subscribe data
        """
        return 4 <= self.value <= 7

    @property
    def paired(self) -> 'SocketType':
        """

        :return: a paired
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
            SocketType.PAIR_CONNECT: SocketType.PAIR_BIND
        }[self]


class FlowOutputType(BetterEnum):
    """The enum for representing flow output config """
    SHELL_PROC = 0  #: a shell-script, run each microservice as a process
    SHELL_DOCKER = 1  #: a shell-script, run each microservice as a container
    DOCKER_SWARM = 2  #: a docker-swarm YAML config
    K8S = 3  #: a Kubernetes YAML config


class FlowBuildLevel(BetterEnum):
    """The enum for representing a flow's build level

    Some :class:`jina.flow.Flow` class functions require certain build level to run.
    """
    EMPTY = 0  #: Nothing is built
    GRAPH = 1  #: The underlying graph is built, you may visualize the flow
    RUNTIME = 2  #: The flow is able to execute
