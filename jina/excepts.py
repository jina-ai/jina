"""This modules defines all kinds of exceptions raised in Jina."""


class NoExplicitMessage(Exception):
    """Waiting until all partial messages are received."""


class ChainedPodException(Exception):
    """Chained exception from the last Pod."""


class MismatchedVersion(SystemError):
    """When the jina version info of the incoming message does not match the local Jina version."""


class ExecutorFailToLoad(SystemError):
    """When the executor can not be loaded in pea/pod."""


class RuntimeFailToStart(SystemError):
    """When pea/pod is failed to started."""


class MemoryOverHighWatermark(Exception):
    """When the memory usage is over the defined high water mark."""


class NoAvailablePortError(Exception):
    """When no available random port could be found"""


class RuntimeTerminated(KeyboardInterrupt):
    """The event loop of BasePea ends."""


class UnknownControlCommand(RuntimeError):
    """The control command received can not be recognized."""


class FlowTopologyError(Exception):
    """Flow exception when the topology is ambiguous."""


class FlowMissingPodError(Exception):
    """Flow exception when a pod can not be found in the flow."""


class FlowBuildLevelError(Exception):
    """Flow exception when required build level is higher than the current build level."""


class BadConfigSource(FileNotFoundError):
    """The yaml config file is bad, not loadable or not exist."""


class BadClient(Exception):
    """A wrongly defined client, can not communicate with jina server correctly."""


class BadClientCallback(BadClient):
    """Error in the callback function on the client side."""


class BadClientInput(BadClient):
    """Error in the request generator function on the client side."""


class ModelCheckpointNotExist(FileNotFoundError):
    """Exception to raise for executors depending on pretrained model files when they do not exist."""


class PretrainedModelFileDoesNotExist(ModelCheckpointNotExist):
    """Depreciated, used in the hub executors.

    TODO: to be removed after hub executors uses ModelCheckpointNotExist
    """


class HubDownloadError(Exception):
    """Exception to raise when :command:`jina hub pull` fails to download package."""


class BadDocType(TypeError):
    """Exception when can not construct a document from the given data."""


class BadRequestType(TypeError):
    """Exception when can not construct a request object from given data."""


class BadNamedScoreType(TypeError):
    """Exception when can not construct a named score from the given data."""


class BadImageNameError(Exception):
    """Exception when an image name can not be found either local & remote"""


class BadYAMLVersion(Exception):
    """Exception when YAML config specifies a wrong version number."""


class DaemonConnectivityError(Exception):
    """Exception to raise when jina daemon is not reachable."""


class DaemonWorkspaceCreationFailed(Exception):
    """Exception to raise when jina daemon is not connectable."""


class DaemonPeaCreationFailed(Exception):
    """Exception to raise when jina daemon is not connectable."""


class NotSupportedError(Exception):
    """Exeception when user accidentally using a retired argument."""


class ValidationError(Exception):
    """Raised when a certain validation cannot be completed."""


class SocketTypeError(Exception):
    """Raised when such socket type is not supported or does not exist."""


class RoutingTableCyclicError(Exception):
    """Raised when the routing graph has cycles."""


class RuntimeRunForeverEarlyError(Exception):
    """Raised when an error occurs when starting the run_forever of Runtime"""


class DockerVersionError(SystemError):
    """Raised when the docker version is incompatible"""
