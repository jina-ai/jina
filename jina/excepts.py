""" This modules defines all kinds of exceptions raised in jina """

__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"



class NoExplicitMessage(Exception):
    """Waiting until all partial messages are received"""


class MismatchedVersion(SystemError):
    """When the jina version info of the incoming message does not match the local jina version"""


class ExecutorFailToLoad(SystemError):
    """When the executor can not be loaded in pea/pod"""


class PeaFailToStart(SystemError):
    """When pea/pod is failed to started"""


class MemoryOverHighWatermark(Exception):
    """When the memory usage is over the defined high water mark"""


class DriverError(Exception):
    """Driver related exceptions"""


class RequestLoopEnd(KeyboardInterrupt):
    """The event loop of BasePea ends"""


class PodRunTimeError(Exception):
    """The error propagated by Pods when Executor throws an exception"""


class DriverNotInstalled(DriverError):
    """Driver is not installed in the BasePea"""


class NoDriverForRequest(DriverError):
    """No matched driver for this request """


class UnattachedDriver(DriverError):
    """Driver is not attached to any BasePea or executor"""


class UnknownControlCommand(RuntimeError):
    """The control command received can not be recognized"""


class FlowTopologyError(Exception):
    """Flow exception when the topology is ambiguous."""


class FlowConnectivityError(Exception):
    """Flow exception when the flow is not connective via network."""


class FlowMissingPodError(Exception):
    """Flow exception when a pod can not be found in the flow."""


class FlowBuildLevelError(Exception):
    """Flow exception when required build level is higher than the current build level."""


class EmptyExecutorYAML(Exception):
    """The yaml config file is empty, nothing to read from there."""


class BadWorkspace(Exception):
    """Can not determine the separate storage strategy for the executor"""


class BadClient(Exception):
    """A wrongly defined grpc client, can not communicate with jina server correctly """


class BadPersistantFile(Exception):
    """Bad or broken dump file that can not be deserialized with ``pickle.load``"""


class BadRequestType(Exception):
    """Bad request type and the pod does not know how to handle """


class GRPCServerError(Exception):
    """Can not connect to the grpc gateway"""


class GatewayPartialMessage(Exception):
    """Gateway receives a multi-part message but it can not handle it"""


class UndefinedModel(Exception):
    """Any time a non-defined model is tried to be used """


class MongoDBException(Exception):
    """ Any errors raised by MongoDb """


class TimedOutException(Exception):
    """ Errors raised for timeout operations """


class DockerLoginFailed(Exception):
    """ Exception to raise for docker hub login failures """
