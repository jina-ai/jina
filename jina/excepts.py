"""This modules defines all kinds of exceptions raised in Jina."""


class BaseJinaExeception:
    """A base class for all exceptions raised by Jina"""


class NoExplicitMessage(Exception, BaseJinaExeception):
    """Waiting until all partial messages are received."""


class ChainedPodException(Exception, BaseJinaExeception):
    """Chained exception from the last Pod."""


class MismatchedVersion(SystemError, BaseJinaExeception):
    """When the jina version info of the incoming message does not match the local Jina version."""


class ExecutorFailToLoad(SystemError, BaseJinaExeception):
    """When the executor can not be loaded in pea/pod."""


class RuntimeFailToStart(SystemError, BaseJinaExeception):
    """When pea/pod is failed to started."""


class ScalingFails(SystemError, BaseJinaExeception):
    """When scaling is unsuccessful for an Executor."""


class MemoryOverHighWatermark(Exception, BaseJinaExeception):
    """When the memory usage is over the defined high water mark."""


class NoAvailablePortError(Exception, BaseJinaExeception):
    """When no available random port could be found"""


class RuntimeTerminated(KeyboardInterrupt, BaseJinaExeception):
    """The event loop of BasePea ends."""


class UnknownControlCommand(RuntimeError, BaseJinaExeception):
    """The control command received can not be recognized."""


class FlowTopologyError(Exception, BaseJinaExeception):
    """Flow exception when the topology is ambiguous."""


class FlowMissingPodError(Exception, BaseJinaExeception):
    """Flow exception when a pod can not be found in the flow."""


class FlowBuildLevelError(Exception, BaseJinaExeception):
    """Flow exception when required build level is higher than the current build level."""


class BadConfigSource(FileNotFoundError, BaseJinaExeception):
    """The yaml config file is bad, not loadable or not exist."""


class BadClient(Exception, BaseJinaExeception):
    """A wrongly defined client, can not communicate with jina server correctly."""


class BadClientCallback(BadClient, BaseJinaExeception):
    """Error in the callback function on the client side."""


class BadClientInput(BadClient, BaseJinaExeception):
    """Error in the request generator function on the client side."""


class BadRequestType(TypeError, BaseJinaExeception):
    """Exception when can not construct a request object from given data."""


class BadNamedScoreType(TypeError, BaseJinaExeception):
    """Exception when can not construct a named score from the given data."""


class BadImageNameError(Exception, BaseJinaExeception):
    """Exception when an image name can not be found either local & remote"""


class BadYAMLVersion(Exception, BaseJinaExeception):
    """Exception when YAML config specifies a wrong version number."""


class DaemonConnectivityError(Exception, BaseJinaExeception):
    """Exception to raise when jina daemon is not reachable."""


class DaemonWorkspaceCreationFailed(Exception, BaseJinaExeception):
    """Exception to raise when jina daemon is not connectable."""


class DaemonPeaCreationFailed(Exception, BaseJinaExeception):
    """Exception to raise when jina daemon is not connectable."""


class NotSupportedError(Exception, BaseJinaExeception):
    """Exception when user accidentally using a retired argument."""


class RoutingTableCyclicError(Exception, BaseJinaExeception):
    """Raised when the routing graph has cycles."""


class RuntimeRunForeverEarlyError(Exception, BaseJinaExeception):
    """Raised when an error occurs when starting the run_forever of Runtime"""


class DockerVersionError(SystemError, BaseJinaExeception):
    """Raised when the docker version is incompatible"""


class DaemonInvalidDockerfile(FileNotFoundError, BaseJinaExeception):
    """Raised when invalid dockerfile is passed to JinaD"""
