__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

"""
Miscellaneous enums used in jina


To use these enums in YAML config, following the example below:

.. highlight:: yaml
.. code-block:: yaml

    !Flow
    with:
      logserver_config: yaml/test-server-config.yml
      optimize_level: !FlowOptimizeLevel IGNORE_GATEWAY
      # or
      optimize_level: IGNORE_GATEWAY
      #or
      optimize_level: ignore_gateway
      no_gateway: true


.. highlight:: yaml
.. code-block:: yaml

      chunk_idx:
        yaml_path: index/chunk.yml
        replicas: $REPLICAS
        separated_workspace: true
        replicas_type: !PollingType ANY
        # or
        replicas_type: ANY
        # or
        replicas_type: any
"""

from enum import IntEnum, EnumMeta


class EnumType(EnumMeta):

    def __new__(cls, *args, **kwargs):
        _cls = super().__new__(cls, *args, **kwargs)
        return cls.register_class(_cls)

    @staticmethod
    def register_class(cls):
        reg_cls_set = getattr(cls, '_registered_class', set())
        if cls.__name__ not in reg_cls_set:
            # print('reg class: %s' % cls.__name__)

            reg_cls_set.add(cls.__name__)
            setattr(cls, '_registered_class', reg_cls_set)
        from .helper import yaml
        yaml.register_class(cls)
        return cls


class BetterEnum(IntEnum, metaclass=EnumType):
    def __str__(self):
        return self.name

    @classmethod
    def from_string(cls, s: str):
        """Parse the enum from a string"""
        try:
            return cls[s.upper()]
        except KeyError:
            raise ValueError('%s is not a valid enum for %s' % (s.upper(), cls))

    @classmethod
    def to_yaml(cls, representer, data):
        """Required by :mod:`ruamel.yaml.constructor` """
        return representer.represent_scalar('!' + cls.__name__, str(data))

    @classmethod
    def from_yaml(cls, constructor, node):
        """Required by :mod:`ruamel.yaml.constructor` """
        return cls.from_string(node.value)


class SchedulerType(BetterEnum):
    LOAD_BALANCE = 0  #: balance the workload between Peas, faster peas get more work
    ROUND_ROBIN = 1  #: workload are scheduled round-robin manner to the peas, assuming all peas have uniform processing speed.


class PollingType(BetterEnum):
    """The enum for representing the parallel type of peas in a pod

    """
    ANY = 1  #: one of the replica will receive the message
    ALL = 2  #: all replica will receive the message, blocked until all done with the message
    ALL_ASYNC = 3  #: (reserved) all replica will receive the message, but any one of them can return, useful in backup

    @property
    def is_push(self) -> bool:
        """

        :return: if this :class:`PollingType` is using `push` protocol
        """
        return self.value == 1

    @property
    def is_block(self) -> bool:
        """

        :return: if this :class:`PollingType` is requiring `block` protocol
        """
        return self.value == 2


class FlowOptimizeLevel(BetterEnum):
    """The level of flow optimization """
    NONE = 0
    IGNORE_GATEWAY = 1
    FULL = 2


class LogVerbosity(BetterEnum):
    """Verbosity level of the logger """
    DEBUG = 10
    INFO = 20
    SUCCESS = 25
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
    ROUTER_BIND = 10
    DEALER_CONNECT = 11

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


class PeaRoleType(BetterEnum):
    """ The enum of a Pea role

    """
    REPLICA = 0
    HEAD = 1
    TAIL = 2
    SHARD = 3


class ClientMode(BetterEnum):
    """ The enum of Client mode

    """
    INDEX = 0
    SEARCH = 1
    TRAIN = 2

