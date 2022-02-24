"""This modules defines all kinds of exceptions raised in Jina."""


class BaseJinaExeception:
    """A base class for all exceptions raised by Jina"""


class ExecutorFailToLoad(SystemError, BaseJinaExeception):
    """When the executor can not be loaded in pod/deployment."""


class RuntimeFailToStart(SystemError, BaseJinaExeception):
    """When pod/deployment is failed to started."""


class ScalingFails(SystemError, BaseJinaExeception):
    """When scaling is unsuccessful for an Executor."""


class RuntimeTerminated(KeyboardInterrupt, BaseJinaExeception):
    """The event loop of BasePod ends."""


class FlowTopologyError(Exception, BaseJinaExeception):
    """Flow exception when the topology is ambiguous."""


class FlowMissingDeploymentError(Exception, BaseJinaExeception):
    """Flow exception when a deployment can not be found in the flow."""


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


class BadImageNameError(Exception, BaseJinaExeception):
    """Exception when an image name can not be found either local & remote"""


class BadYAMLVersion(Exception, BaseJinaExeception):
    """Exception when YAML config specifies a wrong version number."""


class DaemonConnectivityError(Exception, BaseJinaExeception):
    """Exception to raise when jina daemon is not reachable."""


class DaemonWorkspaceCreationFailed(Exception, BaseJinaExeception):
    """Exception to raise when jina daemon is not connectable."""


class DaemonPodCreationFailed(Exception, BaseJinaExeception):
    """Exception to raise when jina daemon is not connectable."""


class NotSupportedError(Exception, BaseJinaExeception):
    """Exception when user accidentally using a retired argument."""


class RuntimeRunForeverEarlyError(Exception, BaseJinaExeception):
    """Raised when an error occurs when starting the run_forever of Runtime"""


class DockerVersionError(SystemError, BaseJinaExeception):
    """Raised when the docker version is incompatible"""


class DaemonInvalidDockerfile(FileNotFoundError, BaseJinaExeception):
    """Raised when invalid dockerfile is passed to JinaD"""


class NoContainerizedError(Exception, BaseJinaExeception):
    """Raised when trying to use non-containerized Executor in K8s or Docker Compose"""
